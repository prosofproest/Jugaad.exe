"""Tracker seam and a dependency-light ByteTrack-style association (VID-05).

This is **not** the official ByteTrack implementation and must not be described
as one. It reproduces the property the pipeline needs — two-stage association of
high- then low-confidence detections with stable ids — using IoU and a
constant-velocity prediction instead of a Kalman filter.

A track id is a motion-region id. It is never a pest identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.modules.video.detector import Detection

BYTETRACK_LITE_VERSION = "bytetrack-lite-0.1"

Box = tuple[float, float, float, float]  # x, y, width, height


def iou(left: Box, right: Box) -> float:
    lx, ly, lw, lh = left
    rx, ry, rw, rh = right
    x1 = max(lx, rx)
    y1 = max(ly, ry)
    x2 = min(lx + lw, rx + rw)
    y2 = min(ly + lh, ry + rh)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    intersection = (x2 - x1) * (y2 - y1)
    union = lw * lh + rw * rh - intersection
    return intersection / union if union > 0 else 0.0


@dataclass
class Track:
    track_id: int
    box: Box
    velocity: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    score: float = 0.0
    hits: int = 1
    age: int = 0
    first_frame: int = 0
    last_frame: int = 0
    boxes: dict[int, Box] = field(default_factory=dict)

    def predict(self) -> Box:
        x, y, width, height = self.box
        dx, dy, dw, dh = self.velocity
        return (x + dx, y + dy, max(1.0, width + dw), max(1.0, height + dh))

    def observe(self, detection: Detection, frame_index: int) -> None:
        new_box = (
            float(detection.x),
            float(detection.y),
            float(detection.width),
            float(detection.height),
        )
        old = self.box
        self.velocity = (
            new_box[0] - old[0],
            new_box[1] - old[1],
            new_box[2] - old[2],
            new_box[3] - old[3],
        )
        self.box = new_box
        self.score = detection.score
        self.hits += 1
        self.age = 0
        self.last_frame = frame_index
        self.boxes[frame_index] = new_box


class Tracker(Protocol):
    version: str

    def update(
        self, detections: list[Detection], frame_index: int
    ) -> list[tuple[int, Detection]]: ...


class ByteTrackLiteTracker:
    """High-then-low IoU association with constant-velocity prediction."""

    version = BYTETRACK_LITE_VERSION

    def __init__(
        self,
        *,
        iou_threshold: float = 0.3,
        max_age: int = 5,
        high_score: float = 0.5,
        low_score: float = 0.1,
    ) -> None:
        self._iou_threshold = iou_threshold
        self._max_age = max_age
        self._high_score = high_score
        self._low_score = low_score
        self._tracks: dict[int, Track] = {}
        self._next_id = 1

    @property
    def tracks(self) -> list[Track]:
        return list(self._tracks.values())

    def _match(
        self, tracks: list[Track], detections: list[Detection], frame_index: int
    ) -> tuple[list[tuple[Track, Detection]], list[Track], list[Detection]]:
        candidates: list[tuple[float, int, int]] = []
        for track_index, track in enumerate(tracks):
            predicted = track.predict()
            for detection_index, detection in enumerate(detections):
                box = (
                    float(detection.x),
                    float(detection.y),
                    float(detection.width),
                    float(detection.height),
                )
                overlap = iou(predicted, box)
                if overlap >= self._iou_threshold:
                    candidates.append((overlap, track_index, detection_index))

        candidates.sort(reverse=True)
        used_tracks: set[int] = set()
        used_detections: set[int] = set()
        matches: list[tuple[Track, Detection]] = []
        for _, track_index, detection_index in candidates:
            if track_index in used_tracks or detection_index in used_detections:
                continue
            used_tracks.add(track_index)
            used_detections.add(detection_index)
            matches.append((tracks[track_index], detections[detection_index]))

        unmatched_tracks = [
            track for index, track in enumerate(tracks) if index not in used_tracks
        ]
        unmatched_detections = [
            detection
            for index, detection in enumerate(detections)
            if index not in used_detections
        ]
        return matches, unmatched_tracks, unmatched_detections

    def update(
        self, detections: list[Detection], frame_index: int
    ) -> list[tuple[int, Detection]]:
        high = [item for item in detections if item.score >= self._high_score]
        low = [
            item
            for item in detections
            if self._low_score <= item.score < self._high_score
        ]

        active = list(self._tracks.values())
        matches, unmatched_tracks, _ = self._match(active, high, frame_index)

        if unmatched_tracks and low:
            second, unmatched_tracks, _ = self._match(unmatched_tracks, low, frame_index)
            matches.extend(second)

        matched_ids: set[int] = set()
        for track, detection in matches:
            track.observe(detection, frame_index)
            matched_ids.add(track.track_id)

        for track in self._tracks.values():
            if track.track_id in matched_ids:
                continue
            track.age += 1
            x, y, width, height = track.predict()
            track.box = (x, y, width, height)

        for track_id in [
            track_id
            for track_id, track in self._tracks.items()
            if track.age > self._max_age
        ]:
            del self._tracks[track_id]

        matched_high = {
            id(detection)
            for _, detection in matches
            if detection.score >= self._high_score
        }
        for detection in high:
            if id(detection) in matched_high:
                continue
            track = Track(
                track_id=self._next_id,
                box=(
                    float(detection.x),
                    float(detection.y),
                    float(detection.width),
                    float(detection.height),
                ),
                score=detection.score,
                first_frame=frame_index,
                last_frame=frame_index,
                boxes={
                    frame_index: (
                        float(detection.x),
                        float(detection.y),
                        float(detection.width),
                        float(detection.height),
                    )
                },
            )
            self._tracks[track.track_id] = track
            self._next_id += 1
            matches.append((track, detection))

        return [(track.track_id, detection) for track, detection in matches]
