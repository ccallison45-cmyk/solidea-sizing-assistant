"""FastAPI application for the Solidea Sizing Assistant."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.conversation.router import init_conversation
from app.conversation.router import router as conversation_router
from app.models import (
    DisproportionResponse,
    FieldSizeMappingResponse,
    SizingRequest,
    SizingResponse,
)
from app.sizing.disproportion import analyze_disproportion
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
    init_conversation(_sizing_data)
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

# Serve prototype pages (dev only)
prototypes_dir = Path(__file__).resolve().parent.parent / "prototypes"
if prototypes_dir.is_dir():
    app.mount(
        "/prototypes", StaticFiles(directory=str(prototypes_dir), html=True), name="prototypes"
    )


# V2 conversation endpoints
app.include_router(conversation_router)


# Serve test conversation page (dev only)
_test_page = Path(__file__).resolve().parent.parent / "test-conversation.html"


@app.get("/test")
async def test_page():
    return FileResponse(str(_test_page), media_type="text/html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/product-fields/{product_type}")
async def product_fields(product_type: str):
    """Return the measurement fields and size list for a product type."""
    key = product_type.replace("-", "_")
    if key not in _sizing_data:
        return {"error": f"Unknown product type: {product_type}"}

    entries = _sizing_data[key]
    sizes = [e["size"] for e in entries]
    fields: dict[str, dict] = {}
    for entry in entries:
        for field_name, range_data in entry["measurements"].items():
            if field_name not in fields:
                fields[field_name] = {
                    "label": field_name.replace("_cm", "")
                    .replace("_kg", "")
                    .replace("_circumference", "")
                    .replace("_", " ")
                    .title(),
                    "unit": "kg" if "_kg" in field_name else "cm",
                    "global_min": range_data["min"],
                    "global_max": range_data["max"],
                }
            else:
                fields[field_name]["global_min"] = min(
                    fields[field_name]["global_min"], range_data["min"]
                )
                fields[field_name]["global_max"] = max(
                    fields[field_name]["global_max"], range_data["max"]
                )

    return {"product_type": key, "sizes": sizes, "fields": fields}


@app.post("/api/v1/size-recommendation", response_model=SizingResponse)
async def size_recommendation(request: SizingRequest):
    result = recommend_size(
        product_type=request.product_type.value,
        measurements=request.measurements,
        sizing_data=_sizing_data,
    )

    # Analyze disproportion if we have at least 2 measurements
    disproportion = None
    if len(request.measurements) >= 2:
        report = analyze_disproportion(
            request.product_type.value,
            request.measurements,
            _sizing_data,
        )
        if report.is_disproportionate:
            disproportion = DisproportionResponse(
                is_disproportionate=True,
                size_spread=report.size_spread,
                field_mappings=[
                    FieldSizeMappingResponse(
                        field=m.field,
                        field_label=m.field.replace("_cm", "")
                        .replace("_kg", "")
                        .replace("_circumference", "")
                        .replace("_", " "),
                        value=m.value,
                        best_size=m.best_size,
                    )
                    for m in report.field_mappings
                ],
                notes=report.notes,
            )

    return SizingResponse(**result, disproportion=disproportion)
