"""
pages/2_Zielgewichte.py
-----------------------
Streamlit page to compare current weights against target weights and edit targets.

Run from the project root:
    streamlit run backend/demo/app.py
"""
from __future__ import annotations

import copy
import pathlib
import sys

_DEMO_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(_DEMO_DIR))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from constants import BODY_PARTS
from exercises_dict import exercise_target_weight, format_exercise_label
from person_store import build_person_exercises, list_persons
from target_weight_store import load_target_weights, save_target_weights
from weight_store import load_weights

_VARIANT_META: dict[str, tuple[str, str]] = {
    "Maschine": ("Maschine_kg", "🏋️"),
    "HomeGym": ("HomeGym_kg", "🏠"),
    "Isometrisch": ("Isometrisch_kg", "🧘"),
}
_TARGET_TOLERANCE_KG = 0.25


def _body_part_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for body_part, muscles in BODY_PARTS:
        for muscle in muscles:
            lookup[muscle] = body_part
    return lookup


def _status_for_delta(target_kg: float, delta_kg: float) -> str:
    if target_kg <= 0:
        return "Kein Ziel"
    if abs(delta_kg) <= _TARGET_TOLERANCE_KG:
        return "Im Ziel"
    if delta_kg < 0:
        return "Unter Ziel"
    return "Über Ziel"


def _collect_rows(exercises: dict, weights: dict) -> list[dict]:
    body_part_by_muscle = _body_part_lookup()
    rows: list[dict] = []

    for muscle_name, movements in exercises.items():
        for movement, entry in movements.items():
            for variant_name, (weight_key, icon) in _VARIANT_META.items():
                exercise_value = entry.get(variant_name)
                if not exercise_value:
                    continue

                target_kg = float(exercise_target_weight(exercise_value) or 0.0)
                current_kg = float(
                    weights.get(muscle_name, {})
                    .get(movement, {})
                    .get(weight_key, 0.0)
                )
                delta_kg = current_kg - target_kg
                progress_pct = (current_kg / target_kg * 100.0) if target_kg > 0 else None

                rows.append(
                    {
                        "Körperbereich": body_part_by_muscle.get(muscle_name, "Sonstiges"),
                        "Muskel": muscle_name,
                        "Bewegung": movement,
                        "Variante": variant_name,
                        "Typ": f"{icon} {variant_name}",
                        "Übung": format_exercise_label(
                            exercise_value,
                            include_target_weight=False,
                            max_name_length=70,
                        ),
                        "Übungsname": format_exercise_label(
                            exercise_value,
                            include_target_weight=False,
                        ),
                        "Zielgewicht_kg": target_kg,
                        "Aktuell_kg": current_kg,
                        "Delta_kg": delta_kg,
                        "Fortschritt_pct": progress_pct,
                        "Status": _status_for_delta(target_kg, delta_kg),
                    }
                )

    return rows


def _row_key(row: dict) -> str:
    raw = "|".join(
        [
            row["Muskel"],
            row["Bewegung"],
            row["Variante"],
            row["Übungsname"],
        ]
    )
    return raw.replace(" ", "_").replace("|", "__").replace("/", "_")


