"""FastAPI entry point for CropSentinel backend.
It wires core dependencies, database, and API routers.
"""

from fastapi import FastAPI
from starlette.responses import JSONResponse

from backend.app.database import engine, Base
from backend.app.api.v1 import health, ready, crops, media

# Create tables (for demo; in production use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CropSentinel Backend", version="0.1.0")

# Register routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(ready.router, prefix="/ready", tags=["ready"])
app.include_router(crops.router, prefix="/v1/crops", tags=["crops"])
app.include_router(media.router, prefix="/v1/media", tags=["media"])

@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({"message": "CropSentinel API"})

