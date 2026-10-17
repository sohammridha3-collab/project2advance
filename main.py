import os
import time
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

from database.database import init_db, engine, get_db
from database.models import User
from services.auth_handler import get_optional_current_user
from services.prediction_service import (
    load_model, get_model, start_background_model_loading, is_model_ready
)
from schemas.schemas import HeartRiskInput, PredictionResponse

# Import all route modules
from routes import auth, prediction, problems, prescriptions, recommendations, medicines, allergies, users, timeline, briefings

load_dotenv()

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("health_risk_system")

BASE_DIR = Path(__file__).resolve().parent

# Ensure upload directory exists
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIRECTORY", str(BASE_DIR / "uploads" / "prescriptions")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# LIFESPAN: Load ML Model & Initialize DB ONCE at application startup
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==================================================")
    logger.info(" Starting AI-Based Health Risk Prediction Backend")
    logger.info("==================================================")
    
    # 1. Initialize Database tables & seed initial reference safety records
    try:
        init_db()
        logger.info("[Database] Database initialized and verified successfully.")
    except Exception as db_err:
        logger.error(f"[Database] Database initialization error: {db_err}")

    # 2. Start ML Model background loading so server opens port 8000 instantly
    try:
        start_background_model_loading()
        logger.info("[ML Model] Model background initialization started. Port 8000 ready immediately.")
    except Exception as ml_err:
        logger.error(f"[ML Model] CRITICAL: Failed to start model loading: {ml_err}")

    yield

    logger.info("Shutting down AI-Based Health Risk Prediction Backend.")

# ============================================================
# FASTAPI APPLICATION DEFINITION
# ============================================================
app = FastAPI(
    title="HealthBridge AI",
    description="Personal Health Continuity Platform connecting health assessments, symptom records, prescription documents, allergies, and clinical visit briefings.",
    version="2.0.0",
    lifespan=lifespan
)

# ============================================================
# CORS CONFIGURATION
# ============================================================
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "null",
]

env_origins = os.getenv("ALLOWED_ORIGINS", "")
if env_origins:
    env_list = [orig.strip() for orig in env_origins.split(",") if orig.strip()]
    allowed_origins = list(set(default_origins + env_list))
else:
    allowed_origins = default_origins

logger.info(f"[CORS] Allowed origins: {allowed_origins}")

from starlette.middleware.base import BaseHTTPMiddleware

class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.headers.get("access-control-request-private-network") == "true" or request.headers.get("origin") == "null":
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        if request.headers.get("origin") == "null":
            response.headers["Access-Control-Allow-Origin"] = "*"
            if "access-control-allow-credentials" in response.headers:
                del response.headers["access-control-allow-credentials"]
        return response

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.add_middleware(PrivateNetworkAccessMiddleware)

# 2. Global Request Timing & Structured Logging Middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    client_host = request.client.host if request.client else "unknown"
    clean_path = request.url.path
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        # Log non-static requests (avoid cluttering logs with polling /health or static assets)
        if not clean_path.startswith("/health") and not clean_path.endswith((".css", ".js", ".png", ".jpg", ".svg", ".ico")):
            logger.info(f"{request.method} {clean_path} [{response.status_code}] ({duration_ms}ms) - {client_host}")
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"[Server Error] {request.method} {clean_path} failed after {duration_ms}ms: {exc}", exc_info=True)
        raise exc

# 3. Global Exception Handler: Ensures unhandled errors return JSON with CORS headers
# (Starlette's default ServerErrorMiddleware returns raw 500 without CORS, causing browser to report Network Error)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    clean_path = request.url.path
    logger.error(
        f"[Unhandled Exception] {request.method} {clean_path}: {type(exc).__name__}: {exc}",
        exc_info=True
    )
    origin = request.headers.get("origin")
    cors_headers = {
        "Access-Control-Allow-Origin": origin if origin else "*",
        "Access-Control-Allow-Credentials": "true" if origin else "false",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. The backend engineering team has logged this issue.",
            "status": "error"
        },
        headers=cors_headers
    )

# ============================================================
# MOUNT ROUTERS (Support both direct and /api prefixed routes)
# ============================================================
app.include_router(auth.router)
app.include_router(auth.router, prefix="/api")

app.include_router(prediction.router)
app.include_router(prediction.router, prefix="/api")

