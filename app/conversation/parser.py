"""Parse user-entered measurements with flexible unit support.

Handles feet/inches, lbs, cm, kg, and bare numbers.  Ported from
the n8n workflow JavaScript logic in n8n/test-workflow-logic.js.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ── constants ────────────────────────────────────────────────────
_INCHES_PER_FOOT = 12
_CM_PER_INCH = 2.54
_KG_PER_LB = 1 / 2.2046

_NUMBER_WORDS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}

# ── helpers ──────────────────────────────────────────────────────


def _parse_number(s: str) -> float | None:
    """Parse a numeric string or number word, returning None on failure."""
    key = s.strip().lower()
    if key in _NUMBER_WORDS:
        return float(_NUMBER_WORDS[key])
    try:
        return float(key)
    except ValueError:
        return None


def feet_inches_to_cm(feet: float, inches: float = 0) -> float:
    total_inches = (feet * _INCHES_PER_FOOT) + inches
    return round(total_inches * _CM_PER_INCH, 2)


def inches_to_cm(value: float) -> float:
    return round(value * _CM_PER_INCH, 2)


def lbs_to_kg(value: float) -> float:
    return round(value * _KG_PER_LB, 2)


# ── regex patterns ───────────────────────────────────────────────

# Feet-inches patterns: 5'7", 5 foot 10, 5ft 7in, etc.
_FEET_INCHES_PATTERNS = [
    re.compile(r"(\d+)\s*['\u2018\u2019]\s*(\d+)?\s*[\"\u201c\u201d]?"),
    re.compile(r"(\d+)\s*(?:feet|foot|ft)\.?\s*(\d+)?\s*(?:inches?|in)?", re.I),
    re.compile(r"(\w+)\s+foot\s+(\w+)", re.I),
]

# Height with explicit unit
_HEIGHT_CM_PATTERNS = [
    re.compile(r"(?:height\s*(?:is|:|=)?\s*)([\d.]+)\s*cm", re.I),
    re.compile(r"([\d.]+)\s*cm\s*(?:tall|height)", re.I),
    re.compile(r"i(?:'m|\s+am)\s+([\d.]+)\s*cm", re.I),
]

_HEIGHT_IN_PATTERNS = [
    re.compile(r"(?:height\s*(?:is|:|=)?\s*)([\d.]+)\s*(?:in(?:ches)?|\")", re.I),
]

# Weight patterns
_WEIGHT_LBS_PATTERNS = [
    re.compile(r"([\d.]+)\s*(?:lbs?|pounds?)", re.I),
]

_WEIGHT_KG_PATTERNS = [
    re.compile(r"([\d.]+)\s*(?:kg|kilograms?)", re.I),
]

# Generic circumference with unit
_CIRC_INCHES = re.compile(r"([\d.]+)\s*(?:in(?:ches)?|\")", re.I)
_CIRC_CM = re.compile(r"([\d.]+)\s*cm", re.I)
_BARE_NUMBER = re.compile(r"^[\s]*([\d.]+)[\s]*$")


# ── dataclass ────────────────────────────────────────────────────


@dataclass
class ParsedMeasurement:
    """Result of parsing a raw user input string for a measurement."""

    value_cm_or_kg: float  # always in cm (lengths) or kg (weight)
    original_input: str
    detected_unit: str  # "cm", "inches", "feet_inches", "kg", "lbs", "bare"


# ── public API ───────────────────────────────────────────────────


def parse_height(raw: str) -> ParsedMeasurement | None:
    """Parse a height input, returning value in cm."""
    text = raw.strip()

    # Feet + inches first (most common US format)
    for pat in _FEET_INCHES_PATTERNS:
        m = pat.search(text)
        if m:
            feet = _parse_number(m.group(1))
            inches = _parse_number(m.group(2)) if m.group(2) else 0.0
            if feet is not None:
                return ParsedMeasurement(
                    value_cm_or_kg=feet_inches_to_cm(feet, inches or 0),
                    original_input=raw,
                    detected_unit="feet_inches",
                )

    # Explicit cm
    for pat in _HEIGHT_CM_PATTERNS:
        m = pat.search(text)
        if m:
            v = _parse_number(m.group(1))
            if v is not None:
                return ParsedMeasurement(v, raw, "cm")

    # Explicit inches
    for pat in _HEIGHT_IN_PATTERNS:
        m = pat.search(text)
        if m:
            v = _parse_number(m.group(1))
            if v is not None:
                return ParsedMeasurement(inches_to_cm(v), raw, "inches")

    # Bare number — heuristic: >100 means cm, <10 means feet
    m = _BARE_NUMBER.match(text)
    if m:
        v = _parse_number(m.group(1))
        if v is not None:
            if v > 100:
                return ParsedMeasurement(v, raw, "cm")
            if v < 10:
                return ParsedMeasurement(feet_inches_to_cm(v), raw, "feet_inches")

    return None


def parse_weight(raw: str) -> ParsedMeasurement | None:
    """Parse a weight input, returning value in kg."""
    text = raw.strip()

    for pat in _WEIGHT_LBS_PATTERNS:
        m = pat.search(text)
        if m:
            v = _parse_number(m.group(1))
            if v is not None:
                return ParsedMeasurement(lbs_to_kg(v), raw, "lbs")

    for pat in _WEIGHT_KG_PATTERNS:
        m = pat.search(text)
        if m:
            v = _parse_number(m.group(1))
            if v is not None:
                return ParsedMeasurement(v, raw, "kg")

    # Bare number — heuristic: >50 means lbs (most US users), <=50 means kg
    m = _BARE_NUMBER.match(text)
    if m:
        v = _parse_number(m.group(1))
        if v is not None:
            if v > 50:
                return ParsedMeasurement(lbs_to_kg(v), raw, "lbs")
            else:
                return ParsedMeasurement(v, raw, "kg")

    return None


def parse_circumference(raw: str) -> ParsedMeasurement | None:
    """Parse a circumference/length measurement, returning value in cm."""
    text = raw.strip()

    m = _CIRC_INCHES.search(text)
    if m:
        v = _parse_number(m.group(1))
        if v is not None:
            return ParsedMeasurement(inches_to_cm(v), raw, "inches")

    m = _CIRC_CM.search(text)
    if m:
        v = _parse_number(m.group(1))
        if v is not None:
            return ParsedMeasurement(v, raw, "cm")

    # Bare number — heuristic: if <=50, assume cm (circumferences are small)
    m = _BARE_NUMBER.match(text)
    if m:
        v = _parse_number(m.group(1))
        if v is not None:
            if v <= 50:
                return ParsedMeasurement(v, raw, "cm")
            else:
                # Could be inches if it's a large number, but more likely cm
                return ParsedMeasurement(v, raw, "cm")

    return None


# Mapping from measurement key suffix to the right parser
_MEASUREMENT_PARSERS: dict[str, type] = {
    "height_cm": parse_height,
    "weight_kg": parse_weight,
}


def parse_measurement(measurement_key: str, raw: str) -> ParsedMeasurement | None:
    """Parse a raw input for a specific measurement key.

    Uses the appropriate parser based on the measurement type.
    """
    if measurement_key == "height_cm":
        return parse_height(raw)
    if measurement_key == "weight_kg":
        return parse_weight(raw)
    # Everything else is a circumference or length in cm
    return parse_circumference(raw)
