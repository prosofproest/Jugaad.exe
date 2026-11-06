# Dockerfile for Jugaad Forecast Backend
# Use a lightweight Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install build dependencies (if any) and then runtime dependencies
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Default command runs the app with uvicorn. In production you’ll mount TLS certs and run with --ssl-keyfile/--ssl-certfile.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
