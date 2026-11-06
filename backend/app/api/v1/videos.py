"""Video reading routes (spec 09 §7).

A clip is uploaded once, then read on demand. Reading is explicit rather than
implicit so the client controls when the (bounded) decode and model work runs.
Video bytes and previews are owner-scoped; there is no public URL.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.session import get_session
from app.modules.video import service
from app.modules.video.extractor import VideoValidationError
from app.modules.video.models import VideoDescriptor, VideoDetail, VideoReading

router = APIRouter(prefix="/videos", tags=["videos"])

_CHUNK = 1024 * 1024


def _api_error(error: VideoValidationError) -> ApiError:
    return ApiError(code=error.code, title=error.message, status=error.status)


def _not_found() -> ApiError:
    return ApiError(code="video_not_found", title="Video not found", status=404)


async def _read_bounded(file: UploadFile, limit: int) -> bytes:
    """Read at most ``limit + 1`` bytes so an oversized upload fails early."""

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise VideoValidationError(
                "video_too_large",
                f"Maximum video size is {limit} bytes.",
                status=413,
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("", response_model=VideoDescriptor, status_code=status.HTTP_201_CREATED)
async def create_video(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> VideoDescriptor:
    settings = get_settings()
    try:
        data = await _read_bounded(file, settings.video_max_bytes)
        return service.create_video_upload(
            session,
            settings=settings,
            filename=file.filename or "video",
            content_type=file.content_type or "",
            data=data,
        )
    except VideoValidationError as error:
        raise _api_error(error) from error


@router.get("/{video_id}", response_model=VideoDetail)
def get_video(video_id: str, session: Session = Depends(get_session)) -> VideoDetail:
    try:
        return service.get_video(session, video_id)
    except service.VideoNotFoundError as error:
        raise _not_found() from error


@router.get("/{video_id}/preview")
def get_preview(
    video_id: str, session: Session = Depends(get_session)
) -> Response:
    settings = get_settings()
    try:
        data = service.preview_bytes(session, settings, video_id)
    except service.VideoNotFoundError as error:
        raise _not_found() from error
    except VideoValidationError as error:
        raise _api_error(error) from error
    return Response(
        content=data,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store"},
    )


@router.post(
    "/{video_id}/read",
    response_model=VideoReading,
    status_code=status.HTTP_201_CREATED,
)
def read_video(video_id: str, session: Session = Depends(get_session)) -> VideoReading:
    settings = get_settings()
    try:
        return service.read_video(session, settings=settings, video_id=video_id)
    except service.VideoNotFoundError as error:
        raise _not_found() from error
