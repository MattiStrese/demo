"""
sinks_goldmines.py  –  Passive Income Stream Visualizer (Streamlit)
--------------------------------------------------------------------
Visualisiere mehrere passive Einkommensquellen über die Zeit.
Einnahmen und Ausgaben werden persistent in finance_data.json gespeichert.

Starten:
    streamlit run sinks_goldmines.py
"""
from __future__ import annotations

import json
import pathlib

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Persistent storage helpers ───────────────────────────────────────────────
_DATA_FILE = pathlib.Path(__file__).resolve().parent / "finance_data.json"

_DEFAULT_SOURCES = [
    {"name": "Dividenden-Portfolio",     "yearly": 2400.0,  "growth_pct": 5.0,  "color": "#4CAF50"},
    {"name": "Mieteinnahmen",            "yearly": 9600.0,  "growth_pct": 3.0,  "color": "#2196F3"},
    {"name": "Blog / Content",           "yearly":  600.0,  "growth_pct": 20.0, "color": "#FF9800"},
    {"name": "Aktives Einkommen (Lohn)", "yearly": 48000.0, "growth_pct": 2.0,  "color": "#E91E63"},
]

_DEFAULT_EXPENSES = [
    {"name": "Miete",            "yearly": 9600.0,  "growth_pct": 2.0, "color": "#F44336"},
    {"name": "Versicherungen",   "yearly": 1800.0,  "growth_pct": 3.0, "color": "#E91E63"},
    {"name": "Lebensmittel",     "yearly": 3600.0,  "growth_pct": 3.5, "color": "#9C27B0"},
    {"name": "Shopping",         "yearly": 1200.0,  "growth_pct": 2.0, "color": "#FF5722"},
    {"name": "Amazon",           "yearly": 4000.0,  "growth_pct": 3.0, "color": "#795548"},
    {"name": "Strom",            "yearly":  900.0,  "growth_pct": 4.0, "color": "#607D8B"},
    {"name": "Wasser",           "yearly":  300.0,  "growth_pct": 2.5, "color": "#D32F2F"},
    {"name": "Müll",             "yearly":  180.0,  "growth_pct": 2.0, "color": "#C2185B"},
    {"name": "Risikorücklage",   "yearly": 2000.0,  "growth_pct": 0.0, "color": "#7B1FA2"},
    {"name": "Steuerberater",    "yearly": 1000.0,  "growth_pct": 2.0, "color": "#BF360C"},
    {"name": "Steuernachzahlung","yearly": 1000.0,  "growth_pct": 3.0, "color": "#4E342E"},
    {"name": "KfZ Kosten",       "yearly": 2000.0,  "growth_pct": 3.0, "color": "#37474F"},
]


def _load_data() -> dict:
    """Load sources, expenses and years from JSON; fall back to defaults."""
    if _DATA_FILE.exists():
        try:
            return json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"sources": _DEFAULT_SOURCES, "expenses": _DEFAULT_EXPENSES, "years": 10}


def _save_data() -> None:
    """Persist current session state to JSON."""
    payload = {
        "sources":  st.session_state.sources,
        "expenses": st.session_state.expenses,
        "years":    st.session_state.get("years_slider", 10),
    }
    _DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert a 6-digit hex color string to an rgba() string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="💰 Passive Einkommensströme",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Passive Einkommensströme – Visualisierung")
st.caption("Füge deine Einkommensquellen hinzu, wähle den Zeithorizont und beobachte, wie deine Ströme wachsen.")

# ── Session state: load from JSON or fall back to defaults ───────────────────
if "sources" not in st.session_state:
    _persisted = _load_data()
    st.session_state.sources  = _persisted["sources"]
    st.session_state.expenses = _persisted["expenses"]
    st.session_state.years_slider = int(_persisted.get("years", 10))

PALETTE = [
    "#4CAF50", "#2196F3", "#FF9800", "#E91E63", "#9C27B0",
    "#00BCD4", "#FF5722", "#8BC34A", "#FFC107", "#3F51B5",
]

EXP_PALETTE = [
    "#F44336", "#E91E63", "#9C27B0", "#FF5722", "#795548",
    "#607D8B", "#D32F2F", "#C2185B", "#7B1FA2", "#BF360C",
]

