"""Observation API router.
Provides endpoints to create and retrieve observations.
Idempotency is enforced via the ``client_report_id`` field.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Observation, User
from backend.app.permissions import get_current_user, require_roles, Role

router = APIRouter()

@router.post("/", summary="Create observation (idempotent)")
def create_observation(
    *,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    crop: str,
    location: str,
    client_report_id: str,
):
    # Ensure user exists in DB – for stub we assume user ID from token is 1
    # In a real system, you would look up the user by token payload.
    # For now we fake a user lookup or create a dummy user if missing.
    db_user = db.query(User).filter(User.id == int(user.get("id", 1))).first()
    if not db_user:
        # Create minimal user record for demonstration
        db_user = User(id=int(user.get("id", 1)), role=user["role"])
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # Idempotency check
    existing = db.query(Observation).filter(Observation.client_report_id == client_report_id).first()
    if existing:
        return {
            "id": existing.id,
            "status": existing.status,
            "message": "Existing observation returned (idempotent)",
        }

    obs = Observation(
        user_id=db_user.id,
        crop=crop,
        location=location,
        client_report_id=client_report_id,
        status="pending",
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return {"id": obs.id, "status": obs.status, "message": "Observation created"}

@router.get("/{obs_id}", summary="Get observation detail")
def get_observation(
    obs_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")
    # Owner or admin can view
    if obs.user_id != int(user.get("id", -1)) and user["role"] != Role.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this observation")
    return {
        "id": obs.id,
        "crop": obs.crop,
        "location": obs.location,
        "status": obs.status,
        "client_report_id": obs.client_report_id,
    }

