"""Non-diagnostic video summary (spec 09 VID-07/VID-08).

The summary reports visibility, quality and tracking consistency. It never
collapses frames into a single diagnosis and never produces a "risk" number.
Reply text is built from fixed templates; the service validates it with
``chat-safety-0.1`` before storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.video.tracker import Track

REASON_TEXT: dict[str, str] = {
    "no_frames": "No frames could be read from the clip.",
    "clip_too_short": "The clip is too short to read.",
    "insufficient_usable_frames": "Too few frames passed the image-quality check.",
    "no_stable_region": "No stable region was tracked across frames.",
    "assessment_abstained": "The assessment engine abstained on every usable frame.",
}

SUMMARY_ABSTAINED_TEXT = (
    "Video summary: {reason} No video-level assessment is shown. Retake a longer, "
    "steadier clip or request expert review."
)
SUMMARY_ASSESSED_TEXT = (
    "Video summary from {engine}: {usable} of {sampled} sampled frames were usable "
    "and {regions} motion region(s) were tracked. This is not a diagnosis; the "
    "candidates are unverified and require expert review."
)
SUMMARY_DEMO_TEXT = (
    "Video summary from {engine} (demo-only, detector {detector}, tracker {tracker}): "
    "{usable} of {sampled} sampled frames were usable and {regions} motion region(s) "
    "were tracked. The label set is not approved for release; this is not a diagnosis."
)
SUMMARY_UNSAFE_TEXT = (
    "The video summary was withheld because it did not pass the content-safety check. "
    "Request expert review."
)
SUMMARY_FAILED_TEXT = (
    "Video summary unavailable: {reason} No assessment is shown. Retry or request expert review."
)

FAILED_REASON_TEXT: dict[str, str] = {
    "video_decode_failed": "The clip could not be decoded.",
    "video_not_found": "The clip is no longer available.",
    "model_not_configured": "The assessment model is not configured.",
    "model_unavailable": "The assessment model is temporarily unavailable.",
    "model_timeout": "The assessment model timed out.",
    "invalid_model_response": "The assessment model returned an invalid response.",
    "unsafe_content_blocked": "The summary did not pass the content-safety check.",
}


def failed_reason_text(code: str) -> str:
    return FAILED_REASON_TEXT.get(code, "The clip could not be read.")


@dataclass(frozen=True)
class VideoSummary:
    state: str
    reason_code: str | None
    error_code: str | None
    summary_text: str
    sampled_frames: int
    usable_frames: int
    duration_ms: int
    quality: dict[str, int]
    tracks: list[dict]
    candidates_observed: list[dict]
    frame_assessments: list[dict] = field(default_factory=list)


def _stable_tracks(tracks: list[Track], interval_ms: int) -> list[dict]:
    stable: list[dict] = []
    for track in tracks:
        if track.hits < 2:
            continue
        span = track.last_frame - track.first_frame + 1
        boxes = list(track.boxes.values())
        areas = [(width * height) for _, _, width, height in boxes if width > 0 and height > 0]
        stable.append(
            {
                "track_id": track.track_id,
                "frames": track.hits,
                "duration_ms": span * interval_ms,
                "mean_area_fraction": round(sum(areas) / len(areas), 4) if areas else 0.0,
            }
        )
    stable.sort(key=lambda item: item["frames"], reverse=True)
    return stable


def _observed_candidates(frame_assessments: list[dict]) -> list[dict]:
    counts: dict[str, dict] = {}
    for frame in frame_assessments:
        assessment = frame.get("assessment") or {}
        for candidate in assessment.get("candidates") or []:
            label = candidate.get("label")
            if not isinstance(label, str):
                continue
            entry = counts.setdefault(
                label,
                {
                    "label": label,
                    "display_name": candidate.get("display_name", label),
                    "frames": 0,
                },
            )
            entry["frames"] += 1
    return sorted(counts.values(), key=lambda item: item["frames"], reverse=True)


def build_summary(
    *,
    sampled_frames: int,
    quality_counts: dict[str, int],
    duration_ms: int,
    frame_assessments: list[dict],
    tracks: list[Track],
    interval_ms: int,
    engine_version: str,
    detector_version: str,
    tracker_version: str,
    is_demo: bool,
    min_usable_frames: int,
    min_duration_ms: int,
) -> VideoSummary:
    usable = quality_counts.get("pass", 0)
    stable = _stable_tracks(tracks, interval_ms)
    candidates = _observed_candidates(frame_assessments)

    def abstained(reason: str) -> VideoSummary:
        return VideoSummary(
            state="abstained",
            reason_code=reason,
            error_code=None,
            summary_text=SUMMARY_ABSTAINED_TEXT.format(reason=REASON_TEXT[reason]),
            sampled_frames=sampled_frames,
            usable_frames=usable,
            duration_ms=duration_ms,
            quality=quality_counts,
            tracks=stable,
            candidates_observed=[],
            frame_assessments=frame_assessments,
        )

    if sampled_frames == 0:
        return abstained("no_frames")
    if duration_ms < min_duration_ms:
        return abstained("clip_too_short")
    if usable < min_usable_frames:
        return abstained("insufficient_usable_frames")
    if not stable:
        return abstained("no_stable_region")

    assessed = [
        frame
        for frame in frame_assessments
        if (frame.get("assessment") or {}).get("state") == "assessed"
    ]
    if not assessed:
        return abstained("assessment_abstained")

    template = SUMMARY_DEMO_TEXT if is_demo else SUMMARY_ASSESSED_TEXT
    text = template.format(
        engine=engine_version,
        detector=detector_version,
        tracker=tracker_version,
        usable=usable,
        sampled=sampled_frames,
        regions=len(stable),
    )
    return VideoSummary(
        state="assessed",
        reason_code=None,
        error_code=None,
        summary_text=text,
        sampled_frames=sampled_frames,
        usable_frames=usable,
        duration_ms=duration_ms,
        quality=quality_counts,
        tracks=stable,
        candidates_observed=candidates,
        frame_assessments=frame_assessments,
    )