app.include_router(problems.router)
app.include_router(problems.router, prefix="/api")

app.include_router(prescriptions.router)
app.include_router(prescriptions.router, prefix="/api")

app.include_router(recommendations.router)
app.include_router(recommendations.router, prefix="/api")

app.include_router(medicines.router)
app.include_router(medicines.router, prefix="/api")

app.include_router(allergies.router)
app.include_router(allergies.router, prefix="/api")

app.include_router(users.router)
app.include_router(users.router, prefix="/api")

app.include_router(timeline.router)
app.include_router(timeline.router, prefix="/api")

app.include_router(briefings.router)
app.include_router(briefings.router, prefix="/api")

# ============================================================
# SYSTEM HEALTH & ROOT ENDPOINTS
# ============================================================
@app.get("/api/status", tags=["system"])
def api_status():
    return {
        "status": "success",
        "system": "AI-Based Health Risk Prediction System",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["system"])
@app.get("/api/health", tags=["system"], include_in_schema=False)
def health_check():
    """
    Lightweight, fast liveness probe confirming FastAPI is responsive.
    """
    model_loaded = is_model_ready()
    db_connected = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception as db_err:
        logger.warning(f"[Health] Database probe warning: {db_err}")
        db_connected = False

    return {
        "status": "healthy" if (model_loaded and db_connected) else ("loading" if db_connected else "degraded"),
        "database_connected": db_connected,
        "model_loaded": model_loaded,
        "server": "online",
        "version": "2.0.0"
    }

@app.get("/health/ready", tags=["system"])
@app.get("/api/health/ready", tags=["system"], include_in_schema=False)
def readiness_check(response: Response):
    """
    Deep readiness check verifying critical system dependencies (Database & ML Model).
    Returns 503 if database connection fails, ensuring proper system monitoring.
    """
    model_loaded = is_model_ready()
    db_connected = False
    error_msg = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception as exc:
        db_connected = False
        error_msg = str(exc)
        logger.error(f"[Readiness] Database connectivity failure: {exc}")

    if not db_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "database_connected": False,
            "model_loaded": model_loaded,
            "error": "Database unavailable"
        }

    return {
        "status": "ready" if model_loaded else "standby",
        "database_connected": True,
        "model_loaded": model_loaded
    }

# Direct /predict endpoint so frontend script.js (calling http://127.0.0.1:8000/predict) operates seamlessly
@app.post("/predict", response_model=PredictionResponse, tags=["prediction"])
@app.post("/api/predict", response_model=PredictionResponse, tags=["prediction"], include_in_schema=False)
def predict_root(
    data: HeartRiskInput,
    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user)
):
    """Direct root-level predict endpoint for seamless compatibility with frontend form."""
    return prediction.run_prediction(data=data, db=db, optional_user=optional_user)

# ============================================================
# FRONTEND DIRECT SERVING (Serve index.html and app files at root)
# ============================================================
from fastapi.responses import FileResponse

@app.get("/", include_in_schema=False)
def serve_index():
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "AI Health Risk Prediction System Backend"}

@app.get("/{page}.html", include_in_schema=False)
def serve_html_page(page: str):
    target = BASE_DIR / f"{page}.html"
    if target.exists() and target.is_file():
        return FileResponse(target)
    raise HTTPException(status_code=404, detail="Page not found")

@app.get("/{page}", include_in_schema=False)
def serve_clean_page(page: str):
    target = BASE_DIR / f"{page}.html"
    if target.exists() and target.is_file():
        return FileResponse(target)
    raise HTTPException(status_code=404, detail="Page not found")

@app.get("/{script}.js", include_in_schema=False)
def serve_js_script(script: str):
    target = BASE_DIR / f"{script}.js"
    if target.exists() and target.is_file():
        return FileResponse(target, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Script not found")

@app.get("/style.css", include_in_schema=False)
def serve_stylesheet():
    target = BASE_DIR / "style.css"
    if target.exists():
        return FileResponse(target, media_type="text/css")
    raise HTTPException(status_code=404, detail="Stylesheet not found")

# Brand assets (logo, favicon)
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Mount workspace directory for serving static frontend files directly if desired
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    # In production and stable local execution, reload=False prevents database/log writes from triggering restarts
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)