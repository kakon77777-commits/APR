# Semantic Inspector Protocol — APR Runtime v0.3

## Purpose

APR core does not depend on a specific VLM vendor.

A semantic inspector receives:

```text
ROI image path
prompt
context
```

and returns:

```text
summary
facts[]
confidence
```

## Python interface

```python
inspect(
    image_path,
    prompt=...,
    context=...
) -> SemanticResult
```

## SemanticFact

```text
key
value
confidence
volatile
ttl
metadata
```

Example:

```json
{
  "summary": "A warning dialog appeared.",
  "confidence": 0.93,
  "facts": [
    {
      "key": "desktop.warning.visible",
      "value": true,
      "confidence": 0.96,
      "volatile": true,
      "ttl": 5,
      "metadata": {
        "kind": "warning_dialog"
      }
    }
  ]
}
```

## External command adapter

`CommandSemanticInspector` accepts a command template containing:

```text
{image}
{prompt}
```

Example:

```python
CommandSemanticInspector([
    "python",
    "my_vlm_wrapper.py",
    "--image", "{image}",
    "--prompt", "{prompt}"
])
```

The wrapper may call:

- a local VLM;
- a local inference server;
- a cloud VLM API;
- an enterprise model gateway.

It only needs to print the JSON object above.

## Why APR uses a provider-neutral adapter

The governance problem is stable:

```text
event -> choose ROI -> inspect -> evidence -> revise state
```

Vendor SDKs and model names are not.

Keeping the SDK wrapper outside core means the APR state/evidence/runtime layer
does not need to change when a provider changes its API.
