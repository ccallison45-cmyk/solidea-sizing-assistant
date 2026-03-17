"""Tests for the progressive evaluation wrapper."""

from app.sizing.loader import load_sizing_data
from app.sizing.progressive import evaluate_partial

SIZING_DATA = load_sizing_data("data")


class TestEvaluatePartial:
    def test_no_measurements(self):
        result = evaluate_partial("leggings", {}, SIZING_DATA)
        assert result.is_definitive is False
        assert result.recommended_size == ""

    def test_exact_match_full_leggings(self):
        result = evaluate_partial(
            "leggings",
            {
                "height_cm": 153,
                "weight_kg": 45,
                "hip_circumference_cm": 85,
                "waist_circumference_cm": 63,
            },
            SIZING_DATA,
        )
        assert result.recommended_size == "S"
        assert result.confidence == "exact"
        assert result.is_definitive is True

    def test_partial_leggings_height_weight_only(self):
        # Just height + weight for a clear small person
        result = evaluate_partial(
            "leggings",
            {"height_cm": 153, "weight_kg": 45},
            SIZING_DATA,
        )
        assert result.recommended_size == "S"
        assert result.confidence == "exact"

    def test_between_sizes_triggers_not_definitive(self):
        # Measurements on the boundary between M and ML
        result = evaluate_partial(
            "leggings",
            {"height_cm": 160, "weight_kg": 60},
            SIZING_DATA,
        )
        # Should detect ambiguity
        assert result.recommended_size in ("M", "ML")

    def test_unknown_product_type(self):
        result = evaluate_partial("nonexistent", {"height_cm": 170}, SIZING_DATA)
        assert result.recommended_size == ""
        assert result.confidence == "out_of_range"

    def test_socks_exact(self):
        result = evaluate_partial(
            "socks",
            {"calf_circumference_cm": 35, "ankle_circumference_cm": 21},
            SIZING_DATA,
        )
        assert result.recommended_size in ("S", "M")
        assert result.confidence == "exact"

    def test_bras_exact(self):
        result = evaluate_partial(
            "bras",
            {"bust_circumference_cm": 90, "underbust_circumference_cm": 74},
            SIZING_DATA,
        )
        assert result.recommended_size in ("S", "M")
        assert result.confidence == "exact"

    def test_arm_sleeves_partial(self):
        result = evaluate_partial(
            "arm_sleeves",
            {"upper_arm_circumference_cm": 25},
            SIZING_DATA,
        )
        assert result.recommended_size == "S"
        assert result.confidence == "exact"

    def test_out_of_range_is_definitive(self):
        # Extremely large measurements
        result = evaluate_partial(
            "socks",
            {"calf_circumference_cm": 80, "ankle_circumference_cm": 50},
            SIZING_DATA,
        )
        assert result.confidence == "out_of_range"
        assert result.is_definitive is True
