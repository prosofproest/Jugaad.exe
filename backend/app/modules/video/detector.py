"""Detector seam and the demo motion-region detector (spec 09 VID-04).

The real system needs a trained detector behind this protocol. The shipped
implementation is a deterministic frame-difference heuristic that returns
*motion regions*. It is not a pest detector, it does not classify anything, and
it must stay labelled ``demo-motion-0.1`` until a validated model exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import cv2
import numpy as np

DEMO_DETECTOR_VERSION = "demo-motion-0.1"


@dataclass(frozen=True)
class Detection:
    """A region in the downscaled frame's pixel coordinates."""

    x: int
    y: int
    width: int
    height: int
    score: float

    @property
    def area(self) -> int:
        return self.width * self.height


class Detector(Protocol):
    version: str

    def prepare(self, frame_bgr: np.ndarray) -> np.ndarray: ...

    def detect(
        self, frame_bgr: np.ndarray, previous_gray: np.ndarray | None
    ) -> list[Detection]: ...


class MotionRegionDetector:
    """Frame-difference regions, versioned and visibly demo-only."""

    version = DEMO_DETECTOR_VERSION

    def __init__(
        self,
        *,
        threshold: int = 25,
        min_area_fraction: float = 0.005,
        max_regions: int = 10,
        analysis_width: int = 320,
    ) -> None:
        self._threshold = threshold
        self._min_area_fraction = min_area_fraction
        self._max_regions = max_regions
        self._analysis_width = analysis_width

    def prepare(self, frame_bgr: np.ndarray) -> np.ndarray:
        height, width = frame_bgr.shape[:2]
        scale = self._analysis_width / width if width > self._analysis_width else 1.0
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        if size != (width, height):
            gray = cv2.resize(gray, size, interpolation=cv2.INTER_AREA)
        return cv2.GaussianBlur(gray, (5, 5), 0)

    def detect(self, frame_bgr: np.ndarray, previous_gray: np.ndarray | None) -> list[Detection]:
        gray = self.prepare(frame_bgr)
        if previous_gray is None or previous_gray.shape != gray.shape:
            return []

        diff = cv2.absdiff(gray, previous_gray)
        _, mask = cv2.threshold(diff, self._threshold, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        frame_area = float(gray.shape[0] * gray.shape[1])
        minimum = self._min_area_fraction * frame_area

        scale_x = frame_bgr.shape[1] / gray.shape[1]
        scale_y = frame_bgr.shape[0] / gray.shape[0]

        found: list[Detection] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < minimum:
                continue
            x, y, width, height = cv2.boundingRect(contour)
            patch = diff[y : y + height, x : x + width]
            mean_diff = float(patch.mean()) if patch.size else 0.0
            found.append(
                Detection(
                    x=round(x * scale_x),
                    y=round(y * scale_y),
                    width=max(1, round(width * scale_x)),
                    height=max(1, round(height * scale_y)),
                    score=min(1.0, mean_diff / 255.0 * 4.0),
                )
            )

        found.sort(key=lambda item: item.area, reverse=True)
        return found[: self._max_regions]
