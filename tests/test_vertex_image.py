from __future__ import annotations

import base64
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from apr_runtime import (
    GoogleVertexImageGenerationPlugin,
    GoogleVertexImageGenerator,
    ImageGenerationResult,
    PluginRegistry,
    VertexImageGenerationError,
)


def fake_png(width: int = 32, height: int = 24, *, padding: int = 0) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x06\x00\x00\x00"
        + (b"x" * padding)
    )


def fake_jpeg(width: int = 40, height: int = 30) -> bytes:
    sof = (
        b"\xff\xc0"
        + struct.pack(">H", 17)
        + b"\x08"
        + struct.pack(">HH", height, width)
        + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
    )
    return b"\xff\xd8" + sof + b"\xff\xd9"


def response_with_image(
    image: bytes,
    *,
    mime_type: str = "image/png",
    prompt_tokens: int = 10,
    image_tokens: int = 1120,
) -> dict:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": base64.b64encode(image).decode("ascii"),
                            }
                        }
                    ]
                },
                "finishReason": "STOP",
            }
        ],
        "modelVersion": "gemini-3.1-flash-lite-image",
        "responseId": "response-test",
        "usageMetadata": {
            "promptTokenCount": prompt_tokens,
            "candidatesTokenCount": image_tokens,
            "totalTokenCount": prompt_tokens + image_tokens,
            "candidatesTokensDetails": [{"modality": "IMAGE", "tokenCount": image_tokens}],
        },
    }


class VertexImageGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.output = Path(self.tmp.name) / "generated.png"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_builds_bounded_vertex_request_and_persists_png(self):
        captured = {}
        token_calls = []

        def token_provider():
            token_calls.append(True)
            return "test-access-token"

        def transport(url, headers, payload, timeout):
            captured.update(url=url, headers=headers, payload=payload, timeout=timeout)
            return response_with_image(fake_png(64, 48))

        generator = GoogleVertexImageGenerator(
            project_id="safe-project",
            token_provider=token_provider,
            transport=transport,
        )
        self.assertEqual(token_calls, [])
        result = generator.generate("Draw one instrument.", output_path=self.output)

        self.assertIsInstance(result, ImageGenerationResult)
        self.assertEqual(token_calls, [True])
        self.assertTrue(self.output.is_file())
        self.assertEqual((result.width, result.height), (64, 48))
        self.assertEqual(result.mime_type, "image/png")
        self.assertIn("https://aiplatform.googleapis.com/", captured["url"])
        self.assertIn("/locations/global/", captured["url"])
        self.assertIn("safe-project", captured["url"])
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-access-token")
        config = captured["payload"]["generationConfig"]
        self.assertEqual(config["candidateCount"], 1)
        self.assertEqual(config["responseModalities"], ["IMAGE"])
        self.assertEqual(config["imageConfig"]["imageSize"], "1K")
        self.assertNotIn("outputMimeType", config["imageConfig"])
        usage = result.metadata["usage"]
        self.assertEqual(usage["image_output_tokens"], 1120)
        self.assertEqual(usage["pricing_scope"], "global")
        self.assertAlmostEqual(usage["estimated_cost_usd"], 0.0336025)

    def test_existing_output_blocks_before_auth_or_network(self):
        self.output.write_bytes(b"existing")
        token = mock.Mock(return_value="token")
        transport = mock.Mock()
        generator = GoogleVertexImageGenerator(
            project_id="safe-project", token_provider=token, transport=transport
        )
        with self.assertRaises(FileExistsError):
            generator.generate("Draw one object.", output_path=self.output)
        token.assert_not_called()
        transport.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b"existing")

    def test_known_model_rejects_an_unsupported_size_before_auth(self):
        token = mock.Mock(return_value="token")
        with self.assertRaisesRegex(ValueError, "supports image_size"):
            GoogleVertexImageGenerator(
                project_id="safe-project",
                token_provider=token,
                image_size="512",
            )
        token.assert_not_called()

    def test_jpeg_response_uses_a_truthful_file_extension(self):
        generator = GoogleVertexImageGenerator(
            project_id="safe-project",
            access_token="token",
            transport=lambda *_: response_with_image(fake_jpeg(80, 60), mime_type="image/jpeg"),
        )
        result = generator.generate("Draw one object.", output_path=self.output)
        self.assertEqual(result.path.suffix, ".jpg")
        self.assertEqual(result.mime_type, "image/jpeg")
        self.assertEqual((result.width, result.height), (80, 60))
        self.assertFalse(self.output.exists())
        self.assertTrue(result.path.exists())

    def test_missing_project_blocks_before_auth_or_network(self):
        token = mock.Mock(return_value="token")
        transport = mock.Mock()
        generator = GoogleVertexImageGenerator(token_provider=token, transport=transport)
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(VertexImageGenerationError, "GOOGLE_CLOUD_PROJECT"):
                generator.generate("Draw one object.", output_path=self.output)
        token.assert_not_called()
        transport.assert_not_called()

    def test_invalid_base64_does_not_create_output(self):
        response = response_with_image(fake_png())
        response["candidates"][0]["content"]["parts"][0]["inlineData"]["data"] = "%%%"
        generator = GoogleVertexImageGenerator(
            project_id="safe-project",
            access_token="token",
            transport=lambda *_: response,
        )
        with self.assertRaisesRegex(VertexImageGenerationError, "base64"):
            generator.generate("Draw one object.", output_path=self.output)
        self.assertFalse(self.output.exists())

    def test_oversized_image_does_not_create_output(self):
        image = fake_png(padding=200)
        generator = GoogleVertexImageGenerator(
            project_id="safe-project",
            access_token="token",
            max_image_bytes=64,
            transport=lambda *_: response_with_image(image),
        )
        with self.assertRaisesRegex(VertexImageGenerationError, "configured maximum"):
            generator.generate("Draw one object.", output_path=self.output)
        self.assertFalse(self.output.exists())

    def test_blocked_prompt_is_reported_without_writing(self):
        generator = GoogleVertexImageGenerator(
            project_id="safe-project",
            access_token="token",
            transport=lambda *_: {"promptFeedback": {"blockReason": "SAFETY"}},
        )
        with self.assertRaisesRegex(VertexImageGenerationError, "SAFETY"):
            generator.generate("Draw one object.", output_path=self.output)
        self.assertFalse(self.output.exists())

    def test_unknown_model_reports_usage_without_price_claim(self):
        generator = GoogleVertexImageGenerator(
            project_id="safe-project",
            access_token="token",
            model="future-image-model",
            transport=lambda *_: response_with_image(fake_png()),
        )
        result = generator.generate("Draw one object.", output_path=self.output)
        self.assertEqual(result.metadata["usage"]["image_output_tokens"], 1120)
        self.assertIsNone(result.metadata["usage"]["estimated_cost_usd"])
        self.assertIsNone(result.metadata["usage"]["pricing_scope"])

    def test_plugin_registration_is_network_free(self):
        registry = PluginRegistry()
        registry.install(GoogleVertexImageGenerationPlugin())
        generator = registry.create_component(
            "image_generator",
            "google_vertex",
            project_id="safe-project",
            token_provider=lambda: "token",
            transport=lambda *_: response_with_image(fake_png()),
        )
        self.assertIsInstance(generator, GoogleVertexImageGenerator)
        self.assertIn("google_vertex_image_generation", registry.plugin_names)


if __name__ == "__main__":
    unittest.main()
