from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .browser_events import BrowserCDPEventSource
from .event_ledger import NativeEvent


@dataclass
class BrowserSubtreeResult:
    requested_node_id: Optional[int]
    requested_backend_node_id: Optional[int]
    document_generation: int
    dom: Dict[str, Any]
    outer_html: Optional[str]
    accessibility_nodes: List[Dict[str, Any]]
    refreshed_document: bool = False


class TargetedBrowserReader:
    """Read only the DOM/AX subtree implicated by a native CDP event."""

    def __init__(
        self,
        events: BrowserCDPEventSource,
        *,
        depth: int = 2,
        include_outer_html: bool = True,
        fetch_ax_relatives: bool = True,
    ) -> None:
        self.events = events
        self.depth = depth
        self.include_outer_html = include_outer_html
        self.fetch_ax_relatives = fetch_ax_relatives

    def read_event(self, event: NativeEvent) -> BrowserSubtreeResult:
        session = self.events.session
        if session is None:
            raise RuntimeError("CDP event source is not started.")
        event_generation = int(event.payload.get("document_generation", self.events.generation))
        if event.kind == "DOM.documentUpdated" or event_generation != self.events.generation:
            root = self.events.reseed_document()
            return BrowserSubtreeResult(
                None, None, self.events.generation, root.get("root", {}), None, [], True
            )

        node_id, backend_id = event.node_id, event.backend_node_id
        if node_id is None and backend_id is None:
            root = self.events.reseed_document()
            return BrowserSubtreeResult(
                None, None, self.events.generation, root.get("root", {}), None, [], True
            )

        params: Dict[str, Any] = {"depth": self.depth, "pierce": True}
        if node_id is not None:
            params["nodeId"] = node_id
        else:
            params["backendNodeId"] = backend_id

        try:
            dom_node = session.send("DOM.describeNode", **params).get("node", {})
        except Exception:
            root = self.events.reseed_document()
            return BrowserSubtreeResult(
                node_id,
                backend_id,
                self.events.generation,
                root.get("root", {}),
                None,
                [],
                True,
            )

        html = None
        if self.include_outer_html:
            html_params = (
                {"nodeId": node_id} if node_id is not None else {"backendNodeId": backend_id}
            )
            try:
                html = session.send("DOM.getOuterHTML", **html_params).get("outerHTML")
            except Exception:
                html = None

        ax_params = {"fetchRelatives": self.fetch_ax_relatives}
        if node_id is not None:
            ax_params["nodeId"] = node_id
        else:
            ax_params["backendNodeId"] = backend_id
        try:
            ax_nodes = session.send("Accessibility.getPartialAXTree", **ax_params).get("nodes", [])
        except Exception:
            ax_nodes = []

        return BrowserSubtreeResult(
            node_id, backend_id, self.events.generation, dom_node, html, ax_nodes, False
        )
