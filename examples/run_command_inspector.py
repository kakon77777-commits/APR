"""
Use any local/cloud VLM wrapper as an external command.

Example environment concept:

    python examples/run_command_inspector.py crop.png

The wrapper command must emit JSON as documented in
docs/SEMANTIC_INSPECTOR_PROTOCOL.md.

This example only demonstrates constructing the adapter.
"""

from apr_runtime import CommandSemanticInspector

inspector = CommandSemanticInspector(
    [
        "python",
        "my_vlm_wrapper.py",
        "--image",
        "{image}",
        "--prompt",
        "{prompt}",
    ],
    name="my_vlm",
    estimated_cost=8.0,
)

print("CommandSemanticInspector configured:", inspector.name)
