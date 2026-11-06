import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .forecast.router import router as forecast_router
from .forecast.jobs import schedule_daily_forecast
from .db import init_db

app = FastAPI(title="Jugaad Forecast Backend", version="0.1.0")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    schedule_daily_forecast()

# CORS – allow local dev front‑ends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include forecast routes
app.include_router(forecast_router, prefix="/forecast", tags=["forecast"])

# Include farmer vertical slice routes
from .farmer.router import router as farmer_router
app.include_router(farmer_router, prefix="/farmer", tags=["farmer"])

# Root health check
@app.get("/health")
def health_check():
    return {"status": "ok"}
