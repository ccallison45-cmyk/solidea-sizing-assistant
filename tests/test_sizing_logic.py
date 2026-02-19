"""Unit tests for the sizing engine."""

from app.sizing.engine import recommend_size
from app.sizing.loader import load_sizing_data

# Load real data once for all tests
SIZING_DATA = load_sizing_data("data")


# --- Arm Sleeves ---


class TestArmSleeves:
    def test_exact_match_small(self):
        result = recommend_size(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 26,
                "forearm_circumference_cm": 22,
                "wrist_circumference_cm": 14,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "S"
        assert result["confidence"] == "exact"

    def test_exact_match_large(self):
        result = recommend_size(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 40,
                "forearm_circumference_cm": 30,
                "wrist_circumference_cm": 20,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "L"
        assert result["confidence"] == "exact"

    def test_exact_match_xl(self):
        result = recommend_size(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 45,
                "forearm_circumference_cm": 34,
                "wrist_circumference_cm": 22,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "XL"
        assert result["confidence"] == "exact"

    def test_between_sizes(self):
        # Values on the overlap boundary between S and M
        result = recommend_size(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 30,
                "forearm_circumference_cm": 24,
                "wrist_circumference_cm": 16,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] in ("S", "M")
        assert result["confidence"] == "exact"

    def test_out_of_range_too_small(self):
        result = recommend_size(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 15,
                "forearm_circumference_cm": 15,
                "wrist_circumference_cm": 10,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "S"
        assert result["confidence"] == "out_of_range"

    def test_partial_measurements(self):
        result = recommend_size(
            "arm_sleeves",
            {"upper_arm_circumference_cm": 35},
            SIZING_DATA,
        )
        assert result["recommended_size"] in ("M", "L")


# --- Leggings ---


class TestLeggings:
    def test_exact_match_medium(self):
        result = recommend_size(
            "leggings",
            {
                "height_cm": 155,
                "weight_kg": 55,
                "hip_circumference_cm": 90,
                "waist_circumference_cm": 67,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "M"
        assert result["confidence"] == "exact"

    def test_exact_match_large(self):
        result = recommend_size(
            "leggings",
            {
                "height_cm": 170,
                "weight_kg": 75,
                "hip_circumference_cm": 95,
                "waist_circumference_cm": 73,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] in ("ML", "L")
        assert result["confidence"] == "exact"

    def test_hip_waist_only(self):
        result = recommend_size(
            "leggings",
            {"hip_circumference_cm": 100, "waist_circumference_cm": 80},
            SIZING_DATA,
        )
        assert result["recommended_size"] in ("XL", "L")

    def test_xxxl(self):
        result = recommend_size(
            "leggings",
            {
                "height_cm": 182,
                "weight_kg": 105,
                "hip_circumference_cm": 120,
                "waist_circumference_cm": 110,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "XXXL"


# --- Capris ---


class TestCapris:
    def test_exact_match_small(self):
        result = recommend_size(
            "capris",
            {
                "height_cm": 153,
                "weight_kg": 45,
                "hip_circumference_cm": 85,
                "waist_circumference_cm": 63,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "S"
        assert result["confidence"] == "exact"

    def test_exact_match_ml(self):
        result = recommend_size(
            "capris",
            {
                "height_cm": 165,
                "weight_kg": 62,
                "hip_circumference_cm": 93,
                "waist_circumference_cm": 70,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "ML"
        assert result["confidence"] == "exact"

    def test_xxl(self):
        result = recommend_size(
            "capris",
            {
                "height_cm": 178,
                "weight_kg": 95,
                "hip_circumference_cm": 110,
                "waist_circumference_cm": 93,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "XXL"


# --- Socks ---


class TestSocks:
    def test_exact_match_small(self):
        result = recommend_size(
            "socks",
            {"calf_circumference_cm": 31, "ankle_circumference_cm": 20},
            SIZING_DATA,
        )
        assert result["recommended_size"] == "S"
        assert result["confidence"] == "exact"

    def test_exact_match_large(self):
        result = recommend_size(
            "socks",
            {"calf_circumference_cm": 40, "ankle_circumference_cm": 24},
            SIZING_DATA,
        )
        assert result["recommended_size"] == "L"
        assert result["confidence"] == "exact"

    def test_exact_match_xxl(self):
        result = recommend_size(
            "socks",
            {"calf_circumference_cm": 47, "ankle_circumference_cm": 30},
            SIZING_DATA,
        )
        assert result["recommended_size"] == "XXL"
        assert result["confidence"] == "exact"

    def test_out_of_range_too_large(self):
        result = recommend_size(
            "socks",
            {"calf_circumference_cm": 60, "ankle_circumference_cm": 40},
            SIZING_DATA,
        )
        assert result["recommended_size"] == "XXL"
        assert result["confidence"] == "out_of_range"


# --- Bras ---


class TestBras:
    def test_exact_match_xs(self):
        result = recommend_size(
            "bras",
            {"bust_circumference_cm": 80, "underbust_circumference_cm": 65},
            SIZING_DATA,
        )
        assert result["recommended_size"] in ("XS", "S")
        assert result["confidence"] == "exact"

    def test_exact_match_medium(self):
        # bust=95, underbust=77 falls in S, M, and L overlap zones
        result = recommend_size(
            "bras",
            {"bust_circumference_cm": 95, "underbust_circumference_cm": 77},
            SIZING_DATA,
        )
        assert result["recommended_size"] in ("S", "M", "L")
        assert result["confidence"] == "exact"

    def test_exact_match_xxl(self):
        result = recommend_size(
            "bras",
            {"bust_circumference_cm": 130, "underbust_circumference_cm": 105},
            SIZING_DATA,
        )
        assert result["recommended_size"] == "XXL"
        assert result["confidence"] == "exact"

    def test_bust_only(self):
        result = recommend_size(
            "bras",
            {"bust_circumference_cm": 100},
            SIZING_DATA,
        )
        assert result["recommended_size"] != ""


# --- Edge Cases ---


class TestEdgeCases:
    def test_unknown_product_type(self):
        result = recommend_size("unknown_product", {"height_cm": 170}, SIZING_DATA)
        assert result["recommended_size"] == ""
        assert result["confidence"] == "out_of_range"
        assert "Unknown product type" in result["notes"]

    def test_irrelevant_measurements(self):
        result = recommend_size(
            "arm_sleeves",
            {"height_cm": 170, "weight_kg": 65},
            SIZING_DATA,
        )
        assert result["recommended_size"] == ""
        assert result["confidence"] == "out_of_range"
        assert "Expected" in result["notes"]

    def test_boundary_values_min(self):
        result = recommend_size(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 22,
                "forearm_circumference_cm": 20,
                "wrist_circumference_cm": 13,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "S"
        assert result["confidence"] == "exact"

    def test_boundary_values_max(self):
        result = recommend_size(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 49,
                "forearm_circumference_cm": 36,
                "wrist_circumference_cm": 23,
            },
            SIZING_DATA,
        )
        assert result["recommended_size"] == "XL"
        assert result["confidence"] == "exact"
