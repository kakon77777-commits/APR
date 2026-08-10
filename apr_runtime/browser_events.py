from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional

from .browser import PlaywrightCDPBrowserSource
from .event_ledger import EventLedger, NativeEvent

DOM_EVENTS = (
    "DOM.attributeModified",
    "DOM.attributeRemoved",
    "DOM.characterDataModified",
    "DOM.childNodeCountUpdated",
    "DOM.childNodeInserted",
    "DOM.childNodeRemoved",
    "DOM.documentUpdated",
)
AX_EVENTS = ("Accessibility.nodesUpdated", "Accessibility.loadComplete")


@dataclass
class BrowserEventConfig:
    seed_depth: int = 2
    pierce: bool = True
    queue_limit: int = 5000
    attribute_significance: float = 0.35
    text_significance: float = 0.45
    subtree_significance: float = 0.55
    document_significance: float = 0.90
    accessibility_significance: float = 0.55


class BrowserCDPEventSource:
    """Native CDP DOM/AX events with bounded initial node seeding."""

    def __init__(
        self,
        browser: PlaywrightCDPBrowserSource,
        *,
        ledger: Optional[EventLedger] = None,
        config: Optional[BrowserEventConfig] = None,
    ) -> None:
        self.browser = browser
        self.ledger = ledger
        self.config = config or BrowserEventConfig()
        self._session = None
        self._queue: Deque[NativeEvent] = deque(maxlen=self.config.queue_limit)
        self._lock = threading.Lock()
        self._generation = 0
        self._started = False

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def session(self):
        return self._session

    def _emit(self, event: NativeEvent) -> None:
        with self._lock:
            self._queue.append(event)
        if self.ledger is not None:
            self.ledger.append(event)

    def _target(self, method: str, params: Dict[str, Any]) -> str:
        if method == "DOM.documentUpdated":
            return "browser.document"
        if method.startswith("Accessibility."):
            return "browser.accessibility"
        node = params.get("node") or {}
        node_id = params.get("nodeId") or params.get("parentNodeId") or node.get("nodeId")
        return f"browser.dom.node:{node_id}" if node_id is not None else "browser.dom"

    def _sig(self, method: str) -> float:
        if method == "DOM.documentUpdated":
            return self.config.document_significance
        if method in ("DOM.childNodeInserted", "DOM.childNodeRemoved"):
            return self.config.subtree_significance
        if method == "DOM.characterDataModified":
            return self.config.text_significance
        if method.startswith("DOM.attribute"):
            return self.config.attribute_significance
        if method.startswith("Accessibility."):
            return self.config.accessibility_significance
        return 0.40

    def _handle(self, method: str, params: Optional[Dict[str, Any]]) -> None:
        params = dict(params or {})
        if method == "DOM.documentUpdated":
            self._generation += 1
        node = params.get("node") or {}
        node_id = params.get("nodeId") or params.get("parentNodeId") or node.get("nodeId")
        backend_id = params.get("backendNodeId") or node.get("backendNodeId")
        self._emit(
            NativeEvent(
                kind=method,
                source="browser_cdp",
                target=self._target(method, params),
                significance=self._sig(method),
                node_id=int(node_id) if node_id is not None else None,
                backend_node_id=int(backend_id) if backend_id is not None else None,
                payload={**params, "document_generation": self._generation},
            )
        )

    def start(self) -> None:
        if self._started:
            return
        page = self.browser.page()
        self._session = page.context.new_cdp_session(page)
        self._session.send("DOM.enable")
        self._session.send(
            "DOM.getDocument", depth=self.config.seed_depth, pierce=self.config.pierce
        )
        try:
            self._session.send("Accessibility.enable")
        except Exception:
            pass
        for method in DOM_EVENTS + AX_EVENTS:
            self._session.on(method, lambda params=None, m=method: self._handle(m, params))
        self._started = True

    def reseed_document(self) -> Dict[str, Any]:
        if self._session is None:
            raise RuntimeError("BrowserCDPEventSource is not started.")
        return self._session.send(
            "DOM.getDocument", depth=self.config.seed_depth, pierce=self.config.pierce
        )

    def drain(self, *, limit: Optional[int] = None) -> List[NativeEvent]:
        with self._lock:
            limit = len(self._queue) if limit is None else int(limit)
            return [self._queue.popleft() for _ in range(min(limit, len(self._queue)))]

    def close(self) -> None:
        if self._session is not None:
            try:
                self._session.detach()
            except Exception:
                pass
        self._session = None
        self._started = False
