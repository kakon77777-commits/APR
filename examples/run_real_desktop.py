"""
APR Runtime v0.2 — real Windows desktop fast-loop demo.

Install:
    pip install -e ".[desktop]"

Run on Windows:
    python examples/run_real_desktop.py

This demo does NOT send screenshots to a VLM. It performs:
- foreground-window polling;
- bounded UI Automation snapshots;
- sampled frame differencing;
- compact event emission;
- volatile WorldState updates.

High-significance events are printed as escalation candidates for a future
VLM / semantic-inspection adapter.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    EvidenceStore,
    FrameDeltaDetector,
    MSSScreenSource,
    PywinautoUIAutomationSource,
    RealStreamConfig,
    RealStreamMonitor,
    SourceUnavailable,
    Win32ForegroundWindowSource,
    WorldState,
)


def main():
    store = EvidenceStore()
    world = WorldState(store)

    try:
        screen = MSSScreenSource(monitor=1)
        foreground = Win32ForegroundWindowSource()
        uia = PywinautoUIAutomationSource(
            foreground_only=True,
            max_elements=120,
        )
    except SourceUnavailable as exc:
        print("Desktop source unavailable:", exc)
        return 2

    monitor = RealStreamMonitor(
        world,
        screen_source=screen,
        foreground_source=foreground,
        uia_source=uia,
        delta_detector=FrameDeltaDetector(
            stride=14,
            pixel_threshold=0.10,
        ),
        config=RealStreamConfig(
            screen_change_threshold=0.025,
            screen_goal_relevance=0.35,
        ),
    )

    print("APR v0.2 desktop stream running. Ctrl+C to stop.")
    print("No screenshot is sent to any external model.")

    try:
        while True:
            events = monitor.poll_once()

            for event in events:
                print(
                    f"[{event.kind:18s}] "
                    f"sig={event.significance:.3f} "
                    f"mode={event.suggested_mode().value:7s} "
                    f"target={event.target}"
                )
                if event.kind == "foreground_changed":
                    print("  ", event.previous, "->", event.value)
                elif event.kind == "screen_change":
                    print("  ", event.metadata)

            escalations = monitor.escalation_candidates(events, threshold=0.45)
            for event in escalations:
                print(
                    "  APR escalation candidate:",
                    event.target,
                    "->",
                    event.suggested_mode().value,
                )

            time.sleep(0.35)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        close = getattr(screen, "close", None)
        if callable(close):
            close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
