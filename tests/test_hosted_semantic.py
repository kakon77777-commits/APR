import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from apr_runtime import PluginRegistry, ScreenFrame, save_frame_png
from apr_runtime.hosted_semantic import (
    ANTHROPIC_MESSAGES_URL,
    OPENAI_RESPONSES_URL,
    SEMANTIC_RESULT_SCHEMA,
    AnthropicMessagesSemanticInspector,
    HostedSemanticError,
    HostedSemanticInspectorsPlugin,
    OpenAIResponsesSemanticInspector,
)


def semantic_payload():
    return {
        "summary": "A destructive confirmation dialog is visible.",
        "confidence": 0.96,
        "facts": [
            {
                "key": "desktop.dialog.visible",
                "value": True,
                "confidence": 0.99,
            }
        ],
    }


class HostedSemanticInspectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.image = Path(self.tmp.name) / "sample.png"
        frame = ScreenFrame(1, 1, bytes([0, 0, 255, 255]))
        save_frame_png(frame, self.image)

    def tearDown(self):
        self.tmp.cleanup()

    def test_openai_builds_bounded_responses_request_and_parses_usage(self):
        captured = {}

        def transport(url, headers, payload, timeout):
            captured.update(url=url, headers=headers, payload=payload, timeout=timeout)
            return {
                "id": "resp_test",
                "model": "gpt-5.6-luna",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": json.dumps(semantic_payload())}
                        ],
                    }
                ],
                "usage": {"input_tokens": 120, "output_tokens": 40},
            }

        inspector = OpenAIResponsesSemanticInspector(api_key="sk-test-openai", transport=transport)
        result = inspector.inspect(self.image, prompt="Inspect.", context={"goal": "safe"})

        self.assertEqual(captured["url"], OPENAI_RESPONSES_URL)
        self.assertEqual(captured["headers"]["Authorization"], "Bearer sk-test-openai")
        self.assertFalse(captured["payload"]["store"])
        self.assertEqual(captured["payload"]["max_output_tokens"], 512)
        self.assertEqual(captured["payload"]["reasoning"]["effort"], "none")
        image = captured["payload"]["input"][0]["content"][0]
        self.assertTrue(image["image_url"].startswith("data:image/png;base64,"))
        self.assertEqual(captured["payload"]["text"]["format"]["type"], "json_schema")
        self.assertEqual(result.facts[0].value, True)
        self.assertTrue(result.facts[0].volatile)
        self.assertEqual(result.facts[0].ttl, 5.0)
        self.assertEqual(result.facts[0].metadata["lifecycle_source"], "inspector_config")
        self.assertEqual(result.raw["usage"]["estimated_cost_usd"], 0.00036)

    def test_anthropic_builds_image_first_messages_request_and_parses_usage(self):
        captured = {}

        def transport(url, headers, payload, timeout):
            captured.update(url=url, headers=headers, payload=payload, timeout=timeout)
            return {
                "id": "msg_test",
                "model": "claude-haiku-4-5-20251001",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": json.dumps(semantic_payload())}],
                "usage": {"input_tokens": 100, "output_tokens": 40},
            }

        inspector = AnthropicMessagesSemanticInspector(api_key="sk-ant-test", transport=transport)
        result = inspector.inspect(self.image, prompt="Inspect.", context={"goal": "safe"})

        self.assertEqual(captured["url"], ANTHROPIC_MESSAGES_URL)
        self.assertEqual(captured["headers"]["x-api-key"], "sk-ant-test")
        self.assertEqual(captured["headers"]["anthropic-version"], "2023-06-01")
        first_content = captured["payload"]["messages"][0]["content"][0]
        self.assertEqual(first_content["type"], "image")
        self.assertEqual(captured["payload"]["output_config"]["format"]["type"], "json_schema")
        self.assertEqual(result.summary, "A destructive confirmation dialog is visible.")
        self.assertEqual(result.raw["usage"]["estimated_cost_usd"], 0.0003)

    def test_keys_are_resolved_lazily_from_environment(self):
        def transport(url, headers, payload, timeout):
            return {
                "id": "resp_env",
                "model": "gpt-5.6-luna",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": json.dumps(semantic_payload())}
                        ],
                    }
                ],
                "usage": {},
            }

        inspector = OpenAIResponsesSemanticInspector(transport=transport)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-test"}, clear=False):
            result = inspector.inspect(self.image, prompt="Inspect.", context={})
        self.assertEqual(result.raw["provider"], "openai")

    def test_missing_key_fails_before_network(self):
        transport_called = False

        def transport(url, headers, payload, timeout):
            nonlocal transport_called
            transport_called = True
            return {}

        inspector = AnthropicMessagesSemanticInspector(transport=transport)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(HostedSemanticError, "ANTHROPIC_API_KEY"):
                inspector.inspect(self.image, prompt="Inspect.", context={})
        self.assertFalse(transport_called)

    def test_invalid_provider_confidence_is_rejected(self):
        invalid = semantic_payload()
        invalid["confidence"] = 2

        def transport(url, headers, payload, timeout):
            return {
                "id": "msg_invalid",
                "model": "claude-haiku-4-5-20251001",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": json.dumps(invalid)}],
                "usage": {},
            }

        inspector = AnthropicMessagesSemanticInspector(api_key="sk-ant-test", transport=transport)
        with self.assertRaisesRegex(HostedSemanticError, "between 0 and 1"):
            inspector.inspect(self.image, prompt="Inspect.", context={})

    def test_unknown_model_override_does_not_claim_a_price(self):
        def transport(url, headers, payload, timeout):
            return {
                "id": "resp_custom",
                "model": "custom-model",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": json.dumps(semantic_payload())}
                        ],
                    }
                ],
                "usage": {"input_tokens": 100, "output_tokens": 20},
            }

        inspector = OpenAIResponsesSemanticInspector(
            api_key="sk-test-openai", model="custom-model", transport=transport
        )
        result = inspector.inspect(self.image, prompt="Inspect.", context={})

        self.assertIsNone(result.raw["usage"]["estimated_cost_usd"])

    def test_fact_lifecycle_is_deterministic_configuration(self):
        def transport(url, headers, payload, timeout):
            return {
                "id": "msg_lifecycle",
                "model": "claude-haiku-4-5-20251001",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": json.dumps(semantic_payload())}],
                "usage": {},
            }

        inspector = AnthropicMessagesSemanticInspector(
            api_key="sk-ant-test",
            fact_volatile=False,
            fact_ttl=30,
            transport=transport,
        )
        result = inspector.inspect(self.image, prompt="Inspect.", context={})

        fact = result.facts[0]
        self.assertFalse(fact.volatile)
        self.assertEqual(fact.ttl, 30.0)
        schema = SEMANTIC_RESULT_SCHEMA["properties"]["facts"]["items"]
        self.assertNotIn("volatile", schema["properties"])
        self.assertNotIn("ttl", schema["properties"])

    def test_plugin_registers_both_inspectors_without_starting_network(self):
        registry = PluginRegistry()
        registry.install(HostedSemanticInspectorsPlugin())

        self.assertEqual(registry.plugin_names, ("hosted_semantic_inspectors",))
        self.assertEqual(set(registry.components("semantic_inspector")), {"openai", "anthropic"})
        openai = registry.create_component("semantic_inspector", "openai")
        anthropic = registry.create_component("semantic_inspector", "anthropic")
        self.assertIsInstance(openai, OpenAIResponsesSemanticInspector)
        self.assertIsInstance(anthropic, AnthropicMessagesSemanticInspector)


if __name__ == "__main__":
    unittest.main()
