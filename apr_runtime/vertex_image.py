from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import os
import re
import struct
import time
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from .image_generation import ImageGenerationResult
from .plugins import PluginRegistry

DEFAULT_VERTEX_IMAGE_MODEL = "gemini-3.1-flash-lite-image"
DEFAULT_VERTEX_LOCATION = "global"
GOOGLE_CLOUD_SCOPE = "https://www.googleapis.com/auth/cloud-platform"

# USD per million tokens for the synchronous standard tier. Google applies a
# 10% multiplier to non-global Gemini 3 endpoints. Unknown model overrides
# still report usage but deliberately do not claim a price.
_VERTEX_IMAGE_PRICING = {
    "gemini-3.1-flash-lite-image": (0.25, 1.50, 30.00),
    "gemini-3.1-flash-image": (0.50, 3.00, 60.00),
    "gemini-3-pro-image": (2.00, 12.00, 120.00),
}
_ALLOWED_ASPECT_RATIOS = {
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9",
}
_ALLOWED_IMAGE_SIZES = {"512", "1K", "2K", "4K"}
_MODEL_IMAGE_SIZES = {
    "gemini-3.1-flash-lite-image": {"1K"},
    "gemini-3.1-flash-image": {"512", "1K", "2K", "4K"},
    "gemini-3-pro-image": {"1K", "2K", "4K"},
}
_PRICING_SNAPSHOT_DATE = "2026-08-10"
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}")
_JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b")

JsonTransport = Callable[[str, Mapping[str, str], Mapping[str, Any], float], Mapping[str, Any]]
TokenProvider = Callable[[], str]


class VertexImageGenerationError(RuntimeError):
    """Safe Vertex image-generation failure that never includes credentials."""


def _safe_error_message(value: str, *, limit: int = 600) -> str:
    value = _BEARER_PATTERN.sub("Bearer <redacted>", value)
    value = _JWT_PATTERN.sub("<access-token-redacted>", value)
    return " ".join(value.split())[:limit]


def _http_json_transport(
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    timeout: float,
) -> Mapping[str, Any]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib_request.Request(url, data=body, headers=dict(headers), method="POST")
    try:
        with urllib_request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            decoded = json.loads(raw)
            message = decoded.get("error", {}).get("message", raw)
        except (AttributeError, json.JSONDecodeError):
            message = raw
        raise VertexImageGenerationError(
            f"Vertex image API returned HTTP {exc.code}: {_safe_error_message(str(message))}"
        ) from exc
    except urllib_error.URLError as exc:
        raise VertexImageGenerationError(
            f"Vertex image API connection failed: {_safe_error_message(str(exc.reason))}"
        ) from exc

    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VertexImageGenerationError("Vertex image API returned invalid JSON.") from exc
    if not isinstance(decoded, dict):
        raise VertexImageGenerationError("Vertex image API returned a non-object response.")
    return decoded


