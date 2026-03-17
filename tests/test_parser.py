"""Tests for the measurement parser module."""

from app.conversation.parser import (
    feet_inches_to_cm,
    inches_to_cm,
    lbs_to_kg,
    parse_circumference,
    parse_height,
    parse_measurement,
    parse_weight,
)


class TestFeetInchesToCm:
    def test_five_six(self):
        assert abs(feet_inches_to_cm(5, 6) - 167.64) < 0.01

    def test_five_foot_even(self):
        assert abs(feet_inches_to_cm(5, 0) - 152.4) < 0.01

    def test_six_foot(self):
        assert abs(feet_inches_to_cm(6, 0) - 182.88) < 0.01

    def test_five_ten(self):
        assert abs(feet_inches_to_cm(5, 10) - 177.8) < 0.01


class TestInchesToCm:
    def test_twelve_inches(self):
        assert abs(inches_to_cm(12) - 30.48) < 0.01

    def test_fifteen_inches(self):
        assert abs(inches_to_cm(15) - 38.1) < 0.01


class TestLbsToKg:
    def test_150_lbs(self):
        assert abs(lbs_to_kg(150) - 68.04) < 0.1

    def test_140_lbs(self):
        assert abs(lbs_to_kg(140) - 63.50) < 0.1


class TestParseHeight:
    def test_feet_inches_quote(self):
        result = parse_height("5'7\"")
        assert result is not None
        assert abs(result.value_cm_or_kg - 170.18) < 0.1
        assert result.detected_unit == "feet_inches"

    def test_feet_inches_no_inches(self):
        result = parse_height("5'")
        assert result is not None
        assert abs(result.value_cm_or_kg - 152.4) < 0.1

    def test_feet_word(self):
        result = parse_height("5 foot 10")
        assert result is not None
        assert abs(result.value_cm_or_kg - 177.8) < 0.1

    def test_cm_explicit(self):
        result = parse_height("height is 170 cm")
        assert result is not None
        assert result.value_cm_or_kg == 170
        assert result.detected_unit == "cm"

    def test_cm_tall(self):
        result = parse_height("165cm tall")
        assert result is not None
        assert result.value_cm_or_kg == 165

    def test_i_am_cm(self):
        result = parse_height("I'm 170 cm")
        assert result is not None
        assert result.value_cm_or_kg == 170

    def test_bare_number_large(self):
        result = parse_height("170")
        assert result is not None
        assert result.value_cm_or_kg == 170
        assert result.detected_unit == "cm"

    def test_bare_number_small(self):
        result = parse_height("5")
        assert result is not None
        assert result.detected_unit == "feet_inches"

    def test_inches_explicit(self):
        result = parse_height("height is 67 inches")
        assert result is not None
        assert abs(result.value_cm_or_kg - 170.18) < 0.1

    def test_garbage(self):
        assert parse_height("hello world") is None


class TestParseWeight:
    def test_lbs(self):
        result = parse_weight("140 lbs")
        assert result is not None
        assert abs(result.value_cm_or_kg - 63.50) < 0.1
        assert result.detected_unit == "lbs"

    def test_pounds(self):
        result = parse_weight("150 pounds")
        assert result is not None
        assert abs(result.value_cm_or_kg - 68.04) < 0.1

    def test_kg(self):
        result = parse_weight("65 kg")
        assert result is not None
        assert result.value_cm_or_kg == 65
        assert result.detected_unit == "kg"

    def test_bare_number_over_50(self):
        result = parse_weight("140")
        assert result is not None
        assert result.detected_unit == "lbs"

    def test_bare_number_under_50(self):
        result = parse_weight("45")
        assert result is not None
        assert result.detected_unit == "kg"

    def test_garbage(self):
        assert parse_weight("hello") is None


class TestParseCircumference:
    def test_inches(self):
        result = parse_circumference("15 inches")
        assert result is not None
        assert abs(result.value_cm_or_kg - 38.1) < 0.1

    def test_cm(self):
        result = parse_circumference("38 cm")
        assert result is not None
        assert result.value_cm_or_kg == 38

    def test_bare_number(self):
        result = parse_circumference("15")
        assert result is not None
        assert result.value_cm_or_kg == 15
        assert result.detected_unit == "cm"

    def test_inch_symbol(self):
        result = parse_circumference('12"')
        assert result is not None
        assert abs(result.value_cm_or_kg - 30.48) < 0.1


class TestParseMeasurement:
    def test_routes_height(self):
        result = parse_measurement("height_cm", "5'6\"")
        assert result is not None
        assert abs(result.value_cm_or_kg - 167.64) < 0.1

    def test_routes_weight(self):
        result = parse_measurement("weight_kg", "140 lbs")
        assert result is not None
        assert abs(result.value_cm_or_kg - 63.50) < 0.1

    def test_routes_circumference(self):
        result = parse_measurement("calf_circumference_cm", "15 inches")
        assert result is not None
        assert abs(result.value_cm_or_kg - 38.1) < 0.1
