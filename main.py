import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database.database import init_db, engine, get_db
from database.models import User
from services.prediction_service import load_model, get_model
from services.auth_handler import get_optional_current_user
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

    # 2. Load ML Model ONCE into memory at startup
    try:
        load_model()
        logger.info("[ML Model] heart_risk_model.pkl loaded ONCE into memory at startup.")
    except Exception as ml_err:
        logger.error(f"[ML Model] CRITICAL: Failed to load heart_risk_model.pkl: {ml_err}")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)
app.add_middleware(PrivateNetworkAccessMiddleware)

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
def health_check():
    model_loaded = get_model() is not None
    db_connected = False
    try:
        with engine.connect() as conn:
            db_connected = True
    except Exception:
        db_connected = False

    return {
        "status": "healthy" if (model_loaded and db_connected) else "degraded",
        "database_connected": db_connected,
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)