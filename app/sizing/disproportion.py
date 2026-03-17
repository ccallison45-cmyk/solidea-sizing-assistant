"""Detect disproportionate body measurements across sizing fields.

When a customer's measurements map to significantly different sizes for different
body areas (e.g., upper arm = XL but wrist = S), this module flags the disproportion
and provides per-field size mappings.

The recommendation strategy is pluggable — currently only "flag_only" is implemented.
The owner will decide on the specific recommendation logic after reviewing prototypes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FieldSizeMapping:
    """Which size a single measurement field maps to."""

    field: str
    value: float
    best_size: str
    best_size_index: int
    penalty: float


@dataclass
class DisproportionReport:
    """Analysis of whether measurements are disproportionate."""

    is_disproportionate: bool
    field_mappings: list[FieldSizeMapping]
    size_spread: int  # How many size steps apart the extremes are
    largest_field: str  # Field mapping to the biggest size
    smallest_field: str  # Field mapping to the smallest size
    notes: str


def _score_field_against_size(
    field: str, value: float, size_entry: dict
) -> float | None:
    """Score a single field against a single size entry.

    Returns penalty (0 = exact match), or None if the field isn't in this size.
    """
    measurements = size_entry["measurements"]
    if field not in measurements:
        return None

    range_min = measurements[field]["min"]
    range_max = measurements[field]["max"]

    if range_min <= value <= range_max:
        return 0.0

    span = range_max - range_min
    if value < range_min:
        return (range_min - value) / span if span else abs(range_min - value)
    return (value - range_max) / span if span else abs(value - range_max)


def _find_best_size_for_field(
    field: str, value: float, size_entries: list[dict]
) -> FieldSizeMapping:
    """Find which size a single measurement field maps to best."""
    best_index = 0
    best_penalty = float("inf")

    for i, entry in enumerate(size_entries):
        penalty = _score_field_against_size(field, value, entry)
        if penalty is None:
            continue
        if penalty < best_penalty:
            best_penalty = penalty
            best_index = i

    return FieldSizeMapping(
        field=field,
        value=value,
        best_size=size_entries[best_index]["size"],
        best_size_index=best_index,
        penalty=best_penalty,
    )


def analyze_disproportion(
    product_type: str,
    measurements: dict[str, float],
    sizing_data: dict[str, list[dict]],
    threshold: int = 2,
) -> DisproportionReport:
    """Analyze whether measurements are disproportionate.

    Args:
        product_type: The product type key.
        measurements: User's measurements keyed by field name.
        sizing_data: Full sizing data dict.
        threshold: Flag as disproportionate if any two fields differ by >= this many
                   size steps (default 2).

    Returns:
        DisproportionReport with per-field analysis.
    """
    if product_type not in sizing_data:
        return DisproportionReport(
            is_disproportionate=False,
            field_mappings=[],
            size_spread=0,
            largest_field="",
            smallest_field="",
            notes="",
        )

    size_entries = sizing_data[product_type]

    # Get the set of fields that exist in the sizing data
    available_fields: set[str] = set()
    for entry in size_entries:
        available_fields.update(entry["measurements"].keys())

    # Score each provided field independently
    field_mappings: list[FieldSizeMapping] = []
    for field, value in measurements.items():
        if field not in available_fields:
            continue
        mapping = _find_best_size_for_field(field, value, size_entries)
        field_mappings.append(mapping)

    if len(field_mappings) < 2:
        return DisproportionReport(
            is_disproportionate=False,
            field_mappings=field_mappings,
            size_spread=0,
            largest_field=field_mappings[0].field if field_mappings else "",
            smallest_field=field_mappings[0].field if field_mappings else "",
            notes="",
        )

    # Find the spread
    min_mapping = min(field_mappings, key=lambda m: m.best_size_index)
    max_mapping = max(field_mappings, key=lambda m: m.best_size_index)
    spread = max_mapping.best_size_index - min_mapping.best_size_index

    is_disproportionate = spread >= threshold

    notes = ""
    if is_disproportionate:
        notes = (
            f"Your {_field_display_name(max_mapping.field)} measures as size "
            f"{max_mapping.best_size}, while your "
            f"{_field_display_name(min_mapping.field)} measures as size "
            f"{min_mapping.best_size} "
            f"({spread} size{'s' if spread != 1 else ''} apart). "
            f"This is common with certain medical conditions. "
            f"We recommend contacting info@solideaus.com for personalized guidance."
        )

    return DisproportionReport(
        is_disproportionate=is_disproportionate,
        field_mappings=field_mappings,
        size_spread=spread,
        largest_field=max_mapping.field,
        smallest_field=min_mapping.field,
        notes=notes,
    )


def recommend_for_disproportionate(
    report: DisproportionReport,
    strategy: str = "flag_only",
) -> dict:
    """Pluggable recommendation for disproportionate measurements.

    Currently only "flag_only" is implemented. Future strategies can be added
    here after the owner decides on the recommendation logic.
    """
    if strategy == "flag_only":
        return {
            "action": "flag",
            "message": report.notes,
            "is_disproportionate": report.is_disproportionate,
            "size_spread": report.size_spread,
            "field_mappings": [
                {
                    "field": m.field,
                    "field_label": _field_display_name(m.field),
                    "value": m.value,
                    "best_size": m.best_size,
                }
                for m in report.field_mappings
            ],
        }

    raise ValueError(f"Unknown disproportion strategy: {strategy}")


def _field_display_name(field: str) -> str:
    """Convert field key to a readable label."""
    return (
        field.replace("_cm", "")
        .replace("_kg", "")
        .replace("_circumference", "")
        .replace("_", " ")
    )