st.set_page_config(
    page_title="🎯 Zielgewichte",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Zielgewichte vs. aktuelles Gewicht")
st.caption(
    "Diese Seite zeigt pro Übung den Vergleich zwischen gespeichertem Trainingsgewicht "
    "und Zielgewicht aus dem Übungskatalog."
)

with st.sidebar:
    st.header("👤 Person")
    persons = list_persons()
    selected_person = st.selectbox(
        "Person auswählen",
        persons,
        key="selected_person",
        label_visibility="collapsed",
    )

target_weights = load_target_weights(selected_person)
person_exercises = build_person_exercises(selected_person)
if not person_exercises:
    st.warning(
        "Für diese Person sind aktuell keine aktiven Muskeln oder Übungen konfiguriert."
    )
    st.stop()

weights = load_weights(selected_person, person_exercises)
rows = _collect_rows(person_exercises, weights)

if not rows:
    st.info("Keine Zielgewichte verfügbar.")
    st.stop()

df = pd.DataFrame(rows)
body_part_options = sorted(df["Körperbereich"].unique().tolist())

col_filter_1, col_filter_2, col_filter_3 = st.columns([2, 1, 1], gap="medium")
with col_filter_1:
    search = st.text_input(
        "🔍 Filtern nach Muskel, Bewegung oder Übung",
        placeholder="z. B. Bizeps, Schulterpresse, PushUps ...",
    ).strip()
with col_filter_2:
    selected_body_parts = st.multiselect(
        "Körperbereich",
        body_part_options,
        default=body_part_options,
    )
with col_filter_3:
    show_only_gaps = st.checkbox("Nur Abweichungen zeigen", value=False)

filtered_df = df[df["Körperbereich"].isin(selected_body_parts)].copy()

if search:
    search_lower = search.lower()
    filtered_df = filtered_df[
        filtered_df["Muskel"].str.lower().str.contains(search_lower)
        | filtered_df["Bewegung"].str.lower().str.contains(search_lower)
        | filtered_df["Übung"].str.lower().str.contains(search_lower)
    ]

if show_only_gaps:
    filtered_df = filtered_df[filtered_df["Status"] != "Im Ziel"]

if filtered_df.empty:
    st.info("Keine Einträge für die aktuellen Filter gefunden.")
    st.stop()

below_count = int((filtered_df["Status"] == "Unter Ziel").sum())
on_target_count = int((filtered_df["Status"] == "Im Ziel").sum())
above_count = int((filtered_df["Status"] == "Über Ziel").sum())
avg_progress = filtered_df["Fortschritt_pct"].dropna()
avg_progress_value = float(avg_progress.mean()) if not avg_progress.empty else None

col_metric_1, col_metric_2, col_metric_3, col_metric_4 = st.columns(4, gap="medium")
col_metric_1.metric("Verglichene Übungen", len(filtered_df))
col_metric_2.metric("Im Ziel", on_target_count)
col_metric_3.metric("Unter Ziel", below_count)
col_metric_4.metric(
    "Ø Zielerreichung",
    f"{avg_progress_value:.0f}%" if avg_progress_value is not None else "—",
)

chart_df = filtered_df.copy()
chart_df["Label"] = (
    chart_df["Muskel"].str.slice(0, 24)
    + " · "
    + chart_df["Bewegung"].str.slice(0, 18)
    + " · "
    + chart_df["Typ"].str.replace(r"^[^ ]+ ", "", regex=True)
)
chart_df = chart_df.sort_values(
    by=["Delta_kg", "Zielgewicht_kg"],
    ascending=[True, False],
).tail(18)

fig = go.Figure()
fig.add_trace(
    go.Bar(
        y=chart_df["Label"],
        x=chart_df["Zielgewicht_kg"],
        name="Zielgewicht",
        orientation="h",
        marker=dict(color="#F57C00", opacity=0.80),
        hovertemplate="%{y}<br>Ziel: <b>%{x:.1f} kg</b><extra></extra>",
    )
)
fig.add_trace(
    go.Bar(
        y=chart_df["Label"],
        x=chart_df["Aktuell_kg"],
        name="Aktuell",
        orientation="h",
        marker=dict(color="#1976D2", opacity=0.90),
        hovertemplate="%{y}<br>Aktuell: <b>%{x:.1f} kg</b><extra></extra>",
    )
)
fig.update_layout(
    barmode="group",
    height=max(380, len(chart_df) * 32),
    xaxis=dict(title="Gewicht (kg)", gridcolor="#e0e0e0", zeroline=False),
    yaxis=dict(autorange="reversed"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(l=10, r=20, t=10, b=40),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)

st.subheader("Vergleichsdiagramm")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Vergleichstabelle")
display_df = filtered_df.copy()
display_df["Zielgewicht"] = display_df["Zielgewicht_kg"].map(lambda value: f"{value:.1f} kg")
display_df["Aktuell"] = display_df["Aktuell_kg"].map(lambda value: f"{value:.1f} kg")
display_df["Delta"] = display_df["Delta_kg"].map(
    lambda value: f"{value:+.1f} kg"
)
display_df["Fortschritt"] = display_df["Fortschritt_pct"].map(
    lambda value: f"{value:.0f}%" if pd.notna(value) else "—"
)
display_df = display_df[
    [
        "Körperbereich",
        "Muskel",
        "Bewegung",
        "Typ",
        "Übung",
        "Zielgewicht",
        "Aktuell",
        "Delta",
        "Fortschritt",
        "Status",
    ]
].sort_values(by=["Körperbereich", "Muskel", "Bewegung", "Typ"])

st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Zielgewichte anpassen")
st.caption(
    "Passe die Zielgewichte per Textfeld an und speichere sie als personenspezifische "
    "Überschreibung. Dezimalzahlen mit Punkt oder Komma sind erlaubt."
)

editable_rows = filtered_df.sort_values(
    by=["Körperbereich", "Muskel", "Bewegung", "Variante"]
).to_dict("records")

with st.form("target_weight_edit_form"):
    current_body_part = None
    current_muscle = None
    for row in editable_rows:
        if row["Körperbereich"] != current_body_part:
            current_body_part = row["Körperbereich"]
            st.markdown(f"### {current_body_part}")
        if row["Muskel"] != current_muscle:
            current_muscle = row["Muskel"]
            st.markdown(f"**{current_muscle}**")

        row_key = _row_key(row)
        col_info, col_current, col_target = st.columns([4, 1, 1], gap="medium")
        with col_info:
            st.markdown(
                f"**{row['Bewegung']}** · {row['Typ']}<br><small>{row['Übung']}</small>",
                unsafe_allow_html=True,
            )
        with col_current:
            st.markdown("**Aktuell**")
            st.caption(f"{row['Aktuell_kg']:.1f} kg")
        with col_target:
            st.text_input(
                f"Zielgewicht {row['Übung']}",
                value=f"{row['Zielgewicht_kg']:.1f}",
                key=f"target_input_{row_key}",
                help="Neues Zielgewicht in kg",
            )

    submitted = st.form_submit_button("💾 Zielgewichte speichern", use_container_width=True)

if submitted:
    updated_target_weights = copy.deepcopy(target_weights)
    errors: list[str] = []

    for row in editable_rows:
        row_key = _row_key(row)
        raw_value = str(st.session_state.get(f"target_input_{row_key}", "")).strip().replace(",", ".")
        try:
            parsed_value = float(raw_value)
        except ValueError:
            errors.append(f"{row['Muskel']} / {row['Bewegung']} / {row['Typ']}: '{raw_value}' ist keine Zahl.")
            continue

        if parsed_value < 0:
            errors.append(f"{row['Muskel']} / {row['Bewegung']} / {row['Typ']}: Gewicht darf nicht negativ sein.")
            continue

        updated_target_weights.setdefault(row["Muskel"], {}).setdefault(row["Bewegung"], {}).setdefault(
            row["Variante"], {}
        )[row["Übungsname"]] = parsed_value

    if errors:
        st.error("Einige Zielgewichte konnten nicht gespeichert werden.")
        for error in errors[:8]:
            st.write(f"- {error}")
    else:
        save_target_weights(updated_target_weights, selected_person)
        st.success("✅ Zielgewichte gespeichert.")
        st.rerun()