# ── Sidebar: add / manage sources ────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Einkommensquellen")

    indices_to_delete = []
    for i, src in enumerate(st.session_state.sources):
        with st.expander(f"{'🟢' if src['yearly'] > 0 else '⚪'} {src['name'] or f'Quelle {i+1}'}", expanded=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                src["name"] = st.text_input("Name", value=src["name"], key=f"name_{i}")
            with col2:
                st.write("")
                st.write("")
                if st.button("🗑️", key=f"del_{i}", help="Quelle entfernen"):
                    indices_to_delete.append(i)

            src["yearly"] = st.number_input(
                "Jährliches Einkommen (€)", min_value=0.0, max_value=12_000_000.0,
                value=float(src["yearly"]), step=100.0, key=f"yearly_{i}",
            )
            src["growth_pct"] = st.slider(
                "Jährliches Wachstum (%)", min_value=0.0, max_value=100.0,
                value=float(src["growth_pct"]), step=0.5, key=f"growth_{i}",
            )
            src["color"] = PALETTE[i % len(PALETTE)]

    for idx in reversed(indices_to_delete):
        st.session_state.sources.pop(idx)
    if indices_to_delete:
        _save_data()
        st.rerun()

    st.divider()
    if st.button("➕ Einkommensquelle hinzufügen", use_container_width=True):
        st.session_state.sources.append({
            "name": f"Quelle {len(st.session_state.sources) + 1}",
            "yearly": 1200.0,
            "growth_pct": 5.0,
            "color": PALETTE[len(st.session_state.sources) % len(PALETTE)],
        })
        _save_data()
        st.rerun()

    st.divider()
    st.subheader("⏱️ Zeithorizont")
    years = st.slider("Prognosezeitraum (Jahre)", min_value=1, max_value=40,
                      value=st.session_state.get("years_slider", 10), step=1, key="years_slider")

    st.divider()
    st.header("💸 Ausgaben")

    exp_to_delete = []
    for i, exp in enumerate(st.session_state.expenses):
        with st.expander(f"{'🔴' if exp['yearly'] > 0 else '⚪'} {exp['name'] or f'Ausgabe {i+1}'}", expanded=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                exp["name"] = st.text_input("Name", value=exp["name"], key=f"exp_name_{i}")
            with col2:
                st.write("")
                st.write("")
                if st.button("🗑️", key=f"exp_del_{i}", help="Ausgabe entfernen"):
                    exp_to_delete.append(i)

            exp["yearly"] = st.number_input(
                "Jährliche Ausgabe (€)", min_value=0.0, max_value=12_000_000.0,
                value=float(exp["yearly"]), step=100.0, key=f"exp_yearly_{i}",
            )
            exp["growth_pct"] = st.slider(
                "Jährl. Kostensteigerung (%)", min_value=0.0, max_value=30.0,
                value=float(exp["growth_pct"]), step=0.5, key=f"exp_growth_{i}",
            )
            exp["color"] = EXP_PALETTE[i % len(EXP_PALETTE)]

    for idx in reversed(exp_to_delete):
        st.session_state.expenses.pop(idx)
    if exp_to_delete:
        _save_data()
        st.rerun()

    st.divider()
    if st.button("➕ Ausgabe hinzufügen", use_container_width=True):
        st.session_state.expenses.append({
            "name": f"Ausgabe {len(st.session_state.expenses) + 1}",
            "yearly": 600.0,
            "growth_pct": 2.0,
            "color": EXP_PALETTE[len(st.session_state.expenses) % len(EXP_PALETTE)],
        })
        _save_data()
        st.rerun()

# ── Persist any inline edits (number inputs / sliders changed this run) ──────
_save_data()

# ── Data computation ──────────────────────────────────────────────────────────
sources = [s for s in st.session_state.sources if s["yearly"] > 0 and s["name"].strip()]

months_total = years * 12
month_index  = np.arange(months_total)           # 0 … N-1
year_frac    = month_index / 12.0

rows = []
for src in sources:
    m0     = src["yearly"] / 12.0
    g      = src["growth_pct"] / 100.0
    monthly_vals = m0 * (1 + g) ** year_frac     # continuous yearly compounding per month
    for mi, mv in enumerate(monthly_vals):
        rows.append({
            "month_idx":  mi,
            "year":       mi // 12 + 1,
            "month_label": pd.Period(freq="M", ordinal=mi).strftime("%b %Y") if mi < 2400 else f"M{mi}",
            "source":     src["name"],
            "monthly":    mv,
            "daily":      mv / 30.44,
            "color":      src["color"],
        })

df = pd.DataFrame(rows)

if df.empty:
    st.info("👈 Füge mindestens eine Einkommensquelle in der Seitenleiste hinzu, um zu starten.")
    st.stop()

# Yearly aggregates
df_yearly = (
    df.groupby(["year", "source", "color"], as_index=False)
    .agg(annual=("monthly", "sum"), monthly_avg=("monthly", "mean"), daily_avg=("daily", "mean"))
)

# Monthly totals across sources
df_monthly_total = df.groupby("month_idx", as_index=False).agg(
    monthly_total=("monthly", "sum"),
    daily_total=("daily", "sum"),
)
df_monthly_total["year"]  = df_monthly_total["month_idx"] // 12 + 1
df_monthly_total["label"] = "Monat " + (df_monthly_total["month_idx"] + 1).astype(str)

# ── Expense computation ───────────────────────────────────────────────────────
expenses = [e for e in st.session_state.expenses if e["yearly"] > 0 and e["name"].strip()]

exp_rows = []
for exp in expenses:
    m0 = exp["yearly"] / 12.0
    g  = exp["growth_pct"] / 100.0
    monthly_vals = m0 * (1 + g) ** year_frac
    for mi, mv in enumerate(monthly_vals):
        exp_rows.append({
            "month_idx": mi,
            "year":      mi // 12 + 1,
            "expense":   exp["name"],
            "monthly":   mv,
            "daily":     mv / 30.44,
            "color":     exp["color"],
        })

df_exp = pd.DataFrame(exp_rows) if exp_rows else pd.DataFrame(
    columns=["month_idx","year","expense","monthly","daily","color"])

df_exp_yearly = (
    df_exp.groupby(["year", "expense", "color"], as_index=False)
    .agg(annual=("monthly", "sum"), monthly_avg=("monthly", "mean"))
) if not df_exp.empty else pd.DataFrame()

df_exp_monthly_total = df_exp.groupby("month_idx", as_index=False).agg(
    monthly_total=("monthly", "sum"),
    daily_total=("daily", "sum"),
) if not df_exp.empty else pd.DataFrame({"month_idx": month_index, "monthly_total": 0.0, "daily_total": 0.0})

# ── KPI strip ────────────────────────────────────────────────────────────────
first_month_total = df[df["month_idx"] == 0]["monthly"].sum()
last_month_total  = df[df["month_idx"] == months_total - 1]["monthly"].sum()
total_earned      = df_monthly_total["monthly_total"].sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("💵 Monatlich (Start)", f"€{first_month_total:,.0f}")
k2.metric("🚀 Monatlich in Jahr " + str(years), f"€{last_month_total:,.0f}",
          delta=f"+{last_month_total - first_month_total:,.0f} vs. Start")
k3.metric("☀️ Täglich (Jahr " + str(years) + ")", f"€{last_month_total/30.44:,.1f}")
k4.metric("🏦 Gesamt über " + str(years) + " Jahre", f"€{total_earned:,.0f}")

st.divider()

# ── Tab layout ────────────────────────────────────────────────────────────────
tab_yearly, tab_monthly, tab_daily, tab_breakdown = st.tabs(
    ["📅 Jährlich", "📆 Monatlich", "☀️ Täglich", "🥧 Aufschlüsselung"]
)

# ─── YEARLY TAB ───────────────────────────────────────────────────────────────
with tab_yearly:
    st.subheader("Jährliches Einkommen je Quelle")
    fig_y = go.Figure()
    for src in sources:
        d = df_yearly[df_yearly["source"] == src["name"]]
        fig_y.add_trace(go.Bar(
            x=d["year"], y=d["annual"],
            name=src["name"], marker_color=src["color"],
            customdata=np.stack([d["monthly_avg"], d["daily_avg"]], axis=-1),
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "Jahr %{x}<br>"
                "Jährlich:       €%{y:,.0f}<br>"
                "Ø Monatlich:    €%{customdata[0]:,.0f}<br>"
                "Ø Täglich:      €%{customdata[1]:,.2f}<extra></extra>"
            ),
        ))
    fig_y.update_layout(
        barmode="stack",
        xaxis_title="Jahr",
        yaxis_title="Jährliches Einkommen (€)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=450,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        xaxis=dict(dtick=1),
    )
    st.plotly_chart(fig_y, use_container_width=True)

    st.subheader("Jährliches Wachstum je Quelle")
    n = len(sources)
    cols_y = st.columns(min(n, 4))
    for ci, src in enumerate(sources):
        d = df_yearly[df_yearly["source"] == src["name"]]
        fig_s = go.Figure(go.Scatter(
            x=d["year"], y=d["annual"],
            fill="tozeroy", line_color=src["color"],
            fillcolor=hex_to_rgba(src["color"], 0.27),
        ))
        fig_s.update_layout(
            height=140, margin=dict(l=0, r=0, t=24, b=0),
            title=dict(text=src["name"], font_size=12, x=0.5),
            xaxis=dict(showticklabels=True, tickfont_size=9),
            yaxis=dict(showticklabels=True, tickprefix="€", tickfont_size=9),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            showlegend=False,
        )
        with cols_y[ci % 4]:
            st.plotly_chart(fig_s, use_container_width=True)

# ─── MONTHLY TAB ──────────────────────────────────────────────────────────────
with tab_monthly:
    st.subheader("Monatlicher Einkommensstrom")

    fig_m = make_subplots(rows=2, cols=1, shared_xaxes=True,
                          row_heights=[0.65, 0.35],
                          subplot_titles=("Gestapeltes Monatseinkommen", "Monat-für-Monat-Wachstum"))

    for src in sources:
        d = df[df["source"] == src["name"]].sort_values("month_idx")
        fig_m.add_trace(go.Scatter(
            x=d["month_idx"] + 1, y=d["monthly"],
            name=src["name"], stackgroup="one",
            fillcolor=hex_to_rgba(src["color"], 0.73),
            line_color=src["color"],
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "Monat %{x}<br>"
                "Monatlich: €%{y:,.0f}<extra></extra>"
            ),
        ), row=1, col=1)

    # Gesamtlinie
    fig_m.add_trace(go.Scatter(
        x=df_monthly_total["month_idx"] + 1,
        y=df_monthly_total["monthly_total"],
        name="Gesamt", line=dict(color="white", width=2, dash="dot"),
        hovertemplate="Monat %{x}<br>Gesamt: €%{y:,.0f}<extra></extra>",
    ), row=1, col=1)

    # MoM-Wachstum %
    mom = df_monthly_total["monthly_total"].pct_change() * 100
    fig_m.add_trace(go.Bar(
        x=df_monthly_total["month_idx"] + 1, y=mom,
        name="MoM %", marker_color="#FFD700", showlegend=False,
        hovertemplate="Monat %{x}<br>Wachstum: %{y:.3f}%<extra></extra>",
    ), row=2, col=1)

    # Jahrestrennlinien
    for yr in range(1, years):
        fig_m.add_vline(x=yr * 12 + 0.5, line_dash="dash", line_color="rgba(200,200,200,0.3)", row="all")

    fig_m.update_layout(
        height=520,
        xaxis2_title="Monat",
        yaxis_title="Monatliches Einkommen (€)",
        yaxis2_title="MoM-Wachstum (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_m, use_container_width=True)

# ─── DAILY TAB ────────────────────────────────────────────────────────────────
with tab_daily:
    st.subheader("Tägliches passives Einkommen")

    # Gauges
    today_daily = first_month_total / 30.44
    future_daily = last_month_total / 30.44

    g1, g2 = st.columns(2)
    with g1:
        fig_gauge1 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=today_daily,
            title={"text": "Tägliches Einkommen heute (€/Tag)", "font": {"size": 16}},
            delta={"reference": 0, "valueformat": ".2f"},
            gauge={
                "axis": {"range": [0, max(future_daily * 1.1, 10)]},
                "bar": {"color": "#4CAF50"},
                "steps": [
                    {"range": [0, future_daily * 0.33], "color": "#1a3d1a"},
                    {"range": [future_daily * 0.33, future_daily * 0.66], "color": "#2d5a2d"},
                    {"range": [future_daily * 0.66, future_daily], "color": "#3d7a3d"},
                ],
                "threshold": {"line": {"color": "gold", "width": 3}, "value": future_daily},
            },
            number={"suffix": " €", "valueformat": ".2f"},
        ))
        fig_gauge1.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0"))
        st.plotly_chart(fig_gauge1, use_container_width=True)

    with g2:
        fig_gauge2 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=future_daily,
            title={"text": f"Tägliches Einkommen in Jahr {years} (€/Tag)", "font": {"size": 16}},
            delta={"reference": today_daily, "valueformat": ".2f", "relative": False},
            gauge={
                "axis": {"range": [0, max(future_daily * 1.1, 10)]},
                "bar": {"color": "#FF9800"},
                "steps": [
                    {"range": [0, future_daily * 0.33], "color": "#3d2a00"},
                    {"range": [future_daily * 0.33, future_daily * 0.66], "color": "#5a3d00"},
                    {"range": [future_daily * 0.66, future_daily], "color": "#7a5200"},
                ],
                "threshold": {"line": {"color": "gold", "width": 3}, "value": today_daily},
            },
            number={"suffix": " €", "valueformat": ".2f"},
        ))
        fig_gauge2.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0"))
        st.plotly_chart(fig_gauge2, use_container_width=True)

    # Daily income timeline
    df_daily = df.groupby("month_idx", as_index=False).agg(daily_total=("daily", "sum"))
    fig_d = go.Figure()
    fig_d.add_trace(go.Scatter(
        x=df_daily["month_idx"] + 1,
        y=df_daily["daily_total"],
        fill="tozeroy",
        fillcolor="rgba(255,193,7,0.2)",
        line=dict(color="#FFC107", width=2),
        name="Tägliches Einkommen",
        hovertemplate="Monat %{x}<br>€%{y:.2f} / Tag<extra></extra>",
    ))
    # Annotate every year
    for yr in range(1, years + 1):
        mi = yr * 12 - 1
        if mi < len(df_daily):
            val = df_daily.loc[df_daily["month_idx"] == mi, "daily_total"].values
            if len(val):
                fig_d.add_annotation(
                    x=mi + 1, y=val[0],
                    text=f"Jahr {yr}<br>€{val[0]:.1f}/Tag",
                    showarrow=True, arrowhead=2, arrowcolor="#FFC107",
                    font=dict(size=9, color="#FFC107"),
                    bgcolor="rgba(0,0,0,0.5)",
                    bordercolor="#FFC107",
                )
    for yr in range(1, years):
        fig_d.add_vline(x=yr * 12 + 0.5, line_dash="dash", line_color="rgba(200,200,200,0.2)")

    fig_d.update_layout(
        height=380,
        xaxis_title="Monat",
        yaxis_title="€ pro Tag",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        showlegend=False,
    )
    st.plotly_chart(fig_d, use_container_width=True)

    st.subheader(f"Quellenübersicht in Jahr {years}")
    last_df = df[df["month_idx"] == months_total - 1][["source", "monthly", "daily"]].copy()
    last_df.columns = ["Quelle", "Monatlich (€)", "Täglich (€)"]
    last_df = last_df.sort_values("Monatlich (€)", ascending=False)
    last_df["Anteil (%)"] = (last_df["Monatlich (€)"] / last_df["Monatlich (€)"].sum() * 100).round(1)
    last_df["Monatlich (€)"] = last_df["Monatlich (€)"].map("€{:,.0f}".format)
    last_df["Täglich (€)"]   = last_df["Täglich (€)"].map("€{:,.2f}".format)
    st.dataframe(last_df.reset_index(drop=True), use_container_width=True, hide_index=True)

