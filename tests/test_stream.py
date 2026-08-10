import sys
import unittest
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


def solid(width, height, value):
    px = bytes([value, value, value, 255])
    return ScreenFrame(width, height, px * (width * height))


class SeqScreen:
    def __init__(self, frames):
        self.frames = frames
        self.i = 0

    def capture(self):
        x = self.frames[min(self.i, len(self.frames) - 1)]
        self.i += 1
        return x


class SeqFG:
    def __init__(self, values):
        self.values = values
        self.i = 0

    def snapshot(self):
        x = self.values[min(self.i, len(self.values) - 1)]
        self.i += 1
        return x


class SeqUIA:
    def __init__(self, values):
        self.values = values
        self.i = 0

    def snapshot(self):
        x = self.values[min(self.i, len(self.values) - 1)]
        self.i += 1
        return x


class RealStreamTests(unittest.TestCase):
    def test_foreground_change_is_event_not_conflict(self):
        store = EvidenceStore()
        world = WorldState(store)
        fg = SeqFG(
            [
                ForegroundWindowSnapshot(1, "A", 10),
                ForegroundWindowSnapshot(2, "B", 20),
            ]
        )
        monitor = RealStreamMonitor(world, foreground_source=fg)

        self.assertEqual(monitor.poll_once(), [])
        events = monitor.poll_once()
        self.assertEqual(events[0].kind, "foreground_changed")
        fact = world.get("desktop.foreground.title")
        self.assertEqual(fact.value, "B")
        self.assertNotEqual(fact.status.value, "contradicted")
        self.assertTrue(fact.volatile)
        self.assertEqual(fact.ttl, 2.0)

    def test_uia_digest_change_emits_event(self):
        store = EvidenceStore()
        world = WorldState(store)
        uia = SeqUIA(
            [
                UIAutomationSnapshot([UIElementRecord("A", "Window")]),
                UIAutomationSnapshot(
                    [
                        UIElementRecord("A", "Window"),
                        UIElementRecord("OK", "Button"),
                    ]
                ),
            ]
        )
        monitor = RealStreamMonitor(world, uia_source=uia)
        monitor.poll_once()
        events = monitor.poll_once()
        self.assertTrue(any(e.kind == "uia_changed" for e in events))
        self.assertEqual(world.get("desktop.uia.element_count").value, 2)

    def test_screen_change_emits_event(self):
        store = EvidenceStore()
        world = WorldState(store)
        screen = SeqScreen(
            [
                solid(16, 16, 0),
                solid(16, 16, 255),
            ]
        )
        monitor = RealStreamMonitor(world, screen_source=screen)
        monitor.poll_once()
        events = monitor.poll_once()
        self.assertTrue(any(e.kind == "screen_change" for e in events))
        self.assertTrue(world.get("desktop.screen.changed").value)


if __name__ == "__main__":
    unittest.main()
