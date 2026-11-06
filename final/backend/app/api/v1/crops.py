"""Crops API router.
Provides a minimal endpoint to list supported crops.
The crops are stored in the ``Crop`` model; a few sample rows are seeded on startup.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Crop

router = APIRouter()

@router.get("/", summary="List supported crops")
def list_crops(db: Session = Depends(get_db)):
    crops = db.query(Crop).filter(Crop.allowed == True).all()
    return [{"id": c.id, "name": c.name, "allowed": c.allowed} for c in crops]

