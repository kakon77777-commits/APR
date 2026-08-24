from __future__ import annotations

import base64
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from .plugins import PluginRegistry
from .semantic import SemanticFact, SemanticResult

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_OPENAI_MODEL = "gpt-5.6-luna"
DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

# USD per million tokens. Unknown model overrides still report tokens but not
# a potentially misleading price estimate.
_OPENAI_PRICING = {
    "gpt-5.6-luna": (1.0, 0.1, 1.25, 6.0),
}
_ANTHROPIC_PRICING = {
    "claude-haiku-4-5": (1.0, 0.1, 1.25, 5.0),
    "claude-haiku-4-5-20251001": (1.0, 0.1, 1.25, 5.0),
}

_SUPPORTED_IMAGE_TYPES = {
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
_SECRET_PATTERN = re.compile(r"sk-(?:proj-|ant-)?[A-Za-z0-9_-]{8,}", re.IGNORECASE)

SEMANTIC_RESULT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "confidence": {"type": "number"},
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": ["string", "number", "boolean", "null"]},
                    "confidence": {"type": "number"},
                },
                "required": ["key", "value", "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "confidence", "facts"],
    "additionalProperties": False,
}

_SYSTEM_INSTRUCTIONS = (
    "You are an APR semantic perception inspector. Use only pixels visible in the supplied "
    "image and the bounded APR context. Do not infer hidden state. Emit a compact summary and "
    "only decision-relevant facts justified by the image. Use stable dotted fact keys, calibrate "
    "confidence, and return no more than eight facts."
)

JsonTransport = Callable[[str, Mapping[str, str], Mapping[str, Any], float], Mapping[str, Any]]


class HostedSemanticError(RuntimeError):
    """Safe provider failure that never includes an API credential."""


def _safe_error_message(value: str, *, limit: int = 600) -> str:
    value = _SECRET_PATTERN.sub("sk-<redacted>", value)
    return " ".join(value.split())[:limit]


