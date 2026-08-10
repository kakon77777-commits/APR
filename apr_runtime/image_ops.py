from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path
from typing import Tuple

from .sources import ScreenFrame

BBox = Tuple[int, int, int, int]


def clamp_bbox(bbox: BBox, width: int, height: int) -> BBox:
    left, top, right, bottom = bbox
    left = max(0, min(width, int(left)))
    top = max(0, min(height, int(top)))
    right = max(left, min(width, int(right)))
    bottom = max(top, min(height, int(bottom)))
    return left, top, right, bottom


def pad_bbox(
    bbox: BBox,
    width: int,
    height: int,
    *,
    padding: int = 24,
) -> BBox:
    left, top, right, bottom = bbox
    return clamp_bbox(
        (
            left - padding,
            top - padding,
            right + padding,
            bottom + padding,
        ),
        width,
        height,
    )


def crop_frame(frame: ScreenFrame, bbox: BBox) -> ScreenFrame:
    left, top, right, bottom = clamp_bbox(bbox, frame.width, frame.height)
    crop_w = right - left
    crop_h = bottom - top
    if crop_w <= 0 or crop_h <= 0:
        raise ValueError(f"Empty crop bbox: {bbox}")

    expected = frame.width * frame.height * 4
    if len(frame.bgra) < expected:
        raise ValueError("Frame BGRA buffer is smaller than width*height*4.")

    out = bytearray(crop_w * crop_h * 4)
    src = frame.bgra
    row_bytes = crop_w * 4

    for y in range(crop_h):
        src_start = ((top + y) * frame.width + left) * 4
        dst_start = y * row_bytes
        out[dst_start : dst_start + row_bytes] = src[src_start : src_start + row_bytes]

    return ScreenFrame(
        width=crop_w,
        height=crop_h,
        bgra=bytes(out),
        left=frame.left + left,
        top=frame.top + top,
        timestamp=frame.timestamp,
    )


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    crc = binascii.crc32(body) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + body + struct.pack(">I", crc)


def frame_to_png_bytes(frame: ScreenFrame, *, compression: int = 6) -> bytes:
    """
    Encode BGRA ScreenFrame as RGB PNG using only the Python standard library.

    This keeps the semantic-evidence layer dependency-light and makes archived
    ROI crops portable to any local/cloud vision adapter.
    """
    if not 0 <= compression <= 9:
        raise ValueError("compression must be in [0, 9]")

    expected = frame.width * frame.height * 4
    if len(frame.bgra) < expected:
        raise ValueError("Frame BGRA buffer is smaller than width*height*4.")

    raw = bytearray()
    bgra = frame.bgra
    w = frame.width
    h = frame.height

    for y in range(h):
        raw.append(0)  # PNG filter type 0
        row = y * w * 4
        for x in range(w):
            i = row + x * 4
            b, g, r = bgra[i], bgra[i + 1], bgra[i + 2]
            raw.extend((r, g, b))

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), compression)

    return (
        signature + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")
    )


def save_frame_png(frame: ScreenFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(frame_to_png_bytes(frame))
    return path
