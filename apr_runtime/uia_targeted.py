from __future__ import annotations

import platform
from dataclasses import dataclass
from typing import List

from .sources import SourceUnavailable, UIElementRecord


@dataclass
class UIASubtreeResult:
    hwnd: int
    root: UIElementRecord
    descendants: List[UIElementRecord]


class PywinautoTargetedUIAReader:
    """Read a bounded UI Automation subtree for one HWND."""

    def __init__(self, *, max_elements: int = 200) -> None:
        if platform.system() != "Windows":
            raise SourceUnavailable("PywinautoTargetedUIAReader requires Windows.")
        try:
            from pywinauto import Desktop
        except Exception as exc:
            raise SourceUnavailable("pywinauto is not installed. Install desktop extras.") from exc
        self.Desktop = Desktop
        self.max_elements = max_elements

    @staticmethod
    def _record(wrapper) -> UIElementRecord:
        info = wrapper.element_info
        rect = getattr(info, "rectangle", None)
        rectangle = None
        if rect is not None:
            try:
                rectangle = [
                    int(rect.left),
                    int(rect.top),
                    int(rect.right),
                    int(rect.bottom),
                ]
            except Exception:
                rectangle = None
        try:
            name = wrapper.window_text()
        except Exception:
            name = getattr(info, "name", "") or ""
        return UIElementRecord(
            name=name,
            control_type=getattr(info, "control_type", "") or "",
            automation_id=getattr(info, "automation_id", "") or "",
            class_name=getattr(info, "class_name", "") or "",
            rectangle=rectangle,
        )

    def read_hwnd(self, hwnd: int) -> UIASubtreeResult:
        desktop = self.Desktop(backend="uia")
        wrapper = desktop.window(handle=int(hwnd))
        root = self._record(wrapper)
        descendants = [self._record(child) for child in wrapper.descendants()[: self.max_elements]]
        return UIASubtreeResult(hwnd=int(hwnd), root=root, descendants=descendants)
