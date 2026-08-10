import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    ScreenFrame,
    crop_frame,
    frame_to_png_bytes,
    pad_bbox,
)


def solid(width, height, b=0, g=0, r=0):
    px = bytes([b, g, r, 255])
    return ScreenFrame(width, height, px * (width * height))


class ImageOpsTests(unittest.TestCase):
    def test_crop_frame_geometry(self):
        f = solid(10, 8)
        crop = crop_frame(f, (2, 1, 7, 5))
        self.assertEqual((crop.width, crop.height), (5, 4))
        self.assertEqual(len(crop.bgra), 5 * 4 * 4)

    def test_padding_clamps(self):
        self.assertEqual(
            pad_bbox((2, 2, 4, 4), 5, 5, padding=10),
            (0, 0, 5, 5),
        )

    def test_png_encoder_signature_and_size(self):
        f = solid(7, 5, 10, 20, 30)
        data = frame_to_png_bytes(f)
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        # IHDR begins at byte 8: length(4), type(4), width/height.
        width, height = struct.unpack(">II", data[16:24])
        self.assertEqual((width, height), (7, 5))


if __name__ == "__main__":
    unittest.main()
