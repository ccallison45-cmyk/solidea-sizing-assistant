"""FastAPI application for the Solidea Sizing Assistant."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models import SizingRequest, SizingResponse
from app.sizing.engine import recommend_size
from app.sizing.loader import load_sizing_data

logging.basicConfig(
    level=os.getenv("APP_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Module-level storage for sizing data (loaded at startup)
_sizing_data: dict[str, list[dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load and validate sizing data at startup."""
    global _sizing_data  # noqa: PLW0603
    data_dir = os.getenv("SIZING_DATA_DIR", "data")
    logger.info("Loading sizing data from %s", data_dir)
    _sizing_data = load_sizing_data(data_dir)
    logger.info("Sizing data loaded: %s", list(_sizing_data.keys()))
    yield
    _sizing_data = {}


app = FastAPI(
    title="Solidea Sizing Assistant",
    description="Size recommendation API for Solidea US compression garments",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# Serve widget static files
widget_dir = Path(__file__).resolve().parent.parent / "widget"
if widget_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(widget_dir)), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/size-recommendation", response_model=SizingResponse)
async def size_recommendation(request: SizingRequest):
    result = recommend_size(
        product_type=request.product_type.value,
        measurements=request.measurements,
        sizing_data=_sizing_data,
    )
    return SizingResponse(**result)
