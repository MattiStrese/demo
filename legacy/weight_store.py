"""
weight_store.py
---------------
Loads and saves per-exercise weights as a JSON file (weights.json)
in the same directory as this module.

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

from exercises_dict import muscle_exercises  # noqa: E402  (local copy)

_WEIGHTS_FILE = pathlib.Path(__file__).parent / "weights.json"
_WEIGHT_KEYS: tuple[str, ...] = ("Maschine_kg", "HomeGym_kg", "Isometrisch_kg")


def get_default_weights() -> dict:
    """Extract factory-default weights from exercises_dict."""
    defaults: dict = {}
    for muscle, movements in muscle_exercises.items():
        defaults[muscle] = {}
        for movement, entry in movements.items():
            defaults[muscle][movement] = {
                key: float(entry.get(key) or 0) for key in _WEIGHT_KEYS
            }
    return defaults


def load_weights() -> dict:
    """
    Load weights from *weights.json*, merged on top of the defaults.
    Missing keys fall back to the exercises_dict defaults.
    """
    defaults = get_default_weights()
    if not _WEIGHTS_FILE.exists():
        return defaults

    try:
        saved: dict = json.loads(_WEIGHTS_FILE.read_text(encoding="utf-8"))
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


def save_weights(weights: dict) -> None:
    """Persist *weights* to *weights.json*."""
    _WEIGHTS_FILE.write_text(
        json.dumps(weights, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
