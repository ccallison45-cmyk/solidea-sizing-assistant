"""Pydantic request/response models for the sizing API."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ProductType(StrEnum):
    arm_sleeves = "arm_sleeves"
    leggings = "leggings"
    capris = "capris"
    socks = "socks"
    bras = "bras"


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
