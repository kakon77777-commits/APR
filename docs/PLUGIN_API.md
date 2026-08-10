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
- `image_generator`
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

## Built-in Google Vertex image generator

APR also ships a provider-specific plugin behind the provider-neutral `ImageGenerator` protocol.
Registration and component creation are offline; authentication and network access begin only when
`generate()` is called.

```python
from apr_runtime import GoogleVertexImageGenerationPlugin, PluginRegistry

registry = PluginRegistry()
registry.install(GoogleVertexImageGenerationPlugin())
generator = registry.create_component(
    "image_generator",
    "google_vertex",
    project_id="your-project-id",
)
result = generator.generate("one brass instrument", output_path="artifact.png")
print(result.path, result.sha256, result.metadata["usage"])
```

Install the optional authentication dependency with `pip install -e ".[vertex]"`. Supply
Application Default Credentials, set `GOOGLE_APPLICATION_CREDENTIALS`, pass a service-account path,
or inject a short-lived token provider. Never pass a private key as an access token or command-line
argument.

The default is a single 1K `gemini-3.1-flash-lite-image` request at `global`, with a 120-second
timeout, a 10,000-character prompt ceiling, a 20 MB response ceiling, and no retries. The generator
refuses to overwrite existing sibling PNG/JPEG outputs, validates base64 plus image magic and
dimensions before writing, and preserves the service's actual MIME type in the filename. Unknown
model overrides retain token counts but report `estimated_cost_usd=None` rather than applying stale
pricing.

Run the bounded example after configuring Google credentials and a project:

```powershell
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"
python examples/run_vertex_image_generation.py
```

See [`experiments/GOOGLE_VERTEX_IMAGE_GENERATION_SMOKE_2026-08-10.md`](experiments/GOOGLE_VERTEX_IMAGE_GENERATION_SMOKE_2026-08-10.md)
for the live contract corrections, final visual artifact, cost estimate, and scope limits.

## Failure and trust semantics

- A plugin whose `register()` raises is rolled back to the pre-install registry state.
- One failed entry point does not hide other failures in report mode.
- Entry-point loading imports and executes third-party Python code. APR never performs it automatically.
- The registry provides composition and provenance boundaries, not sandboxing. Use only trusted plugin distributions or isolate them at the process/container level.

## Compatibility

The plugin API is introduced during the v0.10 repository-integration phase. Treat it as provisional until v1.0; plugins should declare the APR versions they test against.