# ─── BREAKDOWN TAB ────────────────────────────────────────────────────────────
with tab_breakdown:
    st.subheader("Aufschlüsselung der Einkommensquellen")

    col_pie, col_sun = st.columns(2)

    # Tortendiagramm: Anteil am Gesamteinkommen
    total_per_source = df.groupby("source", as_index=False)["monthly"].sum()
    total_per_source["color"] = [
        next((s["color"] for s in sources if s["name"] == nm), "#888")
        for nm in total_per_source["source"]
    ]
    with col_pie:
        fig_pie = go.Figure(go.Pie(
            labels=total_per_source["source"],
            values=total_per_source["monthly"],
            marker_colors=total_per_source["color"],
            hole=0.45,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Gesamt: €%{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig_pie.update_layout(
            title=f"Anteil am Gesamteinkommen über {years} Jahre",
            height=380,
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0"),
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Horizontale Balken: Monatseinkommen Start vs. Ende
    start_vals = df[df["month_idx"] == 0].groupby("source")["monthly"].sum()
    end_vals   = df[df["month_idx"] == months_total - 1].groupby("source")["monthly"].sum()
    bar_df = pd.DataFrame({"Quelle": start_vals.index,
                           "Start": start_vals.values,
                           "Ende":  end_vals.reindex(start_vals.index).values}).sort_values("Ende")
    with col_sun:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=bar_df["Quelle"], x=bar_df["Start"],
            orientation="h", name="Monat 1",
            marker_color="rgba(150,150,150,0.6)",
        ))
        fig_bar.add_trace(go.Bar(
            y=bar_df["Quelle"], x=bar_df["Ende"],
            orientation="h", name=f"Jahr {years}",
            marker_color=[
                next((s["color"] for s in sources if s["name"] == nm), "#888")
                for nm in bar_df["Quelle"]
            ],
        ))
        fig_bar.update_layout(
            barmode="overlay",
            title="Monatseinkommen: Start vs. Ende",
            height=380,
            xaxis_title="Monatliches Einkommen (€)",
            xaxis_tickprefix="€",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Wasserfall: kumulierte Einkommensmeilensteine
    st.subheader("Kumulierte Einkommensmeilensteine")
    yearly_totals = df_yearly.groupby("year")["annual"].sum().reset_index()
    yearly_totals["cumulative"] = yearly_totals["annual"].cumsum()
    fig_wf = go.Figure(go.Waterfall(
        name="Kumuliert",
        orientation="v",
        measure=["relative"] * years,
        x=[f"Jahr {y}" for y in yearly_totals["year"]],
        y=yearly_totals["annual"],
        connector={"line": {"color": "rgba(255,255,255,0.2)"}},
        increasing={"marker": {"color": "#4CAF50"}},
        totals={"marker": {"color": "#2196F3"}},
        hovertemplate="<b>%{x}</b><br>Hinzugekommen: €%{y:,.0f}<br>Laufende Summe: €%{customdata:,.0f}<extra></extra>",
        customdata=yearly_totals["cumulative"],
    ))
    fig_wf.update_layout(
        height=360,
        xaxis_title="Jahr",
        yaxis_title="Hinzugekommenes Einkommen (€)",
        yaxis_tickprefix="€",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
    )
    st.plotly_chart(fig_wf, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AUSGABEN-SEKTION
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
st.header("💸 Ausgaben")

if df_exp.empty:
    st.info("👈 Füge Ausgaben in der Seitenleiste hinzu, um sie hier zu sehen.")
else:
    # KPI strip for expenses
    first_exp_total = df_exp[df_exp["month_idx"] == 0]["monthly"].sum()
    last_exp_total  = df_exp[df_exp["month_idx"] == months_total - 1]["monthly"].sum()
    total_spent     = df_exp_monthly_total["monthly_total"].sum()

    e1, e2, e3, e4 = st.columns(4)
    e1.metric("🔴 Monatl. Ausgaben (Start)", f"€{first_exp_total:,.0f}")
    e2.metric("📈 Monatl. Ausgaben in Jahr " + str(years), f"€{last_exp_total:,.0f}",
              delta=f"+{last_exp_total - first_exp_total:,.0f} vs. Start", delta_color="inverse")
    e3.metric("☀️ Täglich (Jahr " + str(years) + ")", f"€{last_exp_total/30.44:,.1f}")
    e4.metric("🏧 Gesamt ausgegeben über " + str(years) + " Jahre", f"€{total_spent:,.0f}")

    st.divider()
    tab_exp_y, tab_exp_m, tab_exp_break = st.tabs(
        ["📅 Jährlich", "📆 Monatlich", "🥧 Aufschlüsselung"]
    )

    # ── Ausgaben jährlich ────────────────────────────────────────────────────
    with tab_exp_y:
        st.subheader("Jährliche Ausgaben je Kategorie")
        fig_ey = go.Figure()
        for exp in expenses:
            d = df_exp_yearly[df_exp_yearly["expense"] == exp["name"]]
            fig_ey.add_trace(go.Bar(
                x=d["year"], y=d["annual"],
                name=exp["name"], marker_color=exp["color"],
                customdata=d["monthly_avg"].values.reshape(-1, 1),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Jahr %{x}<br>"
                    "Jährlich:    €%{y:,.0f}<br>"
                    "Ø Monatlich: €%{customdata[0]:,.0f}<extra></extra>"
                ),
            ))
        fig_ey.update_layout(
            barmode="stack",
            xaxis_title="Jahr", yaxis_title="Jährliche Ausgaben (€)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=420, xaxis=dict(dtick=1),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
        )
        st.plotly_chart(fig_ey, use_container_width=True)

    # ── Ausgaben monatlich ───────────────────────────────────────────────────
    with tab_exp_m:
        st.subheader("Monatlicher Ausgabenstrom")
        fig_em = go.Figure()
        for exp in expenses:
            d = df_exp[df_exp["expense"] == exp["name"]].sort_values("month_idx")
            fig_em.add_trace(go.Scatter(
                x=d["month_idx"] + 1, y=d["monthly"],
                name=exp["name"], stackgroup="one",
                fillcolor=hex_to_rgba(exp["color"], 0.73),
                line_color=exp["color"],
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Monat %{x}<br>"
                    "Monatlich: €%{y:,.0f}<extra></extra>"
                ),
            ))
        fig_em.add_trace(go.Scatter(
            x=df_exp_monthly_total["month_idx"] + 1,
            y=df_exp_monthly_total["monthly_total"],
            name="Gesamt", line=dict(color="white", width=2, dash="dot"),
            hovertemplate="Monat %{x}<br>Gesamt: €%{y:,.0f}<extra></extra>",
        ))
        for yr in range(1, years):
            fig_em.add_vline(x=yr * 12 + 0.5, line_dash="dash", line_color="rgba(200,200,200,0.3)")
        fig_em.update_layout(
            height=420, xaxis_title="Monat", yaxis_title="Monatliche Ausgaben (€)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"), hovermode="x unified",
        )
        st.plotly_chart(fig_em, use_container_width=True)

    # ── Ausgaben Aufschlüsselung ─────────────────────────────────────────────
    with tab_exp_break:
        st.subheader("Aufschlüsselung der Ausgaben")
        col_ep, col_eb = st.columns(2)

        total_per_exp = df_exp.groupby("expense", as_index=False)["monthly"].sum()
        total_per_exp["color"] = [
            next((e["color"] for e in expenses if e["name"] == nm), "#888")
            for nm in total_per_exp["expense"]
        ]
        with col_ep:
            fig_epie = go.Figure(go.Pie(
                labels=total_per_exp["expense"],
                values=total_per_exp["monthly"],
                marker_colors=total_per_exp["color"],
                hole=0.45, textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Gesamt: €%{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig_epie.update_layout(
                title=f"Ausgabenanteil über {years} Jahre",
                height=360, paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"), showlegend=False,
            )
            st.plotly_chart(fig_epie, use_container_width=True)

        # Start vs. Ende horizontal
        exp_start = df_exp[df_exp["month_idx"] == 0].groupby("expense")["monthly"].sum()
        exp_end   = df_exp[df_exp["month_idx"] == months_total - 1].groupby("expense")["monthly"].sum()
        ebar_df   = pd.DataFrame({"Ausgabe": exp_start.index,
                                   "Start": exp_start.values,
                                   "Ende":  exp_end.reindex(exp_start.index).values}).sort_values("Ende")
        with col_eb:
            fig_ebar = go.Figure()
            fig_ebar.add_trace(go.Bar(
                y=ebar_df["Ausgabe"], x=ebar_df["Start"],
                orientation="h", name="Monat 1",
                marker_color="rgba(150,150,150,0.6)",
            ))
            fig_ebar.add_trace(go.Bar(
                y=ebar_df["Ausgabe"], x=ebar_df["Ende"],
                orientation="h", name=f"Jahr {years}",
                marker_color=[
                    next((e["color"] for e in expenses if e["name"] == nm), "#888")
                    for nm in ebar_df["Ausgabe"]
                ],
            ))
            fig_ebar.update_layout(
                barmode="overlay", title="Monatsausgaben: Start vs. Ende",
                height=360, xaxis_title="Monatliche Ausgaben (€)", xaxis_tickprefix="€",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig_ebar, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EINNAHMEN vs. AUSGABEN – GESAMTBILD
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
st.header("⚖️ Einnahmen vs. Ausgaben – Gesamtbild")

# Merge monthly totals
inc_m = df_monthly_total[["month_idx", "monthly_total"]].rename(columns={"monthly_total": "einnahmen"})
exp_m = df_exp_monthly_total[["month_idx", "monthly_total"]].rename(columns={"monthly_total": "ausgaben"})
balance_df = pd.merge(inc_m, exp_m, on="month_idx", how="left").fillna(0)
balance_df["netto"]      = balance_df["einnahmen"] - balance_df["ausgaben"]
balance_df["kumuliert"]  = balance_df["netto"].cumsum()
balance_df["year"]       = balance_df["month_idx"] // 12 + 1

# ── Yearly summary for comparison ────────────────────────────────────────────
inc_y  = df_yearly.groupby("year")["annual"].sum().rename("einnahmen")
exp_y_grp = df_exp_yearly.groupby("year")["annual"].sum().rename("ausgaben") if not df_exp_yearly.empty \
            else pd.Series(0.0, index=range(1, years + 1), name="ausgaben")
bal_y  = pd.DataFrame({"einnahmen": inc_y, "ausgaben": exp_y_grp}).fillna(0).reset_index()
bal_y["netto"] = bal_y["einnahmen"] - bal_y["ausgaben"]

# ── KPI strip ────────────────────────────────────────────────────────────────
net_start  = balance_df.loc[balance_df["month_idx"] == 0, "netto"].values[0]
net_end    = balance_df.loc[balance_df["month_idx"] == months_total - 1, "netto"].values[0]
cumulative_net = balance_df["netto"].sum()
breakeven_month = balance_df[balance_df["netto"] >= 0]["month_idx"].min()

n1, n2, n3, n4 = st.columns(4)
n1.metric("📊 Netto monatlich (Start)", f"€{net_start:,.0f}",
          delta_color="normal" if net_start >= 0 else "inverse")
n2.metric("📊 Netto monatlich (Jahr " + str(years) + ")", f"€{net_end:,.0f}",
          delta=f"{net_end - net_start:+,.0f} vs. Start",
          delta_color="normal" if net_end >= net_start else "inverse")
n3.metric("🏆 Kumuliertes Netto", f"€{cumulative_net:,.0f}",
          delta_color="normal" if cumulative_net >= 0 else "inverse")
if pd.isna(breakeven_month):
    n4.metric("⚠️ Break-Even", "Nicht erreicht")
else:
    n4.metric("✅ Break-Even ab", f"Monat {int(breakeven_month)+1} (Jahr {int(breakeven_month)//12+1})")

st.divider()

# ── Chart 1: Stacked area – Einnahmen & Ausgaben überlagert ──────────────────
fig_cmp = make_subplots(
    rows=2, cols=1, shared_xaxes=True,
    row_heights=[0.6, 0.4],
    subplot_titles=("Monatliche Einnahmen vs. Ausgaben", "Monatliches Nettoeinkommen"),
)

# Income area
fig_cmp.add_trace(go.Scatter(
    x=balance_df["month_idx"] + 1, y=balance_df["einnahmen"],
    name="Einnahmen", fill="tozeroy",
    fillcolor="rgba(76,175,80,0.35)", line=dict(color="#4CAF50", width=2),
    hovertemplate="Monat %{x}<br>Einnahmen: €%{y:,.0f}<extra></extra>",
), row=1, col=1)

# Expense area
fig_cmp.add_trace(go.Scatter(
    x=balance_df["month_idx"] + 1, y=balance_df["ausgaben"],
    name="Ausgaben", fill="tozeroy",
    fillcolor="rgba(244,67,54,0.35)", line=dict(color="#F44336", width=2),
    hovertemplate="Monat %{x}<br>Ausgaben: €%{y:,.0f}<extra></extra>",
), row=1, col=1)

# Net income bar (green positive, red negative)
net_colors = ["#4CAF50" if v >= 0 else "#F44336" for v in balance_df["netto"]]
fig_cmp.add_trace(go.Bar(
    x=balance_df["month_idx"] + 1, y=balance_df["netto"],
    name="Netto", marker_color=net_colors,
    hovertemplate="Monat %{x}<br>Netto: €%{y:,.0f}<extra></extra>",
), row=2, col=1)

# Zero line
fig_cmp.add_hline(y=0, line_color="white", line_width=1, line_dash="dot", row=2, col=1)

for yr in range(1, years):
    fig_cmp.add_vline(x=yr * 12 + 0.5, line_dash="dash", line_color="rgba(200,200,200,0.2)", row="all")

fig_cmp.update_layout(
    height=540, hovermode="x unified",
    xaxis2_title="Monat",
    yaxis_title="Monatlich (€)", yaxis2_title="Netto (€)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e0e0e0"),
)
st.plotly_chart(fig_cmp, use_container_width=True)

# ── Chart 2: Kumulierter Nettosaldo ──────────────────────────────────────────
st.subheader("Kumulierter Nettosaldo über die Zeit")
cum_colors = ["rgba(76,175,80,0.7)" if v >= 0 else "rgba(244,67,54,0.7)" for v in balance_df["kumuliert"]]
fig_cum = go.Figure()
fig_cum.add_trace(go.Scatter(
    x=balance_df["month_idx"] + 1, y=balance_df["kumuliert"],
    fill="tozeroy",
    fillcolor="rgba(76,175,80,0.2)",
    line=dict(color="#4CAF50", width=2),
    name="Kumuliertes Netto",
    hovertemplate="Monat %{x}<br>Kumuliert: €%{y:,.0f}<extra></extra>",
))
fig_cum.add_hline(y=0, line_color="white", line_width=1, line_dash="dot")
for yr in range(1, years):
    fig_cum.add_vline(x=yr * 12 + 0.5, line_dash="dash", line_color="rgba(200,200,200,0.2)")
fig_cum.update_layout(
    height=320, xaxis_title="Monat", yaxis_title="Kumuliertes Netto (€)",
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e0e0e0"), showlegend=False,
)
st.plotly_chart(fig_cum, use_container_width=True)

# ── Chart 3: Jährliche Gegenüberstellung (gruppiertes Balkendiagramm) ────────
st.subheader("Jährliche Gegenüberstellung")
col_bar_y, col_wf_y = st.columns(2)

with col_bar_y:
    fig_bar_y = go.Figure()
    fig_bar_y.add_trace(go.Bar(
        x=bal_y["year"], y=bal_y["einnahmen"],
        name="Einnahmen", marker_color="#4CAF50",
        hovertemplate="Jahr %{x}<br>Einnahmen: €%{y:,.0f}<extra></extra>",
    ))
    fig_bar_y.add_trace(go.Bar(
        x=bal_y["year"], y=bal_y["ausgaben"],
        name="Ausgaben", marker_color="#F44336",
        hovertemplate="Jahr %{x}<br>Ausgaben: €%{y:,.0f}<extra></extra>",
    ))
    fig_bar_y.update_layout(
        barmode="group", title="Einnahmen vs. Ausgaben pro Jahr",
        height=380, xaxis_title="Jahr", yaxis_title="€", xaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
    )
    st.plotly_chart(fig_bar_y, use_container_width=True)

with col_wf_y:
    fig_net_y = go.Figure(go.Bar(
        x=bal_y["year"], y=bal_y["netto"],
        marker_color=["#4CAF50" if v >= 0 else "#F44336" for v in bal_y["netto"]],
        hovertemplate="Jahr %{x}<br>Netto: €%{y:,.0f}<extra></extra>",
        name="Netto",
    ))
    fig_net_y.add_hline(y=0, line_color="white", line_width=1, line_dash="dot")
    fig_net_y.update_layout(
        title="Jährliches Nettoeinkommen",
        height=380, xaxis_title="Jahr", yaxis_title="Netto (€)", xaxis=dict(dtick=1),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"), showlegend=False,
    )
    st.plotly_chart(fig_net_y, use_container_width=True)

# ── Abschlusstabelle ─────────────────────────────────────────────────────────
st.subheader("📋 Jahresübersicht")
summary_df = bal_y.copy()
summary_df["Sparquote (%)"] = (
    (summary_df["netto"] / summary_df["einnahmen"].replace(0, np.nan)) * 100
).round(1)
summary_df.columns = ["Jahr", "Einnahmen (€)", "Ausgaben (€)", "Netto (€)", "Sparquote (%)"]
for col in ["Einnahmen (€)", "Ausgaben (€)", "Netto (€)"]:
    summary_df[col] = summary_df[col].map("€{:,.0f}".format)
st.dataframe(summary_df.reset_index(drop=True), use_container_width=True, hide_index=True)
