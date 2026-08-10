from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence


@dataclass
class SemanticFact:
    key: str
    value: Any
    confidence: float = 0.8
    volatile: bool = True
    ttl: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticResult:
    summary: str
    facts: List[SemanticFact]
    confidence: float = 0.8
    raw: Optional[Any] = None


class SemanticInspector(Protocol):
    name: str
    estimated_cost: float

    def inspect(
        self,
        image_path: str | Path,
        *,
        prompt: str,
        context: Dict[str, Any],
    ) -> SemanticResult: ...


class CallableSemanticInspector:
    """
    Thin in-process adapter.

    The callable can wrap a local model, SDK client, or cloud API without
    coupling APR core code to a specific provider.
    """

    def __init__(
        self,
        func: Callable[[Path, str, Dict[str, Any]], SemanticResult],
        *,
        name: str = "callable_semantic_inspector",
        estimated_cost: float = 5.0,
    ) -> None:
        self.func = func
        self.name = name
        self.estimated_cost = estimated_cost

    def inspect(
        self,
        image_path: str | Path,
        *,
        prompt: str,
        context: Dict[str, Any],
    ) -> SemanticResult:
        result = self.func(Path(image_path), prompt, context)
        if not isinstance(result, SemanticResult):
            raise TypeError("Callable inspector must return SemanticResult.")
        return result


class CommandSemanticInspector:
    """
    Provider-neutral external-command adapter.

    Each command argument may contain:
      {image}  absolute path to ROI PNG
      {prompt} inspection prompt

    The command must print one JSON object to stdout:

    {
      "summary": "...",
      "confidence": 0.9,
      "facts": [
        {
          "key": "desktop.screen.semantic_change",
          "value": "dialog appeared",
          "confidence": 0.92,
          "volatile": true,
          "ttl": 10
        }
      ]
    }

    This supports local VLM CLIs and cloud wrappers without putting provider
    credentials or fast-changing SDK contracts inside APR core.
    """

    def __init__(
        self,
        command: Sequence[str],
        *,
        name: str = "command_semantic_inspector",
        estimated_cost: float = 8.0,
        timeout: float = 90.0,
    ) -> None:
        if not command:
            raise ValueError("command must not be empty")
        self.command = list(command)
        self.name = name
        self.estimated_cost = estimated_cost
        self.timeout = timeout

    def inspect(
        self,
        image_path: str | Path,
        *,
        prompt: str,
        context: Dict[str, Any],
    ) -> SemanticResult:
        image_path = Path(image_path).resolve()
        args = [part.format(image=str(image_path), prompt=prompt) for part in self.command]
        proc = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"Semantic command failed ({proc.returncode}): {proc.stderr.strip()}"
            )

        payload = json.loads(proc.stdout)
        facts = [
            SemanticFact(
                key=item["key"],
                value=item.get("value"),
                confidence=float(item.get("confidence", payload.get("confidence", 0.8))),
                volatile=bool(item.get("volatile", True)),
                ttl=float(item.get("ttl", 30.0)),
                metadata=dict(item.get("metadata", {})),
            )
            for item in payload.get("facts", [])
        ]
        return SemanticResult(
            summary=str(payload.get("summary", "")),
            facts=facts,
            confidence=float(payload.get("confidence", 0.8)),
            raw=payload,
        )


class RuleSemanticInspector:
    """Deterministic semantic backend for tests and offline demos."""

    def __init__(
        self,
        result_factory: Callable[[Path, str, Dict[str, Any]], SemanticResult],
        *,
        name: str = "rule_semantic_inspector",
        estimated_cost: float = 2.0,
    ) -> None:
        self.result_factory = result_factory
        self.name = name
        self.estimated_cost = estimated_cost

    def inspect(
        self,
        image_path: str | Path,
        *,
        prompt: str,
        context: Dict[str, Any],
    ) -> SemanticResult:
        return self.result_factory(Path(image_path), prompt, context)
