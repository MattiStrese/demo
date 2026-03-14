"""
app.py  –  Trainingsplan Manager (Streamlit)
--------------------------------------------
Full-featured Streamlit interface for the hypertrophy training schedule.
Run from the project root:

    streamlit run backend/demo/app.py

Five tabs:
  📅  Wochenplan        – weekly exercise schedule with progression preview
  💪  Beugung           – flexion exercises grouped by body part + weight sliders
  📐  Streckung         – extension exercises grouped by body part + weight sliders
  🔄  Rotation & mehr   – rotation/secondary exercises grouped by body part + weight sliders
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
/* Body-part section header */
.bodypart-header { font-size:1.05em; font-weight:700; color:#1976D2; border-bottom: 2px solid #1976D2; padding-bottom:3px; margin-top:12px; margin-bottom:6px; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Body-part → muscles mapping (anatomical order: head → feet)
# ---------------------------------------------------------------------------
BODY_PARTS: list[tuple[str, list[str]]] = [
    ("🧠 Nacken", [
        "Sternocleidomastoideus | Splenius Capitis",
    ]),
    ("🫁 Brust", [
        "Pectoralis Clavicularis | Sternalis",
    ]),
    ("🦾 Schulter", [
        "Rotatorenmanschette innen",
        "Rotatorenmanschette aussen",
        "Deltamuskel Vordere Faser",
        "Deltamuskel Mittlere Faser",
        "Deltamuskel Hintere Faser",
        "Trapezius Elevation",
        "Trapezius Retraktion",
        "Trapezius Depression",
    ]),
    ("🔙 Rücken", [
        "Latissimus Dorsi",
        "Serratus Anterior",
    ]),
    ("💪 Oberarme", [
        "Biceps Brachii",
        "Triceps Longum | Lateraler Kopf | Medialer Kopf",
    ]),
    ("🖐 Unterarme", [
        "Finger Flexion",
        "Finger Extension",
        "Handgelenk Flexion",
        "Handgelenk Strecker",
        "Unterarm Supinatoren | Pronatoren",
    ]),
    ("🔥 Core", [
        "Rectus Abdominis",
        "Transversus Abdominis",
        "Obliquus",
        "Erector Spinae",
    ]),
    ("🍑 Hüfte", [
        "Iliopsoas",
        "Gluteus Maximus",
        "Gluteus Medius | Minimus",
        "Gluteus medius (anteriore Fasern)",
        "Adductor Longus | Magnus | Gracilis",
        "Hüft-Außenrotatoren",
    ]),
    ("🦵 Oberschenkel", [
        "Hamstrings",
        "Quadrizeps",
    ]),
    ("🦿 Unterschenkel", [
        "Gastrocnemius | Soleus",
        "Tibialis Anterior",
        "Tibialis Posterior",
    ]),
    ("🦶 Fuß", [
        "Flexor Digitorum Brevis",
        "Extensor Digitorum Brevis",
    ]),
]

# Movement sets per theme day
FLEXION_MOVEMENTS: set[str] = {"Beugung"}
EXTENSION_MOVEMENTS: set[str] = {"Streckung"}
ROTATION_MOVEMENTS: set[str] = {
    "Rotation", "Lateralflexion", "Adduktion", "Abduktion",
    "Supination", "Pronation", "Elevation", "Depression",
    "Protraktion", "Anti-Extension", "Anti-Rotation", "Inversion",
}

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
# Helper – render 3-column weight slider block for one exercise movement
# ---------------------------------------------------------------------------
def _fmt_exercise(val) -> str:
    """Return display string for an exercise name, handling None/empty."""
    if val in (None, "None", "none", "-", ""):
        return "—"
    return str(val)[:55]


def _render_weight_sliders(muscle_name: str, movement: str, entry: dict) -> None:
    """Renders the 3-column Maschine / HomeGym / Isometrisch slider block."""
    machine_ex = _fmt_exercise(entry.get("Maschine"))
    home_ex = _fmt_exercise(entry.get("HomeGym"))
    iso_ex = _fmt_exercise(entry.get("Isometrisch"))

    col_m, col_h, col_i = st.columns(3, gap="medium")

    for col, icon, label, wtype, exercise_text in [
        (col_m, "🏋️", "Maschine", "Maschine_kg", machine_ex),
        (col_h, "🏠", "HomeGym", "HomeGym_kg", home_ex),
        (col_i, "🧘", "Isometrisch", "Isometrisch_kg", iso_ex),
    ]:
        with col:
            st.markdown(
                f'<p class="wtype-header">{icon} {label}</p>', unsafe_allow_html=True
            )
            st.caption(exercise_text)
            skey = _skey(muscle_name, movement, wtype)
            sl_key = f"sl_{skey}"
            ni_key = f"ni_{skey}"
            cur = float(
                st.session_state.weights.get(muscle_name, {})
                .get(movement, {})
                .get(wtype, 0.0)
            )
            if sl_key not in st.session_state:
                st.session_state[sl_key] = cur
            if ni_key not in st.session_state:
                st.session_state[ni_key] = cur
            st.slider(
                f"{label} kg",
                0.0, 200.0, step=0.5,
                key=sl_key,
                label_visibility="collapsed",
                on_change=_make_save_cb(muscle_name, movement, wtype, sl_key),
            )
            st.number_input(
                f"{label} kg (genau)",
                min_value=0.0, max_value=500.0, step=0.5,
                key=ni_key,
                label_visibility="collapsed",
                on_change=_make_save_cb(muscle_name, movement, wtype, ni_key),
            )


# ---------------------------------------------------------------------------
# Helper – render a full theme tab (body parts → muscles → sliders)
# ---------------------------------------------------------------------------
def _render_theme_tab(theme_movements: set[str], tab_title: str, search_key: str) -> None:
    """Render exercises for one theme, grouped by body part (head → feet)."""
    st.subheader(tab_title)
    st.caption(
        "Passe die Gewichte für jede Übung an. "
        "Änderungen werden **sofort gespeichert** (weights.json)."
    )

    search = st.text_input(
        "🔍 Filtern (Muskel oder Übung)",
        placeholder="z. B. Bizeps, Schulter …",
        key=f"search_{search_key}",
    )

    any_shown = False
    for body_part_label, muscles_in_part in BODY_PARTS:
        # Collect muscles in this body part that have relevant movements
        relevant: list[tuple[str, list[str]]] = []
        for muscle_name in muscles_in_part:
            if muscle_name not in muscle_exercises:
                continue
            movs = [mv for mv in muscle_exercises[muscle_name] if mv in theme_movements]
            if not movs:
                continue
            # Apply search filter
            if search:
                s = search.lower()
                match = s in muscle_name.lower() or any(
                    s in mv.lower()
                    or s in str(muscle_exercises[muscle_name][mv].get("Maschine", "")).lower()
                    or s in str(muscle_exercises[muscle_name][mv].get("HomeGym", "")).lower()
                    for mv in movs
                )
                if not match:
                    continue
            relevant.append((muscle_name, movs))

        if not relevant:
            continue

        any_shown = True
        st.markdown(
            f'<div class="bodypart-header">{body_part_label}</div>',
            unsafe_allow_html=True,
        )

        for muscle_name, movements in relevant:
            with st.expander(f"🦾  {muscle_name}", expanded=False):
                for i, movement in enumerate(movements):
                    entry = muscle_exercises[muscle_name][movement]
                    st.markdown(f"##### {movement}")
                    _render_weight_sliders(muscle_name, movement, entry)
                    if i < len(movements) - 1:
                        st.divider()

    if not any_shown:
        st.info("Keine Übungen gefunden.")


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
tab_plan, tab_flexion, tab_extension, tab_rotation, tab_progression = st.tabs(
    [
        "📅  Wochenplan",
        "💪  Beugung",
        "📐  Streckung",
        "🔄  Rotation & mehr",
        "📊  Progression",
    ]
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
# TAB 2 – BEUGUNG (FLEXION)
# ===========================================================================
with tab_flexion:
    _render_theme_tab(FLEXION_MOVEMENTS, "💪  Beugung (Flexion)", "flexion")


# ===========================================================================
# TAB 3 – STRECKUNG (EXTENSION)
# ===========================================================================
with tab_extension:
    _render_theme_tab(EXTENSION_MOVEMENTS, "📐  Streckung (Extension)", "extension")


# ===========================================================================
# TAB 4 – ROTATION & MEHR
# ===========================================================================
with tab_rotation:
    _render_theme_tab(ROTATION_MOVEMENTS, "🔄  Rotation & mehr", "rotation")


# ===========================================================================
# TAB 5 – PROGRESSION
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
    import plotly.graph_objects as go  # noqa: PLC0415

    weighted = [(m, e, c, w, mo) for m, e, c, w, mo in chart_rows if c > 0]

    if weighted:
        labels   = [m[:40] for m, *_ in weighted]
        now_vals = [c  for _, _, c, _, _  in weighted]
        w1_vals  = [w  for _, _, _, w, _  in weighted]
        m1_vals  = [mo for _, _, _, _, mo in weighted]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=labels, x=m1_vals,
            name=f"+1 Monat  ({date_1m.strftime('%d.%m.%Y')})",
            orientation="h",
            marker=dict(color="#F57C00", opacity=0.75),
            hovertemplate="%{y}<br>+1 Monat: <b>%{x:.1f} kg</b><extra></extra>",
        ))
        fig.add_trace(go.Bar(
            y=labels, x=w1_vals,
            name=f"+1 Woche  ({date_1w.strftime('%d.%m.%Y')})",
            orientation="h",
            marker=dict(color="#388E3C", opacity=0.85),
            hovertemplate="%{y}<br>+1 Woche: <b>%{x:.1f} kg</b><extra></extra>",
        ))
        fig.add_trace(go.Bar(
            y=labels, x=now_vals,
            name=f"Heute  ({today.strftime('%d.%m.%Y')})",
            orientation="h",
            marker=dict(color="#1976D2"),
            hovertemplate="%{y}<br>Heute: <b>%{x:.1f} kg</b><extra></extra>",
        ))

        fig.update_layout(
            barmode="overlay",
            height=max(420, len(labels) * 36),
            xaxis=dict(title="Gewicht (kg)", gridcolor="#e0e0e0", zeroline=False),
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
            legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
            margin=dict(l=10, r=20, t=10, b=40),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hoverlabel=dict(bgcolor="white", font_size=13),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(
            "⚠️ Keine Gewichte gesetzt – bitte unter **💪 Beugung**, **📐 Streckung** oder **🔄 Rotation** eintragen.",
            icon="⚠️",
        )

    st.divider()

    # Summary table
    st.subheader("Übersichtstabelle")
    if table_rows:
        import pandas as pd  # noqa: PLC0415 (local import keeps startup fast)

        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
