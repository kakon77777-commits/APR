from __future__ import annotations

import json
import platform
import time
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Dict, List, Optional, Protocol


class SourceUnavailable(RuntimeError):
    pass


@dataclass
class ScreenFrame:
    width: int
    height: int
    bgra: bytes
    timestamp: float = field(default_factory=time.time)
    left: int = 0
    top: int = 0


class ScreenSource(Protocol):
    def capture(self) -> ScreenFrame: ...


class MSSScreenSource:
    """
    Real desktop screen source using python-mss.

    The current python-mss API exposes mss.MSS and grab(). We intentionally
    convert ScreenShot.bgra to bytes at the adapter boundary so downstream
    code does not depend on whether MSS returns bytes or a memoryview.
    """

    def __init__(
        self,
        monitor: int = 1,
        region: Optional[Dict[str, int]] = None,
        with_cursor: bool = False,
    ) -> None:
        try:
            from mss import MSS
        except Exception as exc:
            raise SourceUnavailable(
                "python-mss is not installed. Install the desktop extra: "
                "pip install -e '.[desktop]'"
            ) from exc

        self._MSS = MSS
        self.monitor_index = monitor
        self.region = region
        self.with_cursor = with_cursor
        self._sct = None

    def _ensure(self):
        if self._sct is None:
            # MSS constructor supports with_cursor in current releases.
            try:
                self._sct = self._MSS(with_cursor=self.with_cursor)
            except TypeError:
                self._sct = self._MSS()
        return self._sct

    def capture(self) -> ScreenFrame:
        sct = self._ensure()
        if self.region is not None:
            target = self.region
        else:
            monitors = sct.monitors
            if self.monitor_index < 0 or self.monitor_index >= len(monitors):
                raise SourceUnavailable(
                    f"Monitor {self.monitor_index} unavailable; "
                    f"found {max(0, len(monitors) - 1)} physical monitor(s)."
                )
            target = monitors[self.monitor_index]

        shot = sct.grab(target)
        return ScreenFrame(
            width=int(shot.width),
            height=int(shot.height),
            bgra=bytes(shot.bgra),
            left=int(getattr(shot, "left", target.get("left", 0))),
            top=int(getattr(shot, "top", target.get("top", 0))),
        )

    def close(self) -> None:
        if self._sct is not None:
            close = getattr(self._sct, "close", None)
            if callable(close):
                close()
            self._sct = None


@dataclass(frozen=True)
class ForegroundWindowSnapshot:
    hwnd: int
    title: str
    pid: int
    timestamp: float = field(default_factory=time.time)


class ForegroundWindowSource(Protocol):
    def snapshot(self) -> ForegroundWindowSnapshot: ...


class Win32ForegroundWindowSource:
    """Zero-dependency foreground-window source for Windows."""

    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise SourceUnavailable("Win32ForegroundWindowSource requires Windows.")

        import ctypes
        from ctypes import wintypes

        self.ctypes = ctypes
        self.wintypes = wintypes
        self.user32 = ctypes.windll.user32

        self.user32.GetForegroundWindow.restype = wintypes.HWND
        self.user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self.user32.GetWindowTextLengthW.restype = ctypes.c_int
        self.user32.GetWindowTextW.argtypes = [
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int,
        ]
        self.user32.GetWindowTextW.restype = ctypes.c_int
        self.user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]

    def snapshot(self) -> ForegroundWindowSnapshot:
        hwnd = self.user32.GetForegroundWindow()
        if not hwnd:
            return ForegroundWindowSnapshot(hwnd=0, title="", pid=0)

        length = self.user32.GetWindowTextLengthW(hwnd)
        buf = self.ctypes.create_unicode_buffer(max(1, length + 1))
        self.user32.GetWindowTextW(hwnd, buf, len(buf))

        pid = self.wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, self.ctypes.byref(pid))

        return ForegroundWindowSnapshot(
            hwnd=int(hwnd),
            title=buf.value,
            pid=int(pid.value),
        )


@dataclass(frozen=True)
class UIElementRecord:
    name: str
    control_type: str
    automation_id: str = ""
    class_name: str = ""
    rectangle: Optional[List[int]] = None


@dataclass
class UIAutomationSnapshot:
    elements: List[UIElementRecord]
    timestamp: float = field(default_factory=time.time)

    @property
    def digest(self) -> str:
        payload = [
            {
                "name": e.name,
                "control_type": e.control_type,
                "automation_id": e.automation_id,
                "class_name": e.class_name,
                "rectangle": e.rectangle,
            }
            for e in self.elements
        ]
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


class UIAutomationSource(Protocol):
    def snapshot(self) -> UIAutomationSnapshot: ...


class PywinautoUIAutomationSource:
    """
    Real Windows UI Automation snapshot source.

    The snapshot is intentionally bounded. APR should not serialize the full
    desktop accessibility tree every cycle; it reads only a compact working
    sample and uses its digest as a low-cost structured-change signal.
    """

    def __init__(
        self,
        *,
        max_windows: int = 20,
        max_elements: int = 200,
        foreground_only: bool = True,
    ) -> None:
        if platform.system() != "Windows":
            raise SourceUnavailable("UI Automation source requires Windows.")

        try:
            from pywinauto import Desktop
        except Exception as exc:
            raise SourceUnavailable(
                "pywinauto is not installed. Install the desktop extra: pip install -e '.[desktop]'"
            ) from exc

        self.Desktop = Desktop
        self.max_windows = max_windows
        self.max_elements = max_elements
        self.foreground_only = foreground_only

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

        name = ""
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

    def snapshot(self) -> UIAutomationSnapshot:
        desktop = self.Desktop(backend="uia")
        records: List[UIElementRecord] = []

        if self.foreground_only:
            try:
                wrapper = desktop.get_active()
                records.append(self._record(wrapper))
                for child in wrapper.descendants()[: max(0, self.max_elements - 1)]:
                    records.append(self._record(child))
                return UIAutomationSnapshot(elements=records)
            except Exception:
                # Fall through to top-level windows.
                pass

        try:
            windows = desktop.windows(visible_only=True)
        except TypeError:
            windows = desktop.windows()

        for wrapper in windows[: self.max_windows]:
            records.append(self._record(wrapper))
            if len(records) >= self.max_elements:
                break

        return UIAutomationSnapshot(elements=records[: self.max_elements])
