"""
Main — Entry point aplikasi Nanas Grading Backend API.
Jalankan dengan: uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.middleware.error_handler import register_error_handlers
from app.api.v1 import (
    auth_router,
    user_router,
    batch_router,
    kebun_router,
    public_router,
    report_router,
    yolo_router,
)
from app.services.yolo_engine import load_model

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler: jalankan saat startup dan shutdown."""
    # --- STARTUP ---
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"Environment: {settings.APP_ENV}")

    # Load model YOLO satu kali saat startup
    load_model()

    yield  # Aplikasi berjalan

    # --- SHUTDOWN ---
    logger.info("Aplikasi dimatikan.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend API untuk sistem grading buah nanas multi-tier berbasis AI (YOLOv11). "
        "Mendukung klasifikasi Grade A (Ekspor), Grade B (Premium Lokal), "
        "Grade C (Standar), dan Reject dengan traceability blockchain."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static files (foto upload bisa diakses via URL) ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- Error handlers ---
register_error_handlers(app)

# --- Routers ---
API_PREFIX = "/api/v1"
app.include_router(auth_router.router,   prefix=API_PREFIX)
app.include_router(batch_router.router,  prefix=API_PREFIX)
app.include_router(yolo_router.router,   prefix=API_PREFIX)
app.include_router(kebun_router.router,  prefix=API_PREFIX)
app.include_router(report_router.router, prefix=API_PREFIX)
app.include_router(user_router.router,   prefix=API_PREFIX)

# Public traceability TIDAK diberi /api/v1 prefix dan TIDAK butuh login,
# supaya URL-nya persis sama dengan yang di-encode di dalam QR code
# (lihat batch_router._generate_kode_qr -> "/public/trace/{kode_batch}").
app.include_router(public_router.router)


@app.get("/", tags=["Health Check"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok"}
