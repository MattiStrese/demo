"""
weight_store.py
---------------
Loads and saves per-exercise weights as a JSON file per person,
e.g. weights_matti.json, weights_cornelia.json, etc.

Shape: { muscle_name: { movement: { "Maschine_kg": float, "HomeGym_kg": float, "Isometrisch_kg": float } } }
"""
from __future__ import annotations

import json
import pathlib
import sys

# Add demo directory to path so local modules resolve regardless of cwd
_DEMO_DIR = pathlib.Path(__file__).resolve().parent
if str(_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(_DEMO_DIR))

_WEIGHT_KEYS: tuple[str, ...] = ("Maschine_kg", "HomeGym_kg", "Isometrisch_kg")


def _weights_file(person: str) -> pathlib.Path:
    """Return the path to the weights file for *person*."""
    name = person.lower().replace(" ", "_")
    return pathlib.Path(__file__).parent / f"weights_{name}.json"


def get_default_weights(exercises: dict) -> dict:
    """Extract factory-default weights from an exercises dict."""
    defaults: dict = {}
    for muscle, movements in exercises.items():
        defaults[muscle] = {}
        for movement, entry in movements.items():
            defaults[muscle][movement] = {
                key: float(entry.get(key) or 0) for key in _WEIGHT_KEYS
            }
    return defaults


def load_weights(person: str, exercises: dict) -> dict:
    """
    Load weights from *weights_{person}.json*, merged on top of the defaults.
    Missing keys fall back to the exercises dict defaults.
    """
    defaults = get_default_weights(exercises)
    path = _weights_file(person)
    if not path.exists():
        return defaults

    try:
        saved: dict = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return defaults

    for muscle in defaults:
        if muscle not in saved:
            continue
        for movement in defaults[muscle]:
            if movement not in saved[muscle]:
                continue
            for key in _WEIGHT_KEYS:
                if key in saved[muscle][movement]:
                    try:
                        defaults[muscle][movement][key] = float(
                            saved[muscle][movement][key]
                        )
                    except (TypeError, ValueError):
                        pass  # keep default

    return defaults


def save_weights(weights: dict, person: str) -> None:
    """Persist *weights* to *weights_{person}.json*."""
    _weights_file(person).write_text(
        json.dumps(weights, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
