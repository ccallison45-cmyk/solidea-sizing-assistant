"""Pydantic request/response models for the sizing API."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ProductType(StrEnum):
    # Active Massage Compression — Hands & Arm
    arm_sleeves = "arm_sleeves"
    gauntlets = "gauntlets"
    armbands = "armbands"
    # Active Massage Compression — Breast & Trunk
    bras = "bras"
    braless_tops = "braless_tops"
    tops_with_bra = "tops_with_bra"
    abdominal_band = "abdominal_band"
    # Active Massage Compression — Lower Body
    leggings = "leggings"
    capris = "capris"
    shorts = "shorts"
    bike_shorts = "bike_shorts"
    opaque_leggings = "opaque_leggings"
    opaque_capris = "opaque_capris"
    high_waist_legging = "high_waist_legging"
    # Active Massage Compression — Foot + Lower Leg
    socks = "socks"
    calf_sleeves = "calf_sleeves"
    thigh_highs = "thigh_highs"
    # Active Massage Compression — Men's
    mens_briefs = "mens_briefs"
    # Classic Compression
    classic_arm_sleeves = "classic_arm_sleeves"
    classic_armbands = "classic_armbands"


# ── Shared models ────────────────────────────────────────────────


class FieldSizeMappingResponse(BaseModel):
    field: str
    field_label: str
    value: float
    best_size: str


class DisproportionResponse(BaseModel):
    is_disproportionate: bool
    size_spread: int
    field_mappings: list[FieldSizeMappingResponse]
    notes: str


# ── V1 models ────────────────────────────────────────────────────


class SizingRequest(BaseModel):
    product_type: ProductType
    measurements: dict[str, float] = Field(
        ...,
        min_length=1,
        description="Measurement values keyed by field name (e.g. height_cm, weight_kg)",
    )


class SizingResponse(BaseModel):
    recommended_size: str
    confidence: Literal["exact", "interpolated", "out_of_range"]
    notes: str = ""
    disproportion: DisproportionResponse | None = None


# ── V2 conversation models ──────────────────────────────────────


class ConversationStartRequest(BaseModel):
    product_type: ProductType
    channel: str = "widget"
    collect_all: bool = False


class AnswerValue(BaseModel):
    value: str | None = None
    skip: bool = False


class ConversationAnswerRequest(BaseModel):
    session_id: str
    answer: AnswerValue


class ConversationBatchRequest(BaseModel):
    product_type: ProductType
    channel: str = "email"
    measurements: dict[str, float] = Field(
        ...,
        min_length=1,
        description="Pre-parsed measurements in cm/kg.",
    )


class QuestionResponse(BaseModel):
    id: str
    text: str
    help_text: str
    input_type: str
    skip_allowed: bool


class ProgressResponse(BaseModel):
    current: int
    estimated_total: int


class ResultResponse(BaseModel):
    recommended_size: str
    confidence: str
    notes: str
    disproportion: DisproportionResponse | None = None


class ConversationStepResponse(BaseModel):
    session_id: str
    message: str
    question: QuestionResponse | None = None
    progress: ProgressResponse
    result: ResultResponse | None = None
    status: str  # "in_progress" | "complete" | "error"
