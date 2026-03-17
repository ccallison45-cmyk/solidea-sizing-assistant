"""Progressive evaluation — run the sizing engine with partial measurements.

Wraps engine.recommend_size to support incremental question flows.
The core engine is NOT modified; this module only calls it.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.sizing.engine import recommend_size


@dataclass
class ProgressiveResult:
    """Result of evaluating partial measurements."""

    recommended_size: str
    confidence: str  # "exact", "interpolated", "out_of_range"
    notes: str
    is_definitive: bool  # True if we can stop asking questions
    ambiguous_candidates: list[str]  # close second-choice sizes, if any


def evaluate_partial(
    product_type: str,
    measurements: dict[str, float],
    sizing_data: dict[str, list[dict]],
) -> ProgressiveResult:
    """Run the sizing engine with whatever measurements we have so far.

    Returns a ProgressiveResult indicating whether the recommendation is
    definitive or whether more measurements would help disambiguate.
    """
    if not measurements:
        return ProgressiveResult(
            recommended_size="",
            confidence="out_of_range",
            notes="No measurements provided yet.",
            is_definitive=False,
            ambiguous_candidates=[],
        )

    result = recommend_size(product_type, measurements, sizing_data)
    size = result["recommended_size"]
    confidence = result["confidence"]
    notes = result["notes"]

    # Determine if result is definitive
    if confidence == "exact":
        # Check if there are close runners-up by re-examining the data
        ambiguous = _find_close_candidates(product_type, measurements, sizing_data, size)
        is_definitive = len(ambiguous) == 0
        return ProgressiveResult(
            recommended_size=size,
            confidence=confidence,
            notes=notes,
            is_definitive=is_definitive,
            ambiguous_candidates=ambiguous,
        )

    if confidence == "interpolated":
        ambiguous = _find_close_candidates(product_type, measurements, sizing_data, size)
        return ProgressiveResult(
            recommended_size=size,
            confidence=confidence,
            notes=notes,
            is_definitive=False,
            ambiguous_candidates=ambiguous,
        )

    # out_of_range
    return ProgressiveResult(
        recommended_size=size,
        confidence=confidence,
        notes=notes,
        is_definitive=True,  # nothing more to ask — they're outside the range
        ambiguous_candidates=[],
    )


def _find_close_candidates(
    product_type: str,
    measurements: dict[str, float],
    sizing_data: dict[str, list[dict]],
    best_size: str,
) -> list[str]:
    """Find sizes that are close competitors to the best match.

    Uses the same scoring approach as engine._score_size but exposes
    the runner-up sizes for the conversation manager to decide whether
    a follow-up question is needed.
    """
    from app.sizing.engine import _score_size

    if product_type not in sizing_data:
        return []

    scored = []
    for entry in sizing_data[product_type]:
        status, penalty, matched = _score_size(entry, measurements)
        scored.append((entry["size"], status, penalty, matched))

    # Sort same way as engine
    scored.sort(key=lambda x: (x[1] != "exact", x[2], -x[3]))

    if len(scored) < 2:
        return []

    best = scored[0]
    candidates = []
    for other in scored[1:]:
        # "Close" means the penalty difference is small
        if abs(other[2] - best[2]) < 0.3 and other[1] in ("exact", "interpolated"):
            candidates.append(other[0])

    return candidates
