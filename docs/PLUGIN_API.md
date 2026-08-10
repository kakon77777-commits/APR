# APR Plugin API

APR plugins are explicit Python extensions. They register named component factories; they do not patch global state or start resources during discovery.

## Contract

```python
from apr_runtime import PluginRegistry


class ExamplePlugin:
    name = "example"

    def register(self, registry: PluginRegistry) -> None:
        registry.register_component("adapter", "camera", CameraAdapter)
        registry.register_component("inspector", "local-vlm", LocalVLMInspector)
```

`name` must be non-empty and `register()` must be callable. Registration should only declare factories. Defer network connections, subprocesses, model loading, browser startup, and device acquisition until a component is explicitly created.

## Component namespaces

The registry accepts any non-empty `kind`; recommended shared names are:

- `adapter`
- `source`
- `semantic_inspector`
- `policy`
- `event_handler`
- `persistence`

Factories can be classes or functions:

```python
registry = PluginRegistry()
registry.install(ExamplePlugin())
camera = registry.create_component("adapter", "camera", device_id=0)
```

Duplicate component names fail by default. A plugin must pass `replace=True` deliberately when it owns an intentional override.

## Distribution entry point

A third-party package can advertise a zero-argument plugin class or plugin instance:

```toml
[project.entry-points."apr_runtime.plugins"]
example = "example_apr.plugin:ExamplePlugin"
```

The host decides when to load installed entry points:

```python
registry = PluginRegistry()
report = registry.load_entry_points()

for failure in report.failures:
    print(failure.entry_point, failure.error)
```

Use `strict=True` when any load failure must stop startup:

```python
registry.load_entry_points(strict=True)
```

## Failure and trust semantics

- A plugin whose `register()` raises is rolled back to the pre-install registry state.
- One failed entry point does not hide other failures in report mode.
- Entry-point loading imports and executes third-party Python code. APR never performs it automatically.
- The registry provides composition and provenance boundaries, not sandboxing. Use only trusted plugin distributions or isolate them at the process/container level.

## Compatibility

The plugin API is introduced during the v0.10 repository-integration phase. Treat it as provisional until v1.0; plugins should declare the APR versions they test against.
