"""
app.py  –  Trainingsplan Manager (Streamlit)
--------------------------------------------
Full-featured Streamlit interface for the hypertrophy training schedule.
Run from the project root:

    streamlit run backend/demo/app.py

Three tabs:
  📅  Wochenplan        – weekly exercise schedule with progression preview
  ⚖️  Gewichte          – per-exercise weight editor (sliders + number inputs)
  📊  Progression       – bar chart and summary table
"""
from __future__ import annotations

import datetime
import pathlib
import sys

# ---------------------------------------------------------------------------
# Add demo directory to sys.path so local modules resolve regardless of cwd
# ---------------------------------------------------------------------------
_DEMO_DIR = pathlib.Path(__file__).resolve().parent
if str(_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(_DEMO_DIR))

import streamlit as st

from exercises_dict import muscle_exercises  # local copy
from schedule_logic import (  # local module
    DAY_TO_THEME,
    WEEK_DAYS,
    WEEKLY_PROGRESSION_RATE,
    WeightRow,
    build_weekly_plan,
    format_theme_label,
    generate_progression_chart,
)
from weight_store import load_weights, save_weights  # local module

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="💪 Trainingsplan Manager",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* Day card borders */
.day-card { border-left: 4px solid #1976D2; padding: 6px 10px; border-radius: 6px; margin-bottom: 6px; }
/* Type badges */
.badge-machine  { background:#1976D2; color:white; padding:1px 7px; border-radius:10px; font-size:.78em; }
.badge-home     { background:#388E3C; color:white; padding:1px 7px; border-radius:10px; font-size:.78em; }
.badge-iso      { background:#F57C00; color:white; padding:1px 7px; border-radius:10px; font-size:.78em; }
/* Weight chip */
.wchip { background:#e8f0fe; color:#1a237e; padding:1px 7px; border-radius:10px; font-size:.82em; font-weight:600; }
/* Section headers in weight editor */
.wtype-header { font-size:.88em; font-weight:700; color:#555; margin-bottom:2px; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state – load weights once per session
# ---------------------------------------------------------------------------
if "weights" not in st.session_state:
    st.session_state.weights = load_weights()

if "weights_saved" not in st.session_state:
    st.session_state.weights_saved = False


# ---------------------------------------------------------------------------
# Helper – sanitize keys (muscle names contain spaces, |, etc.)
# ---------------------------------------------------------------------------
def _skey(muscle: str, movement: str, wtype: str) -> str:
    """Stable, widget-safe key for a given muscle/movement/weight-type combo."""
    raw = f"{muscle}|{movement}|{wtype}"
    return raw.replace(" ", "_").replace("|", "__").replace("/", "_")


# ---------------------------------------------------------------------------
# Helper – save callback factories
# ---------------------------------------------------------------------------
def _make_save_cb(muscle: str, movement: str, wtype: str, widget_key: str):
    """on_change callback: write widget value → session_state.weights → JSON."""

    def _cb():
        val = float(st.session_state.get(widget_key, 0.0))
        st.session_state.weights.setdefault(muscle, {}).setdefault(movement, {})[wtype] = val
        save_weights(st.session_state.weights)
        st.session_state.weights_saved = True

    return _cb


# ---------------------------------------------------------------------------
# Build weekly plan (depends on current weights – rebuild on every rerun)
# ---------------------------------------------------------------------------
today: datetime.date = datetime.datetime.now(datetime.timezone.utc).date()
date_1w = today + datetime.timedelta(weeks=1)
date_1m = today + datetime.timedelta(days=30)

weekly_plan = build_weekly_plan(muscle_exercises, st.session_state.weights)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
col_title, col_date = st.columns([3, 1])
with col_title:
    st.title("💪 Trainingsplan Manager")
    st.caption(
        f"Hypertrophie +{WEEKLY_PROGRESSION_RATE * 100:.1f}% / Woche  •  "
        f"Stand {today.strftime('%d.%m.%Y')}"
    )
with col_date:
    st.markdown("###")
    if st.session_state.weights_saved:
        st.success("✅ Gespeichert", icon="💾")

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------
tab_plan, tab_weights, tab_progression = st.tabs(
    ["📅  Wochenplan", "⚖️  Gewichte verwalten", "📊  Progression"]
)


# ===========================================================================
# TAB 1 – WOCHENPLAN
# ===========================================================================
_TYPE_BADGE = {
    "Maschine": '<span class="badge-machine">Maschine</span>',
    "Dynamisch": '<span class="badge-home">HomeGym</span>',
    "Isometrisch": '<span class="badge-iso">Isometrisch</span>',
}

with tab_plan:
    st.subheader(f"📅  Wochenplan  –  {today.strftime('%d.%m.%Y')}")

    day_cols = st.columns(len(WEEK_DAYS), gap="small")
    for col, day_name in zip(day_cols, WEEK_DAYS):
        theme = DAY_TO_THEME[day_name]
        theme_label = format_theme_label(theme)
        exercises = weekly_plan.get(day_name, {})

        with col:
            st.markdown(f"**{day_name}**")
            st.markdown(f"*{theme_label}*")
            st.divider()

            if not exercises:
                st.info("–")
                continue

            for muscle, info in exercises.items():
                weight = info["Gewicht_kg"]
                w1 = info["Gewicht_1W"]
                w1m = info["Gewicht_1M"]
                badge = _TYPE_BADGE.get(info["Typ"], "")

                if weight > 0:
                    weight_html = (
                        f'<span class="wchip">{weight:.1f} kg</span> '
                        f"→ <small>+1W: <b>{w1:.1f}</b> | +1M: <b>{w1m:.1f}</b> kg</small>"
                    )
                else:
                    weight_html = "<small><i>Gewicht nicht gesetzt</i></small>"

                st.markdown(
                    f'<div class="day-card">'
                    f"<b>{muscle[:26]}</b><br>"
                    f"<small>{info['Übung'][:38]}</small><br>"
                    f"{badge}&nbsp;{weight_html}"
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ===========================================================================
# TAB 2 – GEWICHTE VERWALTEN
# ===========================================================================
with tab_weights:
    st.subheader("⚖️  Trainingsgewichte bearbeiten")
    st.caption(
        "Passe die Gewichte für jede Übung an. "
        "Änderungen werden **sofort gespeichert** (weights.json)."
    )

    # Search filter
    search = st.text_input(
        "🔍 Filtern (Muskel oder Übung)",
        placeholder="z. B. Bizeps, Beugung, Kabel …",
        key="weight_search",
    )

    for muscle_name, movements in muscle_exercises.items():
        # Apply search filter
        if search:
            s = search.lower()
            match = s in muscle_name.lower() or any(
                s in mv.lower()
                or s in str(entry.get("Maschine", "")).lower()
                or s in str(entry.get("HomeGym", "")).lower()
                for mv, entry in movements.items()
            )
            if not match:
                continue

        with st.expander(f"🦾  {muscle_name}", expanded=False):
            for movement, entry in movements.items():
                st.markdown(f"##### {movement}")

                machine_ex = entry.get("Maschine") or "—"
                home_ex = entry.get("HomeGym") or "—"
                iso_ex = entry.get("Isometrisch") or "—"
                if iso_ex in ("None", "none"):
                    iso_ex = "—"

                col_m, col_h, col_i = st.columns(3, gap="medium")

                # --- Maschine ---
                with col_m:
                    st.markdown(
                        '<p class="wtype-header">🏋️ Maschine</p>', unsafe_allow_html=True
                    )
                    st.caption(machine_ex[:50])
                    skey = _skey(muscle_name, movement, "Maschine_kg")
                    sl_key = f"sl_{skey}"
                    ni_key = f"ni_{skey}"
                    cur = float(
                        st.session_state.weights.get(muscle_name, {})
                        .get(movement, {})
                        .get("Maschine_kg", 0.0)
                    )
                    if sl_key not in st.session_state:
                        st.session_state[sl_key] = cur
                    if ni_key not in st.session_state:
                        st.session_state[ni_key] = cur
                    st.slider(
                        "Maschine kg",
                        0.0,
                        200.0,
                        step=0.5,
                        key=sl_key,
                        label_visibility="collapsed",
                        on_change=_make_save_cb(muscle_name, movement, "Maschine_kg", sl_key),
                    )
                    st.number_input(
                        "Maschine kg (genau)",
                        min_value=0.0,
                        max_value=500.0,
                        step=0.5,
                        key=ni_key,
                        label_visibility="collapsed",
                        on_change=_make_save_cb(muscle_name, movement, "Maschine_kg", ni_key),
                    )

                # --- HomeGym ---
                with col_h:
                    st.markdown(
                        '<p class="wtype-header">🏠 HomeGym</p>', unsafe_allow_html=True
                    )
                    st.caption(home_ex[:50])
                    skey = _skey(muscle_name, movement, "HomeGym_kg")
                    sl_key = f"sl_{skey}"
                    ni_key = f"ni_{skey}"
                    cur = float(
                        st.session_state.weights.get(muscle_name, {})
                        .get(movement, {})
                        .get("HomeGym_kg", 0.0)
                    )
                    if sl_key not in st.session_state:
                        st.session_state[sl_key] = cur
                    if ni_key not in st.session_state:
                        st.session_state[ni_key] = cur
                    st.slider(
                        "HomeGym kg",
                        0.0,
                        200.0,
                        step=0.5,
                        key=sl_key,
                        label_visibility="collapsed",
                        on_change=_make_save_cb(muscle_name, movement, "HomeGym_kg", sl_key),
                    )
                    st.number_input(
                        "HomeGym kg (genau)",
                        min_value=0.0,
                        max_value=500.0,
                        step=0.5,
                        key=ni_key,
                        label_visibility="collapsed",
                        on_change=_make_save_cb(muscle_name, movement, "HomeGym_kg", ni_key),
                    )

                # --- Isometrisch ---
                with col_i:
                    st.markdown(
                        '<p class="wtype-header">🧘 Isometrisch</p>', unsafe_allow_html=True
                    )
                    st.caption(iso_ex[:50])
                    skey = _skey(muscle_name, movement, "Isometrisch_kg")
                    sl_key = f"sl_{skey}"
                    ni_key = f"ni_{skey}"
                    cur = float(
                        st.session_state.weights.get(muscle_name, {})
                        .get(movement, {})
                        .get("Isometrisch_kg", 0.0)
                    )
                    if sl_key not in st.session_state:
                        st.session_state[sl_key] = cur
                    if ni_key not in st.session_state:
                        st.session_state[ni_key] = cur
                    st.slider(
                        "Isometrisch kg",
                        0.0,
                        200.0,
                        step=0.5,
                        key=sl_key,
                        label_visibility="collapsed",
                        on_change=_make_save_cb(
                            muscle_name, movement, "Isometrisch_kg", sl_key
                        ),
                    )
                    st.number_input(
                        "Isometrisch kg (genau)",
                        min_value=0.0,
                        max_value=500.0,
                        step=0.5,
                        key=ni_key,
                        label_visibility="collapsed",
                        on_change=_make_save_cb(
                            muscle_name, movement, "Isometrisch_kg", ni_key
                        ),
                    )

                st.divider()


# ===========================================================================
# TAB 3 – PROGRESSION
# ===========================================================================
with tab_progression:
    st.subheader("📊  Trainingsgewicht-Progression")
    st.caption(
        f"Jetzt ({today.strftime('%d.%m.%Y')})  →  "
        f"+1 Woche ({date_1w.strftime('%d.%m.%Y')})  →  "
        f"+1 Monat ({date_1m.strftime('%d.%m.%Y')})"
    )

    # Collect unique muscles from weekly plan (first occurrence wins)
    seen: set[str] = set()
    chart_rows: list[WeightRow] = []
    table_rows: list[dict] = []

    for day_name in WEEK_DAYS:
        for muscle, info in weekly_plan.get(day_name, {}).items():
            if muscle in seen:
                continue
            seen.add(muscle)
            c = info["Gewicht_kg"]
            w = info["Gewicht_1W"]
            m = info["Gewicht_1M"]
            chart_rows.append((muscle, info["Übung"], c, w, m))
            table_rows.append(
                {
                    "Muskel": muscle,
                    "Übung": info["Übung"][:55],
                    "Typ": info["Typ"],
                    f"Jetzt ({today.strftime('%d.%m')})": f"{c:.1f} kg" if c > 0 else "—",
                    f"+1 Woche ({date_1w.strftime('%d.%m')})": f"{w:.1f} kg" if c > 0 else "—",
                    f"+1 Monat ({date_1m.strftime('%d.%m')})": f"{m:.1f} kg" if c > 0 else "—",
                }
            )

    # Chart
    fig = generate_progression_chart(chart_rows, today)
    if fig is not None:
        st.pyplot(fig)
    else:
        st.warning(
            "⚠️ Keine Gewichte gesetzt – bitte unter **⚖️ Gewichte verwalten** eintragen.",
            icon="⚠️",
        )

    st.divider()

    # Summary table
    st.subheader("Übersichtstabelle")
    if table_rows:
        import pandas as pd  # noqa: PLC0415 (local import keeps startup fast)

        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
