import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    BrowserSnapshot,
    BrowserStreamMonitor,
    EvidenceStore,
    WorldState,
)


class SequenceBrowser:
    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.i = 0

    def snapshot(self):
        value = self.snapshots[min(self.i, len(self.snapshots) - 1)]
        self.i += 1
        return value


def main():
    source = SequenceBrowser(
        [
            BrowserSnapshot(
                url="https://example.test/a",
                title="Page A",
                aria_snapshot='- heading "A"',
                aria_digest="aria-a",
                dom_digest="dom-a",
                dom_element_count=10,
                active_element={"tag": "BODY"},
            ),
            BrowserSnapshot(
                url="https://example.test/b",
                title="Page B",
                aria_snapshot='- heading "B"',
                aria_digest="aria-b",
                dom_digest="dom-b",
                dom_element_count=14,
                active_element={"tag": "INPUT", "name": "q"},
            ),
        ]
    )

    world = WorldState(EvidenceStore())
    monitor = BrowserStreamMonitor(world, source)

    print("tick 0:", monitor.poll_once())
    events = monitor.poll_once()

    print("tick 1:")
    for event in events:
        print(
            " ",
            event.kind,
            f"sig={event.significance:.2f}",
            event.previous,
            "->",
            event.value,
        )

    print("\nNative browser world state:")
    for key, value in world.snapshot().items():
        if key.startswith("browser."):
            print(" ", key, "=>", value)


if __name__ == "__main__":
    main()