def _non_empty(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _positive_number(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive value")
    return value


def _positive_int(name: str, value: int, *, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value > maximum:
        raise ValueError(f"{name} must be an integer in [1, {maximum}]")
    return value


def _png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise VertexImageGenerationError("Vertex returned data that is not a valid PNG image.")
    width, height = struct.unpack(">II", data[16:24])
    if width <= 0 or height <= 0:
        raise VertexImageGenerationError("Vertex returned a PNG with invalid dimensions.")
    return width, height


def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise VertexImageGenerationError("Vertex returned data that is not a valid JPEG image.")
    offset = 2
    start_of_frame = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while offset + 3 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in {0xD8, 0xD9}:
            continue
        if marker == 0xDA or offset + 2 > len(data):
            break
        segment_length = struct.unpack(">H", data[offset : offset + 2])[0]
        if segment_length < 2 or offset + segment_length > len(data):
            break
        if marker in start_of_frame and segment_length >= 7:
            height, width = struct.unpack(">HH", data[offset + 3 : offset + 7])
            if width > 0 and height > 0:
                return width, height
            break
        offset += segment_length
    raise VertexImageGenerationError("Vertex returned a JPEG with no valid dimensions.")


def _image_details(data: bytes, reported_mime: str) -> tuple[str, str, int, int]:
    if reported_mime == "image/png":
        width, height = _png_dimensions(data)
        return "image/png", ".png", width, height
    if reported_mime in {"image/jpeg", "image/jpg"}:
        width, height = _jpeg_dimensions(data)
        return "image/jpeg", ".jpg", width, height
    raise VertexImageGenerationError(
        f"Vertex returned unsupported image MIME type: {_safe_error_message(reported_mime)}"
    )


def _usage_metadata(
    payload: Mapping[str, Any],
    *,
    model: str,
    location: str,
) -> Dict[str, Any]:
    usage = payload.get("usageMetadata", {})
    usage = usage if isinstance(usage, dict) else {}
    prompt_tokens = int(usage.get("promptTokenCount", 0) or 0)
    output_tokens = int(usage.get("candidatesTokenCount", 0) or 0)

    image_output_tokens = 0
    text_output_tokens = 0
    details = usage.get("candidatesTokensDetails", [])
    if isinstance(details, list):
        for item in details:
            if not isinstance(item, dict):
                continue
            count = int(item.get("tokenCount", 0) or 0)
            modality = str(item.get("modality", "")).upper()
            if modality == "IMAGE":
                image_output_tokens += count
            elif modality == "TEXT":
                text_output_tokens += count

    # This adapter requests IMAGE as the only response modality. Older response
    # shapes may omit modality detail while still reporting candidate tokens.
    if not image_output_tokens and output_tokens and not text_output_tokens:
        image_output_tokens = output_tokens

    result: Dict[str, Any] = {
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "image_output_tokens": image_output_tokens,
        "text_output_tokens": text_output_tokens,
        "total_tokens": int(usage.get("totalTokenCount", 0) or 0),
        "pricing_snapshot_date": _PRICING_SNAPSHOT_DATE,
    }
    pricing = _VERTEX_IMAGE_PRICING.get(model)
    if pricing is None:
        result["estimated_cost_usd"] = None
        result["pricing_scope"] = None
        return result

    input_rate, text_output_rate, image_output_rate = pricing
    multiplier = 1.0 if location == "global" else 1.1
    estimated = (
        multiplier
        * (
            prompt_tokens * input_rate
            + text_output_tokens * text_output_rate
            + image_output_tokens * image_output_rate
        )
        / 1_000_000
    )
    result["estimated_cost_usd"] = round(estimated, 8)
    result["pricing_scope"] = "global" if multiplier == 1.0 else "non_global"
    return result


class GoogleVertexImageGenerator:
    """Single-image Gemini generator backed by the Vertex generateContent API."""

    def __init__(
        self,
        *,
        project_id: Optional[str] = None,
        location: str = DEFAULT_VERTEX_LOCATION,
        model: str = DEFAULT_VERTEX_IMAGE_MODEL,
        credentials_path: Optional[str | Path] = None,
        access_token: Optional[str] = None,
        token_provider: Optional[TokenProvider] = None,
        aspect_ratio: str = "1:1",
        image_size: str = "1K",
        timeout: float = 120.0,
        max_prompt_chars: int = 10_000,
        max_image_bytes: int = 20_000_000,
        transport: Optional[JsonTransport] = None,
    ) -> None:
        if project_id is not None:
            project_id = _non_empty("project_id", project_id)
        self._explicit_project_id = project_id
        self.location = _non_empty("location", location)
        self.model = _non_empty("model", model)
        if aspect_ratio not in _ALLOWED_ASPECT_RATIOS:
            raise ValueError("unsupported aspect_ratio")
        if image_size not in _ALLOWED_IMAGE_SIZES:
            raise ValueError("unsupported image_size")
        supported_sizes = _MODEL_IMAGE_SIZES.get(self.model)
        if supported_sizes is not None and image_size not in supported_sizes:
            supported = ", ".join(sorted(supported_sizes))
            raise ValueError(f"{self.model} supports image_size values: {supported}")
        if access_token is not None:
            access_token = _non_empty("access_token", access_token)
        if token_provider is not None and not callable(token_provider):
            raise TypeError("token_provider must be callable")
        self.credentials_path = (
            Path(credentials_path).expanduser().resolve() if credentials_path is not None else None
        )
        self._explicit_access_token = access_token
        self.token_provider = token_provider
        self.aspect_ratio = aspect_ratio
        self.image_size = image_size
        self.timeout = _positive_number("timeout", timeout)
        self.max_prompt_chars = _positive_int("max_prompt_chars", max_prompt_chars, maximum=100_000)
        self.max_image_bytes = _positive_int(
            "max_image_bytes", max_image_bytes, maximum=100_000_000
        )
        self.transport = transport or _http_json_transport
        self.name = f"google_vertex:{self.model}"

    def _project_id(self) -> str:
        candidate = self._explicit_project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not candidate:
            candidate = os.environ.get("GCLOUD_PROJECT")
        if not isinstance(candidate, str) or not candidate.strip():
            raise VertexImageGenerationError(
                "Vertex image generation requires project_id or GOOGLE_CLOUD_PROJECT."
            )
        return candidate.strip()

    def _access_token(self) -> str:
        candidate = self._explicit_access_token or os.environ.get("GOOGLE_CLOUD_ACCESS_TOKEN")
        if candidate is None and self.token_provider is not None:
            candidate = self.token_provider()
        if candidate is not None:
            if not isinstance(candidate, str) or not candidate.strip():
                raise VertexImageGenerationError("Vertex token provider returned no access token.")
            return candidate.strip()

        try:
            import google.auth
            from google.auth.transport.requests import Request
        except ImportError as exc:
            raise VertexImageGenerationError(
                "Vertex authentication requires the optional google-auth dependency. "
                "Install apr-runtime-mvp[vertex] or provide token_provider."
            ) from exc

        scopes = [GOOGLE_CLOUD_SCOPE]
        try:
            if self.credentials_path is not None:
                from google.oauth2 import service_account

                credentials = service_account.Credentials.from_service_account_file(
                    str(self.credentials_path), scopes=scopes
                )
            else:
                credentials, _ = google.auth.default(scopes=scopes)
        except Exception as exc:
            raise VertexImageGenerationError(
                "Vertex application credentials could not be loaded."
            ) from exc
        try:
            credentials.refresh(Request())
        except Exception as exc:
            raise VertexImageGenerationError(
                f"Vertex access-token refresh failed: {_safe_error_message(str(exc))}"
            ) from exc
        token = getattr(credentials, "token", None)
        if not isinstance(token, str) or not token.strip():
            raise VertexImageGenerationError("Vertex authentication returned no access token.")
        return token.strip()

    def _url(self, project_id: str) -> str:
        host = (
            "aiplatform.googleapis.com"
            if self.location == "global"
            else f"{self.location}-aiplatform.googleapis.com"
        )
        project = urllib_parse.quote(project_id, safe="")
        location = urllib_parse.quote(self.location, safe="")
        model = urllib_parse.quote(self.model, safe="")
        return (
            f"https://{host}/v1/projects/{project}/locations/{location}/"
            f"publishers/google/models/{model}:generateContent"
        )

    def generate(
        self,
        prompt: str,
        *,
        output_path: str | Path,
        overwrite: bool = False,
    ) -> ImageGenerationResult:
        prompt = _non_empty("prompt", prompt)
        if len(prompt) > self.max_prompt_chars:
            raise ValueError(
                f"prompt is {len(prompt)} characters; configured maximum is "
                f"{self.max_prompt_chars}."
            )
        if not isinstance(overwrite, bool):
            raise TypeError("overwrite must be boolean")

        requested_target = Path(output_path).expanduser().resolve()
        if requested_target.suffix.lower() not in {".jpeg", ".jpg", ".png"}:
            raise ValueError("Vertex image output_path must use a .png, .jpg, or .jpeg extension")
        stem = requested_target.name[: -len(requested_target.suffix)]
        possible_targets = {
            requested_target.parent / f"{stem}.png",
            requested_target.parent / f"{stem}.jpg",
            requested_target.parent / f"{stem}.jpeg",
        }
        if not overwrite:
            existing = next((path for path in possible_targets if path.exists()), None)
            if existing is not None:
                raise FileExistsError(f"Generated image already exists: {existing}")

        project_id = self._project_id()
        access_token = self._access_token()
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "candidateCount": 1,
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": self.aspect_ratio,
                    "imageSize": self.image_size,
                },
            },
        }
        started = time.perf_counter()
        response = self.transport(
            self._url(project_id),
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "apr-runtime-mvp",
            },
            payload,
            self.timeout,
        )
        elapsed = time.perf_counter() - started

        candidates = response.get("candidates", [])
        if not isinstance(candidates, list) or not candidates:
            prompt_feedback = response.get("promptFeedback", {})
            block = (
                prompt_feedback.get("blockReason") if isinstance(prompt_feedback, dict) else None
            )
            detail = f" ({block})" if block else ""
            raise VertexImageGenerationError(f"Vertex returned no image candidate{detail}.")
        candidate = candidates[0]
        if not isinstance(candidate, dict):
            raise VertexImageGenerationError("Vertex returned an invalid image candidate.")
        content = candidate.get("content", {})
        parts = content.get("parts", []) if isinstance(content, dict) else []
        image_parts = [
            part.get("inlineData")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("inlineData"), dict)
        ]
        if len(image_parts) != 1:
            raise VertexImageGenerationError(
                f"Vertex returned {len(image_parts)} image parts; exactly one was requested."
            )

        inline = image_parts[0]
        mime_type = inline.get("mimeType")
        encoded = inline.get("data")
        if not isinstance(mime_type, str) or not isinstance(encoded, str):
            raise VertexImageGenerationError("Vertex did not return a valid image payload.")
        try:
            image_data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise VertexImageGenerationError("Vertex returned invalid base64 image data.") from exc
        if not image_data:
            raise VertexImageGenerationError("Vertex returned an empty image.")
        if len(image_data) > self.max_image_bytes:
            raise VertexImageGenerationError(
                f"Vertex image is {len(image_data)} bytes; configured maximum is "
                f"{self.max_image_bytes} bytes."
            )
        mime_type, extension, width, height = _image_details(image_data, mime_type)
        target = requested_target.parent / f"{stem}{extension}"

        target.parent.mkdir(parents=True, exist_ok=True)
        mode = "wb" if overwrite else "xb"
        try:
            with target.open(mode) as handle:
                handle.write(image_data)
        except FileExistsError:
            raise
        except OSError as exc:
            raise VertexImageGenerationError("Generated image could not be persisted.") from exc

        usage = _usage_metadata(response, model=self.model, location=self.location)
        return ImageGenerationResult(
            path=target,
            prompt=prompt,
            provider="google_vertex",
            model=str(response.get("modelVersion") or self.model),
            mime_type=mime_type,
            width=width,
            height=height,
            byte_count=len(image_data),
            sha256=hashlib.sha256(image_data).hexdigest(),
            metadata={
                "location": self.location,
                "aspect_ratio": self.aspect_ratio,
                "image_size": self.image_size,
                "response_id": response.get("responseId"),
                "finish_reason": candidate.get("finishReason"),
                "elapsed_seconds": round(elapsed, 3),
                "usage": usage,
            },
        )


class GoogleVertexImageGenerationPlugin:
    """Explicit APR plugin for real image generation through Google Vertex AI."""

    name = "google_vertex_image_generation"

    def register(self, registry: PluginRegistry) -> None:
        registry.register_component("image_generator", "google_vertex", GoogleVertexImageGenerator)
