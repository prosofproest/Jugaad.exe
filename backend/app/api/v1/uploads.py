"""Image upload and preview routes for conversational capture.

The upload endpoint is the only place raw bytes enter the system. It enforces a
declared type allow-list, a size ceiling, a real decode and the demo quality
gate before writing anything. Uploads and previews are owner-scoped to the
authenticated caller; there is no public URL and no directory listing.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.session import get_session
from app.modules.conversations import service
from app.modules.conversations.media import MediaValidationError, resolve_stored_path
from app.modules.conversations.models import UploadDescriptor
from app.modules.identity.dependencies import get_current_context
from app.modules.identity.service import AuthContext

router = APIRouter(prefix="/uploads", tags=["conversations"])


@router.post("", response_model=UploadDescriptor, status_code=status.HTTP_201_CREATED)
async def create_upload(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> UploadDescriptor:
    settings = get_settings()
    content_type = (file.content_type or "").split(";")[0].strip().lower()

    data = await file.read(settings.max_upload_bytes + 1)
    if not data:
        raise ApiError(
            code="empty_upload",
            title="The uploaded file is empty",
            status=422,
        )
    if len(data) > settings.max_upload_bytes:
        raise ApiError(
            code="file_too_large",
            title="The uploaded file is too large",
            status=413,
            detail=f"Maximum size is {settings.max_upload_bytes} bytes.",
        )

    try:
        descriptor = service.create_upload(
            session,
            settings=settings,
            owner_id=context.user.user_id,
            filename=file.filename or "upload",
            content_type=content_type,
            data=data,
        )
    except MediaValidationError as error:
        raise ApiError(
            code=error.code,
            title=error.message,
            status=error.status,
        ) from error

    return descriptor


@router.get("/{upload_id}")
def get_upload(
    upload_id: str,
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> FileResponse:
    settings = get_settings()
    try:
        row = service.get_upload_row(session, upload_id, context.user.user_id)
    except service.UploadNotFoundError as error:
        raise ApiError(
            code="upload_not_found",
            title="Upload not found",
            status=404,
        ) from error

    try:
        path = resolve_stored_path(settings, row.storage_path)
    except MediaValidationError as error:
        raise ApiError(
            code="upload_not_found",
            title="Upload not found",
            status=404,
        ) from error

    if not path.is_file():
        raise ApiError(
            code="upload_not_found",
            title="Upload not found",
            status=404,
        )

    return FileResponse(
        path,
        media_type=row.content_type,
        filename=row.filename,
        headers={"Cache-Control": "private, max-age=300"},
    )
