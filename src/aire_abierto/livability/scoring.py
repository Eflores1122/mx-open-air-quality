"""Project scores for comparing places. These are not official indexes.

Each component is mapped to 0–100 with a fixed scale written below.
A higher score means the measured burden is lighter. Missing pieces are
left out and the remaining weights are scaled so they sum to 1.

Lower is better for every raw input (PM2.5, crime rate, the share of
people who feel unsafe, imputed rent). The rent score is an affordability
reading of a state average. It is not a claim that a lower figure is a
better life: local earnings are not in this file.
"""

from __future__ import annotations

AIR_GOOD_UGM3 = 5.0
AIR_POOR_UGM3 = 35.0
SAFETY_GOOD_PER_100K = 0.0
SAFETY_POOR_PER_100K = 80.0
RENT_GOOD_MONTHLY_MXN = 2_000.0
RENT_POOR_MONTHLY_MXN = 6_000.0

# Quality leaves rent on its own axis. Combined folds rent in.
QUALITY_WEIGHTS = {"air": 0.40, "safety": 0.35, "perception": 0.25}
COMBINED_WEIGHTS = {"air": 0.30, "safety": 0.30, "perception": 0.20, "rent": 0.20}

COMPONENT_KEYS = ("air", "safety", "perception", "rent")


def lower_is_better(value: float | None, good: float, poor: float) -> float | None:
    """Map a burden onto 0–100. ``good`` scores 100 and ``poor`` scores 0."""
    if value is None:
        return None
    if poor == good:
        raise ValueError("The score scale needs two different ends.")
    if value <= good:
        return 100.0
    if value >= poor:
        return 0.0
    return 100.0 * (poor - value) / (poor - good)


def score_air(pm25_ugm3: float | None) -> float | None:
    return lower_is_better(pm25_ugm3, AIR_GOOD_UGM3, AIR_POOR_UGM3)


def score_safety(rate_per_100k: float | None) -> float | None:
    return lower_is_better(rate_per_100k, SAFETY_GOOD_PER_100K, SAFETY_POOR_PER_100K)


def score_perception(insecurity_pct: float | None) -> float | None:
    """ENSU publishes a percentage. 0% insecure scores 100; 100% scores 0."""
    if insecurity_pct is None:
        return None
    if insecurity_pct < 0 or insecurity_pct > 100:
        raise ValueError(f"Perception percentage is out of range: {insecurity_pct}")
    return 100.0 - insecurity_pct


def score_rent(monthly_mxn: float | None) -> float | None:
    return lower_is_better(monthly_mxn, RENT_GOOD_MONTHLY_MXN, RENT_POOR_MONTHLY_MXN)


def combine(
    components: dict[str, float | None],
    weights: dict[str, float],
    *,
    minimum: int = 1,
) -> tuple[float | None, dict[str, float]]:
    """Weighted mean of the components that have a number.

    Returns the score and the weights actually used after dropping gaps
    and scaling the rest to 1. Returns ``(None, {})`` when fewer than
    ``minimum`` components remain. The mart asks for two, so a place
    that only has a crime rate is not ranked as if air and perception
    had been measured.
    """
    available = {
        key: float(weights.get(key, 0.0))
        for key in COMPONENT_KEYS
        if components.get(key) is not None and float(weights.get(key, 0.0)) > 0
    }
    total = sum(available.values())
    if total <= 0 or len(available) < minimum:
        return None, {}
    used = {key: weight / total for key, weight in available.items()}
    score = sum(used[key] * float(components[key]) for key in used)
    return score, used


def component_scores(
    *,
    pm25_ugm3: float | None,
    high_harm_per_100k: float | None,
    insecurity_pct: float | None,
    rent_monthly_mxn: float | None,
) -> dict[str, float | None]:
    return {
        "air": score_air(pm25_ugm3),
        "safety": score_safety(high_harm_per_100k),
        "perception": score_perception(insecurity_pct),
        "rent": score_rent(rent_monthly_mxn),
    }
