import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    EvidenceStore,
    ForegroundWindowSnapshot,
    RealStreamMonitor,
    ScreenFrame,
    UIAutomationSnapshot,
    UIElementRecord,
    WorldState,
)


def solid_frame(width, height, b, g, r):
    px = bytes([b, g, r, 255])
    return ScreenFrame(width=width, height=height, bgra=px * (width * height))


class SequenceScreen:
    def __init__(self, frames):
        self.frames = list(frames)
        self.i = 0

    def capture(self):
        value = self.frames[min(self.i, len(self.frames) - 1)]
        self.i += 1
        return value


class SequenceForeground:
    def __init__(self, values):
        self.values = list(values)
        self.i = 0

    def snapshot(self):
        value = self.values[min(self.i, len(self.values) - 1)]
        self.i += 1
        return value


class SequenceUIA:
    def __init__(self, values):
        self.values = list(values)
        self.i = 0

    def snapshot(self):
        value = self.values[min(self.i, len(self.values) - 1)]
        self.i += 1
        return value


def main():
    width, height = 48, 32
    black = solid_frame(width, height, 0, 0, 0)

    changed = bytearray(black.bgra)
    # Change a large central region to white.
    for y in range(8, 24):
        for x in range(12, 36):
            i = (y * width + x) * 4
            changed[i : i + 4] = bytes([255, 255, 255, 255])
    white_box = ScreenFrame(width, height, bytes(changed))

    screen = SequenceScreen([black, black, white_box])
    foreground = SequenceForeground(
        [
            ForegroundWindowSnapshot(100, "Editor", 10),
            ForegroundWindowSnapshot(100, "Editor", 10),
            ForegroundWindowSnapshot(200, "Browser", 20),
        ]
    )
    uia = SequenceUIA(
        [
            UIAutomationSnapshot([UIElementRecord("Editor", "Window")]),
            UIAutomationSnapshot([UIElementRecord("Editor", "Window")]),
            UIAutomationSnapshot(
                [
                    UIElementRecord("Browser", "Window"),
                    UIElementRecord("Search", "Edit"),
                ]
            ),
        ]
    )

    store = EvidenceStore()
    world = WorldState(store)
    monitor = RealStreamMonitor(
        world,
        screen_source=screen,
        foreground_source=foreground,
        uia_source=uia,
    )

    for tick in range(3):
        events = monitor.poll_once()
        print(f"\n--- tick {tick} ---")
        if not events:
            print("no significant event")
        for event in events:
            print(
                event.kind,
                f"sig={event.significance:.3f}",
                f"suggested={event.suggested_mode().value}",
                event.metadata,
            )

    print("\nWorld-state snapshot:")
    for key, value in world.snapshot().items():
        print(key, "=>", value)


if __name__ == "__main__":
    main()
