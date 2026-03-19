"""
schedule_logic.py
-----------------
Pure-logic helpers for building the weekly training plan and
generating the hypertrophy progression chart.

Extracted / adapted from backend/training_schedule_strength.py.
No PDF or backend.core imports here – keeps the demo self-contained.
"""
from __future__ import annotations

import datetime
import io
import math
import random

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WEEKLY_PROGRESSION_RATE: float = 0.025  # 2.5 % per week

WEEK_DAYS: list[str] = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]

_SECONDARY_THEMES: list[str] = [
    "Rotation",
    "Lateralflexion",
    "Adduktion",
    "Abduktion",
    "Supination",
    "Pronation",
    "Elevation",
    "Depression",
    "Protraktion",
    "Anti-Extension",
    "Anti-Rotation",
]

_WEEKLY_THEMES: list[str | list[str]] = [
    "Beugung",
    "Streckung",
    _SECONDARY_THEMES,
    "Beugung",
    "Streckung",
    _SECONDARY_THEMES,
    "Beugung",
]

DAY_TO_THEME: dict[str, str | list[str]] = {
    WEEK_DAYS[i]: _WEEKLY_THEMES[i] for i in range(len(WEEK_DAYS))
}

_WEIGHT_KEY_MAP: dict[str, str] = {
    "Maschine": "Maschine_kg",
    "Dynamisch": "HomeGym_kg",
    "Isometrisch": "Isometrisch_kg",
}

_PRIORITY_MOVEMENTS: list[str] = [
    "Rotation",
    "Lateralflexion",
    "Adduktion",
    "Abduktion",
    "Elevation",
    "Depression",
    "Anti-Extension",
    "Supination",
    "Pronation",
]


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------
def round_to_half(value: float) -> float:
    """Round to the nearest 0.5 kg."""
    return math.floor(value * 2 + 0.5) / 2


def compute_hypertrophy_weight(current_kg: float, weeks: int) -> float:
    """Project weight after *weeks* of 2.5 % weekly overload, rounded to 0.5 kg."""
    if current_kg <= 0:
        return 0.0
    return round_to_half(current_kg * (1 + WEEKLY_PROGRESSION_RATE) ** weeks)


# ---------------------------------------------------------------------------
# Exercise selection
# ---------------------------------------------------------------------------
def _pick_exercise_variant(
    muscle_exercises: dict,
    muscle_name: str,
    movement: str,
    *,
    prefer_isometric: bool,
) -> tuple[str | None, str | None]:
    entry = muscle_exercises[muscle_name][movement]

    if prefer_isometric:
        iso = entry.get("Isometrisch")
        if iso and iso not in (None, "None", "none"):
            return iso, "Isometrisch"

    home = entry.get("HomeGym")
    if home and home not in (None, "None", "none"):
        return home, "Dynamisch"

    machine = entry.get("Maschine")
    if machine and machine not in (None, "None", "none"):
        return machine, "Maschine"

    return None, None


def _pick_movement_for_day(
    available: list[str],
    day_theme: str | list[str],
) -> str | None:
    if isinstance(day_theme, str):
        return day_theme if day_theme in available else None

    for m in _PRIORITY_MOVEMENTS:
        if m in available and m in day_theme:
            return m

    candidates = [m for m in available if m in day_theme]
    return random.choice(candidates) if candidates else None


# ---------------------------------------------------------------------------
# Weekly plan builder
# ---------------------------------------------------------------------------
def build_weekly_plan(
    muscle_exercises: dict,
    weights: dict,
) -> dict:
    """
    Build the full weekly plan.

    *weights* has shape:  weights[muscle][movement][weight_key] = float
    Returns a dict shaped:  plan[day][muscle] = { exercise info dict }
    """
    weekly_plan: dict = {}

    for day_name in WEEK_DAYS:
        day_theme = DAY_TO_THEME[day_name]
        is_secondary = isinstance(day_theme, list)
        daily_plan: dict = {}

        for muscle_name in muscle_exercises:
            available = list(muscle_exercises[muscle_name].keys())
            movement = _pick_movement_for_day(available, day_theme)
            if not movement:
                continue

            exercise_name, execution_type = _pick_exercise_variant(
                muscle_exercises,
                muscle_name,
                movement,
                prefer_isometric=is_secondary,
            )
            if not exercise_name or not execution_type:
                continue

            weight_key = _WEIGHT_KEY_MAP.get(execution_type, "HomeGym_kg")
            current_weight = float(
                weights.get(muscle_name, {}).get(movement, {}).get(weight_key, 0.0)
            )

            daily_plan[muscle_name] = {
                "Bewegung": movement,
                "Typ": execution_type,
                "Übung": exercise_name,
                "Gewicht_key": weight_key,
                "Gewicht_kg": current_weight,
                "Gewicht_1W": compute_hypertrophy_weight(current_weight, 1),
                "Gewicht_1M": compute_hypertrophy_weight(current_weight, 4),
            }

        weekly_plan[day_name] = daily_plan

    return weekly_plan


# ---------------------------------------------------------------------------
# Progression chart
# ---------------------------------------------------------------------------
WeightRow = tuple[str, str, float, float, float]  # (muscle, exercise, now, +1W, +1M)


def generate_progression_chart(
    rows: list[WeightRow],
    today: datetime.date,
) -> plt.Figure | None:
    """
    Horizontal grouped bar chart: now vs +1 week vs +1 month.
    Returns a matplotlib Figure or None when all weights are 0.
    """
    weighted = [(m, e, c, w, mo) for m, e, c, w, mo in rows if c > 0]
    if not weighted:
        return None

    date_1w = today + datetime.timedelta(weeks=1)
    date_1m = today + datetime.timedelta(days=30)

    labels = [m[:30] for m, *_ in weighted]
    now_vals = [c for _, _, c, _, _ in weighted]
    w1_vals = [w for _, _, _, w, _ in weighted]
    m1_vals = [mo for _, _, _, _, mo in weighted]

    n = len(labels)
    bar_h = 0.26
    y_pos = list(range(n))

    fig, ax = plt.subplots(figsize=(13, max(5, n * 0.55)))
    ax.barh(
        [i + bar_h for i in y_pos],
        now_vals,
        bar_h,
        label=f"Heute  {today.strftime('%d.%m.%Y')}",
        color="#1976D2",
    )
    ax.barh(
        y_pos,
        w1_vals,
        bar_h,
        label=f"+1 Woche  {date_1w.strftime('%d.%m.%Y')}",
        color="#388E3C",
    )
    ax.barh(
        [i - bar_h for i in y_pos],
        m1_vals,
        bar_h,
        label=f"+1 Monat  {date_1m.strftime('%d.%m.%Y')}",
        color="#F57C00",
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Gewicht (kg)", fontsize=9)
    ax.set_title(
        f"Trainingsgewicht-Progression (Hypertrophie +{WEEKLY_PROGRESSION_RATE * 100:.1f}%/Woche)\n"
        f"Stand: {today.strftime('%d.%m.%Y')}",
        fontsize=10,
    )
    ax.legend(fontsize=8)
    ax.xaxis.grid(True, alpha=0.35)
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def format_theme_label(theme: str | list[str]) -> str:
    return "/".join(theme) if isinstance(theme, list) else theme
