"""Tests for disproportionate measurement detection."""

import pytest

from app.sizing.disproportion import (
    DisproportionReport,
    FieldSizeMapping,
    _find_best_size_for_field,
    analyze_disproportion,
    recommend_for_disproportionate,
)
from app.sizing.loader import load_sizing_data

# Load real sizing data for integration-style tests
_sizing_data = load_sizing_data("data")


class TestFieldSizeMapping:
    """Test per-field size scoring."""

    def test_exact_match_small(self):
        mapping = _find_best_size_for_field(
            "upper_arm_circumference_cm", 26.0, _sizing_data["arm_sleeves"]
        )
        assert mapping.best_size == "S"
        assert mapping.penalty == 0.0

    def test_exact_match_large(self):
        mapping = _find_best_size_for_field(
            "upper_arm_circumference_cm", 45.0, _sizing_data["arm_sleeves"]
        )
        assert mapping.best_size == "XL"
        assert mapping.penalty == 0.0

    def test_between_sizes_picks_closer(self):
        # Value of 31 is just above S max (30), right at M min (30)
        mapping = _find_best_size_for_field(
            "upper_arm_circumference_cm", 31.0, _sizing_data["arm_sleeves"]
        )
        assert mapping.best_size == "M"
        assert mapping.penalty == 0.0

    def test_field_not_in_data(self):
        # Using a field that exists in leggings but not arm_sleeves
        mapping = _find_best_size_for_field(
            "height_cm", 170.0, _sizing_data["arm_sleeves"]
        )
        # Should still return something (falls back to first size)
        assert mapping.best_size is not None


class TestAnalyzeDisproportion:
    """Test the main disproportion analysis."""

    def test_proportionate_measurements(self):
        """All fields map to the same size — not disproportionate."""
        report = analyze_disproportion(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 26.0,  # S
                "forearm_circumference_cm": 22.0,  # S
                "wrist_circumference_cm": 14.0,  # S
            },
            _sizing_data,
        )
        assert not report.is_disproportionate
        assert report.size_spread == 0

    def test_slightly_off_not_disproportionate(self):
        """Fields differ by 1 size — below default threshold of 2."""
        report = analyze_disproportion(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 26.0,  # S
                "forearm_circumference_cm": 26.0,  # M
                "wrist_circumference_cm": 14.0,  # S
            },
            _sizing_data,
        )
        assert not report.is_disproportionate
        assert report.size_spread == 1

    def test_disproportionate_arm_measurements(self):
        """Upper arm maps to XL but wrist maps to S — 3 sizes apart."""
        report = analyze_disproportion(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 45.0,  # XL
                "forearm_circumference_cm": 22.0,  # S
                "wrist_circumference_cm": 14.0,  # S
            },
            _sizing_data,
        )
        assert report.is_disproportionate
        assert report.size_spread == 3
        assert report.largest_field == "upper_arm_circumference_cm"
        assert report.smallest_field in ("forearm_circumference_cm", "wrist_circumference_cm")
        assert "info@solideaus.com" in report.notes

    def test_disproportionate_with_custom_threshold(self):
        """A spread of 1 is flagged with threshold=1."""
        report = analyze_disproportion(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 26.0,  # S
                "forearm_circumference_cm": 26.0,  # M
                "wrist_circumference_cm": 14.0,  # S
            },
            _sizing_data,
            threshold=1,
        )
        assert report.is_disproportionate
        assert report.size_spread == 1

    def test_single_measurement_never_disproportionate(self):
        """Can't be disproportionate with only one field."""
        report = analyze_disproportion(
            "arm_sleeves",
            {"upper_arm_circumference_cm": 45.0},
            _sizing_data,
        )
        assert not report.is_disproportionate
        assert len(report.field_mappings) == 1

    def test_unknown_product_type(self):
        report = analyze_disproportion(
            "nonexistent_product",
            {"upper_arm_circumference_cm": 26.0},
            _sizing_data,
        )
        assert not report.is_disproportionate
        assert len(report.field_mappings) == 0

    def test_leggings_disproportionate(self):
        """Height/weight map to S but hip maps to XXL — common with lipedema."""
        report = analyze_disproportion(
            "leggings",
            {
                "height_cm": 154.0,  # S
                "weight_kg": 45.0,  # S
                "hip_circumference_cm": 110.0,  # XXL
                "waist_circumference_cm": 65.0,  # S/M
            },
            _sizing_data,
        )
        assert report.is_disproportionate
        assert report.size_spread >= 3
        assert "hip" in report.largest_field

    def test_field_mappings_populated(self):
        report = analyze_disproportion(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 26.0,
                "forearm_circumference_cm": 22.0,
                "wrist_circumference_cm": 14.0,
            },
            _sizing_data,
        )
        assert len(report.field_mappings) == 3
        for m in report.field_mappings:
            assert m.field != ""
            assert m.best_size != ""
            assert m.value > 0

    def test_irrelevant_fields_ignored(self):
        """Fields not in the sizing data are silently ignored."""
        report = analyze_disproportion(
            "arm_sleeves",
            {
                "upper_arm_circumference_cm": 26.0,
                "forearm_circumference_cm": 22.0,
                "completely_fake_field": 999.0,
            },
            _sizing_data,
        )
        assert len(report.field_mappings) == 2


class TestRecommendForDisproportionate:
    """Test the pluggable recommendation strategy."""

    def test_flag_only_strategy(self):
        report = DisproportionReport(
            is_disproportionate=True,
            field_mappings=[
                FieldSizeMapping("upper_arm_circumference_cm", 45.0, "XL", 3, 0.0),
                FieldSizeMapping("wrist_circumference_cm", 14.0, "S", 0, 0.0),
            ],
            size_spread=3,
            largest_field="upper_arm_circumference_cm",
            smallest_field="wrist_circumference_cm",
            notes="Test notes",
        )
        result = recommend_for_disproportionate(report, strategy="flag_only")
        assert result["action"] == "flag"
        assert result["is_disproportionate"] is True
        assert result["size_spread"] == 3
        assert len(result["field_mappings"]) == 2

    def test_unknown_strategy_raises(self):
        report = DisproportionReport(
            is_disproportionate=False,
            field_mappings=[],
            size_spread=0,
            largest_field="",
            smallest_field="",
            notes="",
        )
        with pytest.raises(ValueError, match="Unknown disproportion strategy"):
            recommend_for_disproportionate(report, strategy="nonexistent")
