from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .sources import ScreenFrame


@dataclass(frozen=True)
class FrameDelta:
    mean_abs_delta: float
    changed_ratio: float
    sampled_pixels: int
    changed_pixels: int
    bbox: Optional[Tuple[int, int, int, int]]

    @property
    def magnitude(self) -> float:
        # A compact monitor score, deliberately not equivalent to semantic
        # significance.
        return max(
            0.0,
            min(1.0, 0.55 * self.changed_ratio + 0.45 * self.mean_abs_delta),
        )


class FrameDeltaDetector:
    """
    Low-cost sampled BGRA frame differencing.

    This is a Fast Loop signal, not a semantic vision model.
    It intentionally samples pixels using a configurable stride to keep
    monitoring cost bounded.
    """

    def __init__(
        self,
        *,
        stride: int = 12,
        pixel_threshold: float = 0.08,
    ) -> None:
        if stride < 1:
            raise ValueError("stride must be >= 1")
        if not 0 <= pixel_threshold <= 1:
            raise ValueError("pixel_threshold must be in [0, 1]")
        self.stride = stride
        self.pixel_threshold = pixel_threshold

    def compare(self, previous: ScreenFrame, current: ScreenFrame) -> FrameDelta:
        if previous.width != current.width or previous.height != current.height:
            # Geometry change itself is a strong low-level change.
            return FrameDelta(
                mean_abs_delta=1.0,
                changed_ratio=1.0,
                sampled_pixels=1,
                changed_pixels=1,
                bbox=(0, 0, current.width, current.height),
            )

        expected = current.width * current.height * 4
        if len(previous.bgra) < expected or len(current.bgra) < expected:
            raise ValueError("Frame BGRA buffer is smaller than width*height*4.")

        total_delta = 0.0
        sampled = 0
        changed = 0
        min_x = current.width
        min_y = current.height
        max_x = -1
        max_y = -1

        w = current.width
        h = current.height
        a = previous.bgra
        b = current.bgra

        for y in range(0, h, self.stride):
            row = y * w
            for x in range(0, w, self.stride):
                i = (row + x) * 4
                # Ignore alpha. Normalize BGR delta by the maximum 3*255.
                d = (abs(a[i] - b[i]) + abs(a[i + 1] - b[i + 1]) + abs(a[i + 2] - b[i + 2])) / 765.0
                total_delta += d
                sampled += 1

                if d >= self.pixel_threshold:
                    changed += 1
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        mean = 0.0 if sampled == 0 else total_delta / sampled
        ratio = 0.0 if sampled == 0 else changed / sampled

        if changed == 0:
            bbox = None
        else:
            bbox = (
                min_x,
                min_y,
                min(current.width, max_x + self.stride),
                min(current.height, max_y + self.stride),
            )

        return FrameDelta(
            mean_abs_delta=mean,
            changed_ratio=ratio,
            sampled_pixels=sampled,
            changed_pixels=changed,
            bbox=bbox,
        )
