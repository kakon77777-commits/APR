import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import FrameDeltaDetector, ScreenFrame


def frame(width, height, rgb=(0, 0, 0)):
    r, g, b = rgb
    px = bytes([b, g, r, 255])
    return ScreenFrame(width, height, px * (width * height))


class FrameDeltaTests(unittest.TestCase):
    def test_identical_frames_have_zero_delta(self):
        detector = FrameDeltaDetector(stride=1)
        a = frame(4, 4)
        b = frame(4, 4)
        delta = detector.compare(a, b)
        self.assertEqual(delta.changed_pixels, 0)
        self.assertEqual(delta.changed_ratio, 0.0)
        self.assertIsNone(delta.bbox)

    def test_changed_region_is_detected(self):
        detector = FrameDeltaDetector(stride=1, pixel_threshold=0.05)
        a = frame(4, 4)
        raw = bytearray(a.bgra)
        for y in (1, 2):
            for x in (1, 2):
                i = (y * 4 + x) * 4
                raw[i : i + 4] = bytes([255, 255, 255, 255])
        b = ScreenFrame(4, 4, bytes(raw))
        delta = detector.compare(a, b)
        self.assertEqual(delta.changed_pixels, 4)
        self.assertAlmostEqual(delta.changed_ratio, 0.25)
        self.assertEqual(delta.bbox, (1, 1, 3, 3))

    def test_geometry_change_is_full_change(self):
        detector = FrameDeltaDetector()
        delta = detector.compare(frame(4, 4), frame(5, 4))
        self.assertEqual(delta.changed_ratio, 1.0)


if __name__ == "__main__":
    unittest.main()
