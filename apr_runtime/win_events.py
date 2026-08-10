from __future__ import annotations

import platform
import threading
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional

from .event_ledger import EventLedger, NativeEvent
from .sources import SourceUnavailable

EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_OBJECT_SHOW = 0x8002
EVENT_OBJECT_HIDE = 0x8003
EVENT_OBJECT_FOCUS = 0x8005
OBJID_WINDOW = 0x00000000
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002


@dataclass
class WinEventConfig:
    queue_limit: int = 5000
    foreground_significance: float = 0.75
    focus_significance: float = 0.40
    show_hide_significance: float = 0.45


class Win32NativeEventSource:
    """Optional Windows event source using SetWinEventHook."""

    def __init__(
        self,
        *,
        ledger: Optional[EventLedger] = None,
        config: Optional[WinEventConfig] = None,
    ) -> None:
        if platform.system() != "Windows":
            raise SourceUnavailable("Win32NativeEventSource requires Windows.")
        import ctypes
        from ctypes import wintypes

        self.ctypes, self.wintypes = ctypes, wintypes
        self.user32 = ctypes.windll.user32
        self.ledger = ledger
        self.config = config or WinEventConfig()
        self._queue: Deque[NativeEvent] = deque(maxlen=self.config.queue_limit)
        self._lock = threading.Lock()
        self._hooks = []
        self._callback = None
        self.WINEVENTPROC = ctypes.WINFUNCTYPE(
            None,
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.HWND,
            wintypes.LONG,
            wintypes.LONG,
            wintypes.DWORD,
            wintypes.DWORD,
        )
        self.user32.SetWinEventHook.restype = wintypes.HANDLE
        self.user32.UnhookWinEvent.argtypes = [wintypes.HANDLE]

    def _sig(self, event: int) -> float:
        if event == EVENT_SYSTEM_FOREGROUND:
            return self.config.foreground_significance
        if event == EVENT_OBJECT_FOCUS:
            return self.config.focus_significance
        return self.config.show_hide_significance

    @staticmethod
    def _kind(event: int) -> str:
        return {
            EVENT_SYSTEM_FOREGROUND: "win.foreground",
            EVENT_OBJECT_FOCUS: "win.focus",
            EVENT_OBJECT_SHOW: "win.object_show",
            EVENT_OBJECT_HIDE: "win.object_hide",
        }.get(event, f"win.event.{event}")

    def _emit(self, event: NativeEvent) -> None:
        with self._lock:
            self._queue.append(event)
        if self.ledger is not None:
            self.ledger.append(event)

    def start(self) -> None:
        if self._hooks:
            return

        def callback(hook, event, hwnd, object_id, child_id, event_thread, event_time):
            if event in (EVENT_OBJECT_SHOW, EVENT_OBJECT_HIDE) and object_id != OBJID_WINDOW:
                return
            self._emit(
                NativeEvent(
                    kind=self._kind(int(event)),
                    source="win32_winevent",
                    target=f"window:{int(hwnd)}" if hwnd else "windows.desktop",
                    significance=self._sig(int(event)),
                    hwnd=int(hwnd) if hwnd else None,
                    payload={
                        "event": int(event),
                        "object_id": int(object_id),
                        "child_id": int(child_id),
                        "event_thread": int(event_thread),
                        "event_time_ms": int(event_time),
                    },
                )
            )

        self._callback = self.WINEVENTPROC(callback)
        flags = WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS
        for low, high in [
            (EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND),
            (EVENT_OBJECT_SHOW, EVENT_OBJECT_FOCUS),
        ]:
            hook = self.user32.SetWinEventHook(low, high, 0, self._callback, 0, 0, flags)
            if hook:
                self._hooks.append(hook)
        if not self._hooks:
            raise RuntimeError("SetWinEventHook did not install any hook.")

    def pump(self, *, max_messages: int = 100) -> int:
        msg = self.wintypes.MSG()
        PM_REMOVE = 0x0001
        count = 0
        while count < max_messages and self.user32.PeekMessageW(
            self.ctypes.byref(msg), 0, 0, 0, PM_REMOVE
        ):
            self.user32.TranslateMessage(self.ctypes.byref(msg))
            self.user32.DispatchMessageW(self.ctypes.byref(msg))
            count += 1
        return count

    def drain(self, *, limit: Optional[int] = None) -> List[NativeEvent]:
        with self._lock:
            limit = len(self._queue) if limit is None else int(limit)
            return [self._queue.popleft() for _ in range(min(limit, len(self._queue)))]

    def close(self) -> None:
        for hook in self._hooks:
            try:
                self.user32.UnhookWinEvent(hook)
            except Exception:
                pass
        self._hooks.clear()
        self._callback = None
