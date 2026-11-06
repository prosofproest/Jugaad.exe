# Run the FastAPI backend for forecasting
# Ensure you have uvicorn installed: pip install uvicorn fastapi
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

