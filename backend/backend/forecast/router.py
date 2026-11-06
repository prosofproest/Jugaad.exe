# backend/forecast/router.py
"""Forecast API router.
Provides endpoints for triggering forecast generation and retrieving latest forecasts.
Persists forecasts to a SQLite DB via ``backend.db`` utilities.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
import datetime

from ..db import insert_forecast, get_latest_forecast

router = APIRouter()

@router.post("/run")
async def run_forecast(crop: str, target: str, geo: str, horizon_days: int = 7):
    """Trigger a forecast run for the given parameters.
    This stub generates dummy data and stores it in the DB.
    """
    now = datetime.datetime.utcnow().isoformat() + "Z"
    forecast = {
        "crop": crop,
        "target": target,
        "geo": geo,
        "horizon_days": horizon_days,
        "issued_at": now,
        "risk_band": "moderate",
        "probability": 0.42,
        "no_score": False,
        "drivers": {"rainfall": 120, "temperature_avg": 28},
    }
    insert_forecast(forecast)
    return {"status": "run", "forecast": forecast}

@router.get("/latest")
async def get_latest(crop: str, target: str, geo: str, horizon_days: int = 7):
    """Retrieve the most recent forecast for the given parameters.
    Returns 404 if not found.
    """
    forecast = get_latest_forecast(crop, target, geo, horizon_days)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found for the given keys")
    return forecast
