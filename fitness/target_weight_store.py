"""
target_weight_store.py
----------------------
Persist per-person target-weight overrides for exercise entries.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

_DEMO_DIR = pathlib.Path(__file__).resolve().parent
if str(_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(_DEMO_DIR))

from exercises_dict import exercise_entries, muscle_exercises

_TARGET_KEYS: tuple[str, ...] = ("Maschine", "HomeGym", "Isometrisch")


def _target_weights_file(person: str) -> pathlib.Path:
    """Return the path to the target-weight overrides file for *person*."""
    name = person.lower().replace(" ", "_")
    return pathlib.Path(__file__).parent / f"target_weights_{name}.json"


def get_default_target_weights(exercises: dict) -> dict:
    """Extract default target weights from an exercises dict."""
    defaults: dict = {}
    for muscle, movements in exercises.items():
        defaults[muscle] = {}
        for movement, entry in movements.items():
            defaults[muscle][movement] = {}
            for variant in _TARGET_KEYS:
                options = exercise_entries(entry.get(variant))
                if not options:
                    continue
                defaults[muscle][movement][variant] = {
                    str(option["name"]): float(option.get("target_weight") or 0.0)
                    for option in options
                }
    return defaults


def load_target_weights(person: str, exercises: dict | None = None) -> dict:
    """
    Load target-weight overrides for *person* merged on top of exercise defaults.
    """
    source_exercises = exercises if exercises is not None else muscle_exercises
    defaults = get_default_target_weights(source_exercises)
    path = _target_weights_file(person)
    if not path.exists():
        return defaults

    try:
        saved: dict = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return defaults

    for muscle, movements in defaults.items():
        saved_movements = saved.get(muscle, {})
        if not isinstance(saved_movements, dict):
            continue
        for movement, variants in movements.items():
            saved_variants = saved_movements.get(movement, {})
            if not isinstance(saved_variants, dict):
                continue
            for variant, exercises_map in variants.items():
                saved_exercises = saved_variants.get(variant, {})
                if not isinstance(saved_exercises, dict):
                    continue
                for exercise_name in exercises_map:
                    if exercise_name not in saved_exercises:
                        continue
                    try:
                        exercises_map[exercise_name] = float(saved_exercises[exercise_name])
                    except (TypeError, ValueError):
                        pass

    return defaults


def save_target_weights(target_weights: dict, person: str) -> None:
    """Persist target-weight overrides for *person*."""
    _target_weights_file(person).write_text(
        json.dumps(target_weights, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def apply_target_weights(exercises: dict, target_weights: dict) -> dict:
    """Return a deep-copied exercises dict with target-weight overrides applied."""
    updated = copy.deepcopy(exercises)

    for muscle, movements in updated.items():
        for movement, entry in movements.items():
            for variant in _TARGET_KEYS:
                raw_value = entry.get(variant)
                if not raw_value:
                    continue

                options = exercise_entries(raw_value)
                for option in options:
                    exercise_name = str(option["name"])
                    override = (
                        target_weights.get(muscle, {})
                        .get(movement, {})
                        .get(variant, {})
                        .get(exercise_name)
                    )
                    if override is not None:
                        option["target_weight"] = float(override)

                if isinstance(raw_value, list):
                    entry[variant] = options
                else:
                    entry[variant] = options[0] if options else None

    return updated


def load_target_weighted_exercises(person: str, exercises: dict | None = None) -> dict:
    """Load exercises with persisted target-weight overrides applied for *person*."""
    source_exercises = exercises if exercises is not None else muscle_exercises
    target_weights = load_target_weights(person, source_exercises)
    return apply_target_weights(source_exercises, target_weights)
