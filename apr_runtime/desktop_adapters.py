from __future__ import annotations

from typing import Optional

from .adapters import BaseAdapter
from .models import Evidence, Modality, PerceptualAction
from .sources import (
    ForegroundWindowSource,
    UIAutomationSource,
)


class DesktopStructuredAdapter(BaseAdapter):
    """
    Real structured desktop adapter.

    Supported fact keys:
      desktop.foreground.title
      desktop.foreground.hwnd
      desktop.foreground.pid
      desktop.uia.digest
      desktop.uia.element_count
    """

    modality = Modality.STRUCTURED

    def __init__(
        self,
        foreground: ForegroundWindowSource,
        uia: Optional[UIAutomationSource] = None,
        *,
        reliability: float = 0.99,
        base_cost: float = 0.5,
    ) -> None:
        self.foreground = foreground
        self.uia = uia
        self.reliability = reliability
        self.base_cost = base_cost

    def configure_world(self, world) -> None:
        for key in (
            "desktop.foreground.title",
            "desktop.foreground.hwnd",
            "desktop.foreground.pid",
            "desktop.uia.digest",
            "desktop.uia.element_count",
        ):
            world.configure_fact(key, ttl=2.0, volatile=True)

    def observe(self, action: PerceptualAction) -> Evidence:
        key = action.target

        if key.startswith("desktop.foreground."):
            snap = self.foreground.snapshot()
            mapping = {
                "desktop.foreground.title": snap.title,
                "desktop.foreground.hwnd": snap.hwnd,
                "desktop.foreground.pid": snap.pid,
            }
            if key not in mapping:
                raise KeyError(f"Unsupported desktop fact: {key}")
            return Evidence(
                claim_key=key,
                observed_value=mapping[key],
                modality=Modality.STRUCTURED,
                source="win32_foreground",
                confidence=self.reliability,
                cost=action.estimated_cost,
                metadata={"hwnd": snap.hwnd, "pid": snap.pid, "title": snap.title},
            )

        if key.startswith("desktop.uia."):
            if self.uia is None:
                raise RuntimeError("UI Automation source is unavailable.")
            snap = self.uia.snapshot()
            mapping = {
                "desktop.uia.digest": snap.digest,
                "desktop.uia.element_count": len(snap.elements),
            }
            if key not in mapping:
                raise KeyError(f"Unsupported UI Automation fact: {key}")
            return Evidence(
                claim_key=key,
                observed_value=mapping[key],
                modality=Modality.STRUCTURED,
                source="windows_uia",
                confidence=max(0.0, self.reliability - 0.02),
                cost=action.estimated_cost,
                metadata={
                    "element_count": len(snap.elements),
                    "sample": [
                        {
                            "name": e.name,
                            "control_type": e.control_type,
                            "automation_id": e.automation_id,
                        }
                        for e in snap.elements[:20]
                    ],
                },
            )

        raise KeyError(f"Unsupported structured desktop fact: {key}")
