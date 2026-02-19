"""Load and validate sizing data from JSON files."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EXPECTED_PRODUCT_FILES = {
    "arm_sleeves": "arm-sleeves.json",
    "leggings": "leggings.json",
    "capris": "capris.json",
    "socks": "socks.json",
    "bras": "bras.json",
}


def _validate_sizing_entry(entry: dict, filepath: str, index: int) -> None:
    """Validate a single sizing entry against the expected structure."""
    if "size" not in entry:
        raise ValueError(f"{filepath}: entry {index} missing 'size' field")
    if not isinstance(entry["size"], str) or not entry["size"]:
        raise ValueError(f"{filepath}: entry {index} has invalid 'size' (must be non-empty string)")

    if "measurements" not in entry:
        raise ValueError(f"{filepath}: entry {index} missing 'measurements' field")

    measurements = entry["measurements"]
    if not isinstance(measurements, dict) or len(measurements) == 0:
        raise ValueError(f"{filepath}: entry {index} 'measurements' must be a non-empty object")

    for field_name, range_obj in measurements.items():
        if not isinstance(range_obj, dict):
            raise ValueError(f"{filepath}: entry {index}, field '{field_name}' must be an object")
        if "min" not in range_obj or "max" not in range_obj:
            raise ValueError(
                f"{filepath}: entry {index}, field '{field_name}' missing 'min' or 'max'"
            )
        if not isinstance(range_obj["min"], (int, float)):
            raise ValueError(
                f"{filepath}: entry {index}, field '{field_name}' min must be a number"
            )
        if not isinstance(range_obj["max"], (int, float)):
            raise ValueError(
                f"{filepath}: entry {index}, field '{field_name}' max must be a number"
            )
        if range_obj["min"] > range_obj["max"]:
            raise ValueError(f"{filepath}: entry {index}, field '{field_name}' min > max")


def load_sizing_data(data_dir: str = "data") -> dict[str, list[dict]]:
    """Load all sizing JSON files from the data directory.

    Returns a dict mapping product_type -> list of size entries.
    Raises ValueError if any file is missing or invalid.
    """
    data_path = Path(data_dir)
    if not data_path.is_dir():
        raise ValueError(f"Sizing data directory not found: {data_dir}")

    sizing_data: dict[str, list[dict]] = {}

    for product_type, filename in EXPECTED_PRODUCT_FILES.items():
        filepath = data_path / filename
        if not filepath.exists():
            raise ValueError(f"Missing sizing data file: {filepath}")

        try:
            raw = json.loads(filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}") from e

        if not isinstance(raw, list) or len(raw) == 0:
            raise ValueError(f"{filepath}: must be a non-empty array")

        for i, entry in enumerate(raw):
            _validate_sizing_entry(entry, str(filepath), i)

        sizing_data[product_type] = raw
        logger.info("Loaded %d sizes for %s from %s", len(raw), product_type, filepath)

    return sizing_data
