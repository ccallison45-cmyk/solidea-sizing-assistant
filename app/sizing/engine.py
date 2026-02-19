"""Core sizing logic: match measurements against loaded sizing data."""


def _score_size(size_entry: dict, measurements: dict[str, float]) -> tuple[str, float, int]:
    """Score how well a set of measurements matches a size entry.

    Returns (status, penalty, matched_fields) where:
    - status: "exact" if all provided measurements fall within ranges,
              "interpolated" if close but not all within range,
              "out_of_range" if far outside ranges
    - penalty: sum of how far outside the ranges the measurements fall (0 = perfect match)
    - matched_fields: count of measurements that fall within the size's ranges
    """
    size_measurements = size_entry["measurements"]
    available_fields = set(size_measurements.keys())
    provided_fields = set(measurements.keys())
    common_fields = available_fields & provided_fields

    if not common_fields:
        return ("out_of_range", float("inf"), 0)

    total_penalty = 0.0
    matched_count = 0

    for field in common_fields:
        value = measurements[field]
        range_min = size_measurements[field]["min"]
        range_max = size_measurements[field]["max"]

        if range_min <= value <= range_max:
            matched_count += 1
        elif value < range_min:
            span = range_max - range_min
            total_penalty += (range_min - value) / span if span else abs(range_min - value)
        else:
            span = range_max - range_min
            total_penalty += (value - range_max) / span if span else abs(value - range_max)

    if matched_count == len(common_fields):
        status = "exact"
    elif total_penalty <= 0.5:
        status = "interpolated"
    else:
        status = "out_of_range"

    return (status, total_penalty, matched_count)


def recommend_size(
    product_type: str,
    measurements: dict[str, float],
    sizing_data: dict[str, list[dict]],
) -> dict:
    """Find the best matching size for given measurements.

    Returns a dict with recommended_size, confidence, and notes.
    """
    if product_type not in sizing_data:
        return {
            "recommended_size": "",
            "confidence": "out_of_range",
            "notes": f"Unknown product type: {product_type}",
        }

    size_entries = sizing_data[product_type]

    # Check that at least one provided measurement is relevant
    all_fields: set[str] = set()
    for entry in size_entries:
        all_fields.update(entry["measurements"].keys())

    provided_fields = set(measurements.keys())
    relevant_fields = all_fields & provided_fields
    if not relevant_fields:
        return {
            "recommended_size": "",
            "confidence": "out_of_range",
            "notes": (
                f"None of the provided measurements ({', '.join(sorted(provided_fields))}) "
                f"are relevant for {product_type}. "
                f"Expected: {', '.join(sorted(all_fields))}"
            ),
        }

    # Score each size
    scored: list[tuple[dict, str, float, int]] = []
    for entry in size_entries:
        status, penalty, matched = _score_size(entry, measurements)
        scored.append((entry, status, penalty, matched))

    # Sort: prefer exact matches, then fewest penalty, then most matched fields
    scored.sort(key=lambda x: (x[1] != "exact", x[2], -x[3]))

    best_entry, best_status, best_penalty, best_matched = scored[0]
    best_size = best_entry["size"]

    notes = ""
    if best_status == "interpolated":
        # Check if there's a second candidate close by
        if len(scored) > 1:
            second = scored[1]
            if second[1] in ("exact", "interpolated") and abs(second[2] - best_penalty) < 0.3:
                notes = (
                    f"You're between sizes {best_size} and {second[0]['size']}. "
                    f"We recommend {best_size}, but consider sizing up to "
                    f"{second[0]['size']} for a more comfortable fit."
                )
            else:
                notes = (
                    f"Your measurements are close to size {best_size} but not an exact match. "
                    f"Consider sizing up for comfort."
                )
        else:
            notes = (
                f"Your measurements are close to size {best_size} but not an exact match. "
                f"Consider sizing up for comfort."
            )
    elif best_status == "out_of_range":
        notes = (
            f"Your measurements fall outside the standard size range. "
            f"The closest size is {best_size}. "
            f"Please contact info@solideaus.com for personalized assistance."
        )

    return {
        "recommended_size": best_size,
        "confidence": best_status,
        "notes": notes,
    }
