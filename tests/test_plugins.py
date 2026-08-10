import unittest
from unittest.mock import Mock, patch

from apr_runtime.plugins import (
    DuplicateComponentError,
    PluginLoadError,
    PluginRegistry,
)


class ExamplePlugin:
    name = "example"

    def register(self, registry: PluginRegistry) -> None:
        registry.register_component("adapter", "echo", lambda value: value)


class BrokenPlugin:
    name = "broken"

    def register(self, registry: PluginRegistry) -> None:
        registry.register_component("adapter", "temporary", lambda: None)
        raise RuntimeError("registration failed")


class PluginRegistryTests(unittest.TestCase):
    def test_install_and_create_component(self):
        registry = PluginRegistry()
        registry.install(ExamplePlugin())

        self.assertEqual(registry.plugin_names, ("example",))
        self.assertEqual(registry.create_component("adapter", "echo", "ok"), "ok")

    def test_duplicate_component_requires_explicit_replace(self):
        registry = PluginRegistry()
        registry.register_component("source", "demo", lambda: 1)
        with self.assertRaises(DuplicateComponentError):
            registry.register_component("source", "demo", lambda: 2)

        registry.register_component("source", "demo", lambda: 2, replace=True)
        self.assertEqual(registry.create_component("source", "demo"), 2)

    def test_failed_install_rolls_back_partial_registration(self):
        registry = PluginRegistry()
        with self.assertRaisesRegex(RuntimeError, "registration failed"):
            registry.install(BrokenPlugin())

        self.assertEqual(registry.components("adapter"), {})
        self.assertEqual(registry.plugin_names, ())

    @patch("apr_runtime.plugins.metadata.entry_points")
    def test_entry_point_load_report_keeps_failures_explicit(self, entry_points):
        good = Mock(name="good_entry_point")
        good.name = "good"
        good.load.return_value = ExamplePlugin
        bad = Mock(name="bad_entry_point")
        bad.name = "bad"
        bad.load.side_effect = ImportError("missing dependency")
        entry_points.return_value = [good, bad]

        report = PluginRegistry().load_entry_points()

        self.assertFalse(report.ok)
        self.assertEqual([item.plugin_name for item in report.loaded], ["example"])
        self.assertEqual(report.failures[0].entry_point, "bad")
        self.assertIn("missing dependency", report.failures[0].error)

    @patch("apr_runtime.plugins.metadata.entry_points")
    def test_strict_entry_point_loading_raises(self, entry_points):
        bad = Mock(name="bad_entry_point")
        bad.name = "bad"
        bad.load.side_effect = ImportError("missing dependency")
        entry_points.return_value = [bad]

        with self.assertRaises(PluginLoadError):
            PluginRegistry().load_entry_points(strict=True)


if __name__ == "__main__":
    unittest.main()
