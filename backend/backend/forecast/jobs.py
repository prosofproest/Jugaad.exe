# backend/forecast/jobs.py
"""Scheduled forecast job utilities.
Implements a simple daily scheduler that triggers the forecast generation logic.
For production you would replace the dummy `run_forecast_job` with actual model inference.
"""
import datetime
from .router import _latest_forecast


def _dummy_forecast(crop: str, target: str, geo: str, horizon_days: int = 7):
    """Generate a dummy forecast payload.
    Mirrors the logic in ``router.run_forecast`` but usable from a scheduler.
    """
    now = datetime.datetime.utcnow().isoformat() + "Z"
    return {
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


def run_forecast_job(crop: str, target: str, geo: str, horizon_days: int = 7):
    """Execute a forecast run and store it in the in‑memory cache.
    In a real system this would:
    * Load the latest feature snapshot
    * Run the trained model (e.g., ONNX inference)
    * Apply calibration / threshold logic
    * Persist results to the database
    """
    forecast = _dummy_forecast(crop, target, geo, horizon_days)
    key = f"{crop}:{target}:{geo}:{horizon_days}"
    _latest_forecast[key] = forecast
    print(f"[ForecastJob] Ran forecast for {key} at {forecast['issued_at']}")
    return forecast


def schedule_daily_forecast():
    """Run a set of default forecasts – placeholder for a real scheduler.
    This function can be called from a FastAPI startup event.
    """
    default_params = [
        {"crop": "maize", "target": "leaf_spot", "geo": "district_01"},
        {"crop": "wheat", "target": "rust", "geo": "district_02"},
    ]
    for p in default_params:
        run_forecast_job(**p)

