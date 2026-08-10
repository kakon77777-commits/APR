"""
Attach APR Runtime v0.4 to an existing Chromium browser over CDP.

Start Chromium/Chrome/Edge with remote debugging enabled on a profile you
intentionally expose for automation, for example on port 9222.

Install:
    pip install -e ".[browser]"

Run:
    python examples/run_browser_native_state.py

Security note:
A CDP endpoint grants powerful browser automation access. Bind it only to a
trusted local interface and do not expose it to untrusted networks.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    BrowserStreamMonitor,
    EvidenceStore,
    PlaywrightCDPBrowserSource,
    SourceUnavailable,
    WorldState,
)


def main():
    world = WorldState(EvidenceStore())

    try:
        source = PlaywrightCDPBrowserSource(
            "http://127.0.0.1:9222",
            aria_depth=5,
            max_dom_elements=350,
            no_defaults=True,
        )
        monitor = BrowserStreamMonitor(world, source)

        print("APR browser native-state monitor running. Ctrl+C to stop.")
        print("No screenshot or cloud VLM is used.")

        while True:
            for event in monitor.poll_once():
                print(f"[{event.kind:22s}] sig={event.significance:.2f} target={event.target}")
                if event.kind == "browser_navigation":
                    print("  ", event.previous, "->", event.value)
            time.sleep(0.5)

    except SourceUnavailable as exc:
        print("Browser source unavailable:", exc)
        return 2
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        try:
            source.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
