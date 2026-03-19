"""
pages/1_Neue_Person.py
----------------------
Streamlit page: create or edit a person's training configuration.

For each muscle the trainer can:
  • Enable / disable the muscle entirely
  • Per movement: choose which exercise variant to use
    (Automatisch = let the schedule pick, or lock to Maschine / HomeGym / Isometrisch)

Run from the project root:
    streamlit run backend/demo/app.py
"""
from __future__ import annotations

import pathlib
import sys

_DEMO_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(_DEMO_DIR))

import streamlit as st

from constants import BODY_PARTS, VARIANTS
from exercises_dict import muscle_exercises
from person_store import (
    build_person_exercises,
    list_persons,
    load_person_config,
    save_person_config,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="👤 Person konfigurieren",
    page_icon="👤",
    layout="wide",
)

st.title("👤 Person konfigurieren")
st.caption(
    "Lege eine neue Person an oder bearbeite eine bestehende Konfiguration. "
    "Wähle für jeden Muskel, ob er trainiert wird, und welche Übungsvariante bevorzugt wird."
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.muscle-header { font-weight: 700; font-size: 1em; }
.bodypart-header {
    font-size: 1.05em; font-weight: 700; color: #1976D2;
    border-bottom: 2px solid #1976D2;
    padding-bottom: 3px; margin-top: 12px; margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Person selection / creation
# ---------------------------------------------------------------------------
existing_persons = list_persons()

col_sel, col_new = st.columns([2, 2], gap="large")

with col_sel:
    st.subheader("Bestehende Person bearbeiten")
    edit_person = st.selectbox(
        "Person auswählen",
        ["— neue Person —"] + existing_persons,
        key="edit_person_select",
    )

with col_new:
    st.subheader("Neue Person anlegen")
    new_name = st.text_input(
        "Name der neuen Person",
        placeholder="z. B. Julia",
        key="new_person_name",
    )

# Determine which person we're configuring
if edit_person != "— neue Person —":
    person_name = edit_person
elif new_name.strip():
    person_name = new_name.strip()
else:
    person_name = None

if person_name is None:
    st.info("👆 Wähle eine bestehende Person aus oder gib einen neuen Namen ein.")
    st.stop()

st.divider()
st.subheader(f"Konfiguration für: **{person_name}**")

# Load existing config (or default)
config = load_person_config(person_name)
muscle_cfg: dict = config.setdefault("muscles", {})

# ---------------------------------------------------------------------------
# Helper – exercise option labels for a movement entry
# ---------------------------------------------------------------------------
_NONE_VALS = (None, "None", "none", "-", "")

def _variant_options(entry: dict) -> list[str]:
    """Return list of selectable option strings for a movement entry."""
    opts = ["⚙️ Automatisch"]
    for key, icon, label in VARIANTS:
        val = entry.get(key)
        if val not in _NONE_VALS:
            opts.append(f"{icon} {label}: {str(val)[:60]}")
    return opts


def _option_to_variant(option: str) -> str | None:
    """Map a display option string back to the variant key."""
    for key, icon, label in VARIANTS:
        if option.startswith(f"{icon} {label}:"):
            return key
    return None  # Automatisch


def _current_option(entry: dict, preferred: str | None, opts: list[str]) -> str:
    """Find the currently selected option string for this movement."""
    if preferred:
        for key, icon, label in VARIANTS:
            if key == preferred:
                target_prefix = f"{icon} {label}:"
                for opt in opts:
                    if opt.startswith(target_prefix):
                        return opt
    return opts[0]  # Automatisch


# ---------------------------------------------------------------------------
# Build the form grouped by body part
# ---------------------------------------------------------------------------
changes: dict = {}  # muscle → {enabled, movements}

for body_part_label, muscles_in_part in BODY_PARTS:
    # Only show body parts that have at least one muscle in the catalog
    relevant_muscles = [m for m in muscles_in_part if m in muscle_exercises]
    if not relevant_muscles:
        continue

    st.markdown(f'<div class="bodypart-header">{body_part_label}</div>', unsafe_allow_html=True)

    for muscle_name in relevant_muscles:
        movements = muscle_exercises[muscle_name]
        saved_mcfg = muscle_cfg.get(muscle_name, {})
        is_enabled = saved_mcfg.get("enabled", False)

        with st.expander(f"{'✅' if is_enabled else '❌'}  {muscle_name}", expanded=False):
            enabled_key = f"ena_{muscle_name}"
            enabled = st.checkbox(
                "Muskel aktiv",
                value=is_enabled,
                key=enabled_key,
            )
            changes[muscle_name] = {"enabled": enabled, "movements": {}}

            if not enabled:
                st.caption("Dieser Muskel wird für diese Person deaktiviert.")
                continue

            st.caption("Wähle die bevorzugte Übungsvariante pro Bewegung:")
            saved_movs = saved_mcfg.get("movements", {})

            for movement, entry in movements.items():
                opts = _variant_options(entry)
                if len(opts) == 1:
                    # Only "Automatisch" available – nothing to choose
                    st.caption(f"**{movement}** — keine Varianten verfügbar")
                    continue

                current = _current_option(entry, saved_movs.get(movement), opts)

                sel = st.selectbox(
                    f"**{movement}**",
                    opts,
                    index=opts.index(current),
                    key=f"mov_{muscle_name}_{movement}",
                )
                variant = _option_to_variant(sel)
                if variant:
                    changes[muscle_name]["movements"][movement] = variant

# ---------------------------------------------------------------------------
# Save button
# ---------------------------------------------------------------------------
st.divider()

col_save, col_preview = st.columns([1, 3])

with col_save:
    if st.button("💾 Konfiguration speichern", type="primary", use_container_width=True):
        new_config = {"person": person_name, "muscles": {}}
        for muscle, mcfg in changes.items():
            new_config["muscles"][muscle] = {
                "enabled": mcfg["enabled"],
                "movements": mcfg["movements"],
            }
        save_person_config(person_name, new_config)
        st.success(f"✅ Konfiguration für **{person_name}** gespeichert!")
        st.balloons()

with col_preview:
    if st.button("🔍 Vorschau — aktive Muskeln", use_container_width=True):
        active = [m for m, c in changes.items() if c["enabled"]]
        disabled = [m for m, c in changes.items() if not c["enabled"]]
        st.write(f"**{len(active)} aktive Muskeln**, {len(disabled)} deaktiviert")
        if disabled:
            st.write("Deaktiviert: " + ", ".join(disabled))