def _http_json_transport(
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    timeout: float,
) -> Mapping[str, Any]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib_request.Request(
        url,
        data=body,
        headers=dict(headers),
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            decoded = json.loads(raw)
            message = decoded.get("error", {}).get("message", raw)
        except (AttributeError, json.JSONDecodeError):
            message = raw
        raise HostedSemanticError(
            f"Hosted semantic API returned HTTP {exc.code}: {_safe_error_message(str(message))}"
        ) from exc
    except urllib_error.URLError as exc:
        raise HostedSemanticError(
            f"Hosted semantic API connection failed: {_safe_error_message(str(exc.reason))}"
        ) from exc

    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HostedSemanticError("Hosted semantic API returned invalid JSON.") from exc
    if not isinstance(decoded, dict):
        raise HostedSemanticError("Hosted semantic API returned a non-object JSON response.")
    return decoded


def _require_positive_number(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive value")
    return value


def _require_non_negative_number(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative value")
    return value


def _require_positive_int(name: str, value: int, *, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value > maximum:
        raise ValueError(f"{name} must be an integer in [1, {maximum}]")
    return value


def _require_api_key(explicit: Optional[str], environment_name: str, provider: str) -> str:
    candidate = explicit if explicit is not None else os.environ.get(environment_name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise HostedSemanticError(
            f"{provider} semantic inspection requires the {environment_name} environment variable."
        )
    return candidate.strip()


def _encode_image(image_path: str | Path, *, max_image_bytes: int) -> tuple[str, str]:
    path = Path(image_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Semantic image does not exist: {path}")
    media_type = _SUPPORTED_IMAGE_TYPES.get(path.suffix.lower())
    if media_type is None:
        supported = ", ".join(sorted(_SUPPORTED_IMAGE_TYPES))
        raise ValueError(f"Unsupported semantic image type; expected one of: {supported}")
    size = path.stat().st_size
    if size > max_image_bytes:
        raise ValueError(
            f"Semantic image is {size} bytes; configured maximum is {max_image_bytes} bytes."
        )
    return media_type, base64.b64encode(path.read_bytes()).decode("ascii")


def _bounded_prompt(prompt: str, context: Mapping[str, Any], *, max_chars: int) -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")
    context_json = json.dumps(
        context,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    combined = f"{prompt.strip()}\nAPR context: {context_json}"
    if len(combined) > max_chars:
        raise ValueError(
            f"Semantic prompt is {len(combined)} characters; configured maximum is {max_chars}."
        )
    return combined


def _probability(name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise HostedSemanticError(f"Provider field {name!r} must be numeric.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise HostedSemanticError(f"Provider field {name!r} must be numeric.") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise HostedSemanticError(f"Provider field {name!r} must be between 0 and 1.")
    return number


def _semantic_result(
    structured: Any,
    *,
    provider: str,
    model: str,
    fact_volatile: bool,
    fact_ttl: float,
    raw_metadata: Mapping[str, Any],
) -> SemanticResult:
    if not isinstance(structured, dict):
        raise HostedSemanticError(f"{provider} returned a non-object semantic result.")
    summary = structured.get("summary")
    facts_payload = structured.get("facts")
    if not isinstance(summary, str):
        raise HostedSemanticError(f"{provider} semantic summary must be a string.")
    if not isinstance(facts_payload, list):
        raise HostedSemanticError(f"{provider} semantic facts must be an array.")
    if len(facts_payload) > 16:
        raise HostedSemanticError(f"{provider} returned more than 16 semantic facts.")

    facts = []
    for index, item in enumerate(facts_payload):
        if not isinstance(item, dict):
            raise HostedSemanticError(f"{provider} fact {index} must be an object.")
        key = item.get("key")
        value = item.get("value")
        if not isinstance(key, str) or not key.strip():
            raise HostedSemanticError(f"{provider} fact {index} has an invalid key.")
        if isinstance(value, (dict, list)):
            raise HostedSemanticError(f"{provider} fact {index} value must be a JSON scalar.")
        facts.append(
            SemanticFact(
                key=key.strip(),
                value=value,
                confidence=_probability(f"facts[{index}].confidence", item.get("confidence")),
                volatile=fact_volatile,
                ttl=fact_ttl,
                metadata={
                    "provider": provider,
                    "model": model,
                    "lifecycle_source": "inspector_config",
                },
            )
        )

    return SemanticResult(
        summary=summary.strip(),
        facts=facts,
        confidence=_probability("confidence", structured.get("confidence")),
        raw=dict(raw_metadata),
    )


def _openai_output_text(payload: Mapping[str, Any]) -> str:
    parts = []
    refusals = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                parts.append(content["text"])
            elif content.get("type") == "refusal":
                refusals.append(str(content.get("refusal", "request refused")))
    if refusals:
        raise HostedSemanticError(f"OpenAI refused semantic inspection: {refusals[0]}")
    if not parts:
        raise HostedSemanticError("OpenAI returned no semantic output text.")
    return "".join(parts)


def _anthropic_output_text(payload: Mapping[str, Any]) -> str:
    parts = [
        item["text"]
        for item in payload.get("content", [])
        if isinstance(item, dict)
        and item.get("type") == "text"
        and isinstance(item.get("text"), str)
    ]
    if not parts:
        raise HostedSemanticError("Anthropic returned no semantic output text.")
    return "".join(parts)


def _cost_metadata(
    usage: Mapping[str, Any],
    *,
    pricing: Optional[tuple[float, float, float, float]],
    anthropic: bool = False,
) -> Dict[str, Any]:
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    if anthropic:
        cached_tokens = int(usage.get("cache_read_input_tokens", 0) or 0)
        cache_write_tokens = int(usage.get("cache_creation_input_tokens", 0) or 0)
    else:
        details = usage.get("input_tokens_details", {})
        details = details if isinstance(details, dict) else {}
        cached_tokens = int(details.get("cached_tokens", 0) or 0)
        cache_write_tokens = int(details.get("cache_write_tokens", 0) or 0)
    result = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached_tokens,
        "cache_write_input_tokens": cache_write_tokens,
    }
    if pricing is None:
        result["estimated_cost_usd"] = None
        return result

    input_rate, cached_input_rate, cache_write_rate, output_rate = pricing
    uncached_tokens = max(0, input_tokens - cached_tokens - cache_write_tokens)
    estimated_cost = (
        uncached_tokens * input_rate
        + cached_tokens * cached_input_rate
        + cache_write_tokens * cache_write_rate
        + output_tokens * output_rate
    ) / 1_000_000
    result["estimated_cost_usd"] = round(estimated_cost, 8)
    return result


class OpenAIResponsesSemanticInspector:
    """APR vision inspector backed by OpenAI's Responses API."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: str = DEFAULT_OPENAI_MODEL,
        max_output_tokens: int = 512,
        reasoning_effort: str = "none",
        image_detail: str = "low",
        timeout: float = 60.0,
        max_image_bytes: int = 5_000_000,
        max_prompt_chars: int = 8_000,
        fact_volatile: bool = True,
        fact_ttl: float = 5.0,
        estimated_cost: float = 1.0,
        transport: Optional[JsonTransport] = None,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")
        if reasoning_effort not in {"none", "low", "medium", "high", "xhigh", "max"}:
            raise ValueError("unsupported OpenAI reasoning_effort")
        if image_detail not in {"low", "high", "auto", "original"}:
            raise ValueError("unsupported OpenAI image_detail")
        if not isinstance(fact_volatile, bool):
            raise TypeError("fact_volatile must be boolean")
        self._explicit_api_key = api_key
        self.model = model.strip()
        self.max_output_tokens = _require_positive_int(
            "max_output_tokens", max_output_tokens, maximum=4_096
        )
        self.reasoning_effort = reasoning_effort
        self.image_detail = image_detail
        self.timeout = _require_positive_number("timeout", timeout)
        self.max_image_bytes = _require_positive_int(
            "max_image_bytes", max_image_bytes, maximum=20_000_000
        )
        self.max_prompt_chars = _require_positive_int(
            "max_prompt_chars", max_prompt_chars, maximum=100_000
        )
        self.fact_volatile = fact_volatile
        self.fact_ttl = _require_non_negative_number("fact_ttl", fact_ttl)
        self.estimated_cost = _require_positive_number("estimated_cost", estimated_cost)
        self.transport = transport or _http_json_transport
        self.name = f"openai:{self.model}"

    def inspect(
        self,
        image_path: str | Path,
        *,
        prompt: str,
        context: Dict[str, Any],
    ) -> SemanticResult:
        api_key = _require_api_key(self._explicit_api_key, "OPENAI_API_KEY", "OpenAI")
        media_type, image_data = _encode_image(image_path, max_image_bytes=self.max_image_bytes)
        bounded_prompt = _bounded_prompt(prompt, context, max_chars=self.max_prompt_chars)
        request_payload = {
            "model": self.model,
            "store": False,
            "max_output_tokens": self.max_output_tokens,
            "reasoning": {"effort": self.reasoning_effort},
            "instructions": _SYSTEM_INSTRUCTIONS,
            "text": {
                "verbosity": "low",
                "format": {
                    "type": "json_schema",
                    "name": "apr_semantic_result",
                    "strict": True,
                    "schema": SEMANTIC_RESULT_SCHEMA,
                },
            },
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": f"data:{media_type};base64,{image_data}",
                            "detail": self.image_detail,
                        },
                        {"type": "input_text", "text": bounded_prompt},
                    ],
                }
            ],
        }
        response = self.transport(
            OPENAI_RESPONSES_URL,
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "apr-runtime-mvp",
            },
            request_payload,
            self.timeout,
        )
        if response.get("status") != "completed":
            reason = response.get("incomplete_details") or response.get("error") or "unknown"
            raise HostedSemanticError(f"OpenAI response did not complete: {reason}")
        try:
            structured = json.loads(_openai_output_text(response))
        except json.JSONDecodeError as exc:
            raise HostedSemanticError("OpenAI semantic output was not valid JSON.") from exc

        usage = response.get("usage", {})
        usage = usage if isinstance(usage, dict) else {}
        cost = _cost_metadata(
            usage,
            pricing=_OPENAI_PRICING.get(self.model),
        )
        response_model = str(response.get("model") or self.model)
        return _semantic_result(
            structured,
            provider="openai",
            model=response_model,
            fact_volatile=self.fact_volatile,
            fact_ttl=self.fact_ttl,
            raw_metadata={
                "provider": "openai",
                "model": response_model,
                "request_id": response.get("id"),
                "status": response.get("status"),
                "usage": cost,
            },
        )


class AnthropicMessagesSemanticInspector:
    """APR vision inspector backed by Anthropic's Messages API."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: str = DEFAULT_ANTHROPIC_MODEL,
        max_output_tokens: int = 512,
        timeout: float = 60.0,
        max_image_bytes: int = 5_000_000,
        max_prompt_chars: int = 8_000,
        fact_volatile: bool = True,
        fact_ttl: float = 5.0,
        estimated_cost: float = 1.0,
        transport: Optional[JsonTransport] = None,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")
        if not isinstance(fact_volatile, bool):
            raise TypeError("fact_volatile must be boolean")
        self._explicit_api_key = api_key
        self.model = model.strip()
        self.max_output_tokens = _require_positive_int(
            "max_output_tokens", max_output_tokens, maximum=4_096
        )
        self.timeout = _require_positive_number("timeout", timeout)
        self.max_image_bytes = _require_positive_int(
            "max_image_bytes", max_image_bytes, maximum=10_000_000
        )
        self.max_prompt_chars = _require_positive_int(
            "max_prompt_chars", max_prompt_chars, maximum=100_000
        )
        self.fact_volatile = fact_volatile
        self.fact_ttl = _require_non_negative_number("fact_ttl", fact_ttl)
        self.estimated_cost = _require_positive_number("estimated_cost", estimated_cost)
        self.transport = transport or _http_json_transport
        self.name = f"anthropic:{self.model}"

    def inspect(
        self,
        image_path: str | Path,
        *,
        prompt: str,
        context: Dict[str, Any],
    ) -> SemanticResult:
        api_key = _require_api_key(self._explicit_api_key, "ANTHROPIC_API_KEY", "Anthropic")
        media_type, image_data = _encode_image(image_path, max_image_bytes=self.max_image_bytes)
        bounded_prompt = _bounded_prompt(prompt, context, max_chars=self.max_prompt_chars)
        request_payload = {
            "model": self.model,
            "max_tokens": self.max_output_tokens,
            "system": _SYSTEM_INSTRUCTIONS,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": bounded_prompt},
                    ],
                }
            ],
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "schema": SEMANTIC_RESULT_SCHEMA,
                }
            },
        }
        response = self.transport(
            ANTHROPIC_MESSAGES_URL,
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
                "User-Agent": "apr-runtime-mvp",
            },
            request_payload,
            self.timeout,
        )
        stop_reason = response.get("stop_reason")
        if stop_reason in {"max_tokens", "refusal"}:
            raise HostedSemanticError(f"Anthropic response stopped with reason: {stop_reason}")
        try:
            structured = json.loads(_anthropic_output_text(response))
        except json.JSONDecodeError as exc:
            raise HostedSemanticError("Anthropic semantic output was not valid JSON.") from exc

        usage = response.get("usage", {})
        usage = usage if isinstance(usage, dict) else {}
        cost = _cost_metadata(
            usage,
            pricing=_ANTHROPIC_PRICING.get(self.model),
            anthropic=True,
        )
        response_model = str(response.get("model") or self.model)
        return _semantic_result(
            structured,
            provider="anthropic",
            model=response_model,
            fact_volatile=self.fact_volatile,
            fact_ttl=self.fact_ttl,
            raw_metadata={
                "provider": "anthropic",
                "model": response_model,
                "request_id": response.get("id"),
                "status": stop_reason,
                "usage": cost,
            },
        )


class HostedSemanticInspectorsPlugin:
    """Explicit APR plugin for the two hosted semantic inspectors."""

    name = "hosted_semantic_inspectors"

    def register(self, registry: PluginRegistry) -> None:
        registry.register_component(
            "semantic_inspector", "openai", OpenAIResponsesSemanticInspector
        )
        registry.register_component(
            "semantic_inspector", "anthropic", AnthropicMessagesSemanticInspector
        )
