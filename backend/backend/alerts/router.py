# backend/alerts/router.py
"""Alert API router.
Provides simple endpoints to trigger an alert for a forecast and to retrieve alert status.
In a real system this would integrate with SMS/Email/push services.
"""

from fastapi import APIRouter, HTTPException
from ..db import insert_alert, get_latest_alert
from typing import Dict
import datetime

router = APIRouter()

@router.post("/trigger")
async def trigger_alert(crop: str, target: str, geo: str, horizon_days: int = 7, channel: str = "in_app"):
    """Create an alert for a given forecast.
    This stub records the alert in the DB and returns a token.
    """
    now = datetime.datetime.utcnow().isoformat() + "Z"
    alert = {
        "crop": crop,
        "target": target,
        "geo": geo,
        "horizon_days": horizon_days,
        "issued_at": now,
        "channel": channel,
        "status": "sent",
        "reason": "risk_threshold_exceeded",
    }
    insert_alert(alert)
    return {"status": "alert_created", "alert": alert}

@router.get("/latest")
async def get_latest_alert(crop: str, target: str, geo: str, horizon_days: int = 7):
    """Retrieve the most recent alert for the given keys.
    Returns 404 if none.
    """
    alert = get_latest_alert(crop, target, geo, horizon_days)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found for the given keys")
    return alert

