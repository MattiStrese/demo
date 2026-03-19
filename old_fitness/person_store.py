"""
person_store.py
---------------
Manages per-person training configuration files.

Config file: storage/person_config_{slug}.json
Config JSON shape:
{
  "person": "Name",
  "muscles": {
    "Biceps Brachii": {
      "enabled": true,
      "movements": {
        "Beugung": "HomeGym"    // preferred variant; absent = auto-select
      }
    },
    "Quadrizeps": { "enabled": false }
  }
}
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

_DEMO_DIR = pathlib.Path(__file__).resolve().parent
if str(_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(_DEMO_DIR))

_STORAGE_DIR = _DEMO_DIR / "storage"
_STORAGE_DIR.mkdir(exist_ok=True)

from exercises_dict import PERSONS as _BASE_PERSONS, muscle_exercises as _BASE_EXERCISES

_CONFIG_PREFIX = "person_config_"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", name.lower()).strip("_")


def _config_file(name: str) -> pathlib.Path:
    return _STORAGE_DIR / f"{_CONFIG_PREFIX}{_slug(name)}.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_persons() -> list[str]:
    """
    All known persons = hardcoded base list  +  any extra persons saved via
    the config page (in their own person_config_*.json files).
    Preserves order; no duplicates.
    """
    file_persons: list[str] = []
    for f in sorted(_STORAGE_DIR.glob(f"{_CONFIG_PREFIX}*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            file_persons.append(data["person"])
        except Exception:
            pass

    base_slugs = {_slug(p) for p in _BASE_PERSONS}
    extras = [p for p in file_persons if _slug(p) not in base_slugs]
    return list(_BASE_PERSONS) + extras


def load_person_config(name: str) -> dict:
    """
    Load saved config for *name*.
    Returns a default config (all enabled, no variant preferences) if none exists.
    """
    path = _config_file(name)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"person": name, "muscles": {}}


def save_person_config(name: str, config: dict) -> None:
    """Persist *config* for *name* to person_config_{slug}.json."""
    config["person"] = name
    _config_file(name).write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_person_exercises(name: str, base_exercises: dict | None = None) -> dict:
    """
    Apply the saved config for *name* to *base_exercises* (defaults to the
    global muscle_exercises catalog).

    - Disabled muscles are excluded entirely.
    - When a preferred variant is set for a movement, the other two variants
      are nulled out so schedule_logic picks the correct one automatically.
    """
    if base_exercises is None:
        base_exercises = _BASE_EXERCISES

    config = load_person_config(name)
    muscle_cfg: dict = config.get("muscles", {})

    result: dict = {}
    for muscle, movements in base_exercises.items():
        cfg = muscle_cfg.get(muscle, {})
        if not cfg.get("enabled", False):
            continue  # muscle disabled for this person

        result[muscle] = {}
        for movement, entry in movements.items():
            preferred: str | None = cfg.get("movements", {}).get(movement)
            new_entry = dict(entry)  # shallow copy is fine – we only replace top-level keys
            if preferred in ("Maschine", "HomeGym", "Isometrisch"):
                # Null out non-preferred variants so _pick_exercise_variant
                # in schedule_logic always chooses the right one.
                for variant in ("Maschine", "HomeGym", "Isometrisch"):
                    if variant != preferred:
                        new_entry[variant] = None
            result[muscle][movement] = new_entry

    return result
