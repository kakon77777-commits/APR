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

## Built-in hosted semantic inspectors

APR ships an explicit plugin for OpenAI Responses and Anthropic Messages vision inspection. It
uses only the Python standard library, performs no network work during registration or component
creation, reads credentials lazily at inspection time, and never writes credentials into evidence.

```python
from apr_runtime import HostedSemanticInspectorsPlugin, PluginRegistry

registry = PluginRegistry()
registry.install(HostedSemanticInspectorsPlugin())

openai = registry.create_component("semantic_inspector", "openai")
anthropic = registry.create_component("semantic_inspector", "anthropic")
```

Set `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` in the process environment. Defaults are bounded
for inexpensive smoke tests: `gpt-5.6-luna`, `claude-haiku-4-5-20251001`, 512 maximum output
tokens, 60-second timeout, a 5 MB image limit, and no automatic retries. OpenAI requests use the
Responses API with `store=false`; both providers use JSON Schema output and return token/cost
metadata through `SemanticResult.raw`. Fact lifecycle is deterministic APR policy rather than
model output: hosted inspectors default to `fact_volatile=True` and `fact_ttl=5.0`, both
configurable at component creation.

Run the synthetic cross-provider check only after setting both variables:

```powershell
python examples/run_hosted_semantic_comparison.py --provider both
```

The example makes exactly one generation request per selected provider. API pricing and model
availability change, so verify current provider documentation before changing the defaults.

## Failure and trust semantics

- A plugin whose `register()` raises is rolled back to the pre-install registry state.
- One failed entry point does not hide other failures in report mode.
- Entry-point loading imports and executes third-party Python code. APR never performs it automatically.
- The registry provides composition and provenance boundaries, not sandboxing. Use only trusted plugin distributions or isolate them at the process/container level.

## Compatibility

The plugin API is introduced during the v0.10 repository-integration phase. Treat it as provisional until v1.0; plugins should declare the APR versions they test against.
