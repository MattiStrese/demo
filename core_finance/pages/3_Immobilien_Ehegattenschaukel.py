import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =========================================
# Titel & Einführung
# =========================================
st.title("Ehegattenschaukel – Interaktive Veranschaulichung")
st.markdown("""
Die **Ehegattenschaukel** beschreibt vereinfacht die steueroptimierte Verteilung (bzw. zeitweilige Übertragung) von Kapitalerträgen
oder realisierten Gewinnen zwischen zwei Ehepartnern, um **persönliche Freibeträge** und **unterschiedliche effektive Steuersätze**
besser zu nutzen.

Diese App zeigt dir:
- wie sich Steuerlast **ohne** Verteilung (alles bei Person A) gegenüber einer **freien Verteilung** auf A & B unterscheidet,
- wie hoch die **optimale Verteilung** (Minimum der Gesamtsteuer) wäre – nach den von dir gesetzten Parametern.

> *Die Berechnung ist stark vereinfacht (Pauschalsteuersatz/Abgeltungsteuer-Modell).*
""")

# =========================================
# Modus-Auswahl (Monat/Jahr nur fürs UI-Feeling, steuerlich hier egal)
# =========================================
modus = st.selectbox("Darstellung für:", ["Jahr", "Monat"])
faktor = 1 if modus == "Monat" else 1  # rein kosmetisch in dieser App; Beträge sind Jahreswerte

# =========================================
# Eingaben
# =========================================
st.header("Eingaben")

col1, col2 = st.columns(2)
with col1:
    # Gesamter „zu verteilender“ realisierter Gewinn/Kapitalertrag
    total_gain = st.number_input(
        "Zu verteilender Gewinn/Kapitalertrag gesamt (in €)",
        min_value=0.0,
        value=10000.0,
        step=500.0
    )
    # Sonstige Kapitalerträge pro Person (belegen ggf. Freibetrag)
    other_cap_a = st.number_input(
        "Weitere Kapitalerträge Person A (in €)",
        min_value=0.0, value=500.0, step=100.0
    )
    other_cap_b = st.number_input(
        "Weitere Kapitalerträge Person B (in €)",
        min_value=0.0, value=200.0, step=100.0
    )
with col2:
    # Freibeträge & Sätze
    pauschbetrag = st.number_input(
        "Sparer-Pauschbetrag pro Person (in €)",
        min_value=0.0, value=1000.0, step=50.0
    )
    abgeltung_inkl_soli = st.number_input(
        "Effektiver Steuersatz auf Kapitalerträge (in %)",
        min_value=0.0, max_value=60.0, value=26.375, step=0.125,
        help="Z.B. 25% Abgeltungsteuer + Solidaritätszuschlag. Kirchensteuer optional separat."
    )
    church_tax_rate = st.number_input(
        "Kirchensteuer (in % auf Steuer, optional)",
        min_value=0.0, max_value=15.0, value=0.0, step=0.5,
        help="Anteil an der Steuer, nicht am Gewinn (vereinfacht). 8%/9% je nach Bundesland – hier optional."
    )

st.divider()

st.subheader("Freie Verteilung des Gewinns")
share_a = st.slider("Anteil des Gewinns bei Person A (%)", 0, 100, 50, step=1)
share_b = 100 - share_a

# =========================================
# Hilfsfunktionen
# =========================================
def tax_on_capital(income_capital: float, pausch: float, rate_percent: float, church_rate_percent: float) -> tuple[float, float, float]:
    """
    Berechnet Steuer auf Kapitalerträge (vereinfachtes Abgeltungsteuer-Modell).
    - income_capital: gesamte Kapitalerträge
    - pausch: Sparer-Pauschbetrag
    - rate_percent: effektiver Steuersatz (z.B. 26.375)
    - church_rate_percent: Anteil der Kirchensteuer auf die Steuer (z.B. 9)
    Rückgabe: (steuerpflichtiger Betrag, Steuer (ohne Kirche), Kirchensteuer)
    """
    taxable = max(income_capital - pausch, 0.0)
    base_tax = taxable * (rate_percent / 100.0)
    church_tax = base_tax * (church_rate_percent / 100.0)
    return taxable, base_tax, church_tax

def evaluate_split(total_gain: float, x_to_a: float) -> dict:
    """Bewertet eine Verteilung x_to_a (Anteil für A in €) vs. Rest für B."""
    gain_a = x_to_a
    gain_b = total_gain - x_to_a

    # Gesamte Kapitalerträge pro Person inkl. weiterer Kapitalerträge
    cap_a = other_cap_a + gain_a
    cap_b = other_cap_b + gain_b

    taxable_a, base_tax_a, church_a = tax_on_capital(cap_a, pauschbetrag, abgeltung_inkl_soli, church_tax_rate)
    taxable_b, base_tax_b, church_b = tax_on_capital(cap_b, pauschbetrag, abgeltung_inkl_soli, church_tax_rate)

    total_tax = base_tax_a + church_a + base_tax_b + church_b

    return {
        "gain_a": gain_a, "gain_b": gain_b,
        "cap_a": cap_a, "cap_b": cap_b,
        "taxable_a": taxable_a, "taxable_b": taxable_b,
        "tax_a_no_church": base_tax_a, "tax_b_no_church": base_tax_b,
        "church_a": church_a, "church_b": church_b,
        "total_tax": total_tax
    }

# =========================================
# Szenario 1: Ohne Schaukel (Alles bei A)
# =========================================
scenario_no_split = evaluate_split(total_gain, total_gain)

# =========================================
# Szenario 2: Aktuelle Slider-Verteilung
# =========================================
scenario_slider = evaluate_split(total_gain, total_gain * (share_a / 100.0))

# =========================================
# Szenario 3: Optimale Verteilung (Minimierung)
# =========================================
# Brute-Force über 0..100% in 0.1%-Schritten (schnell genug)
best = None
best_pct = 0.0
for pct in [i/10 for i in range(0, 1001)]:  # 0.0% .. 100.0%
    res = evaluate_split(total_gain, total_gain * (pct / 100.0))
    if best is None or res["total_tax"] < best["total_tax"]:
        best = res
        best_pct = pct

# =========================================
# Ergebnisse – Übersicht
# =========================================
st.header("Ergebnisse & Vergleich")

colA, colB, colC = st.columns(3)
with colA:
    st.metric("Ohne Schaukel: Steuer gesamt (A 100%)", f"{scenario_no_split['total_tax']:,.2f} €")
with colB:
    st.metric("Slider-Verteilung: Steuer gesamt", f"{scenario_slider['total_tax']:,.2f} €")
with colC:
    st.metric("Optimale Verteilung: Steuer gesamt", f"{best['total_tax']:,.2f} €")

st.caption(
    f"Optimale Verteilung laut Modell: **{best_pct:.1f}%** an Person A "
    f"(= {best['gain_a']:,.2f} €) und **{100-best_pct:.1f}%** an Person B "
    f"(= {best['gain_b']:,.2f} €)."
)

# =========================================
# Tabellen-Details
# =========================================
st.subheader("Detailwerte pro Szenario")

def make_df(label: str, d: dict) -> pd.DataFrame:
    return pd.DataFrame({
        "Kennzahl": [
            "Zugeordneter Gewinn A (€/%)",
            "Zugeordneter Gewinn B (€/%)",
            "Kapitalerträge A gesamt",
            "Kapitalerträge B gesamt",
            "Steuerpfl. Betrag A",
            "Steuerpfl. Betrag B",
            "Steuer A (ohne KiSt)",
            "Steuer B (ohne KiSt)",
            "Kirchensteuer A",
            "Kirchensteuer B",
            "Steuer gesamt"
        ],
        label: [
            f"{d['gain_a']:,.2f} € ({(d['gain_a']/total_gain*100 if total_gain else 0):.1f}%)",
            f"{d['gain_b']:,.2f} € ({(d['gain_b']/total_gain*100 if total_gain else 0):.1f}%)",
            f"{d['cap_a']:,.2f} €",
            f"{d['cap_b']:,.2f} €",
            f"{d['taxable_a']:,.2f} €",
            f"{d['taxable_b']:,.2f} €",
            f"{d['tax_a_no_church']:,.2f} €",
            f"{d['tax_b_no_church']:,.2f} €",
            f"{d['church_a']:,.2f} €",
            f"{d['church_b']:,.2f} €",
            f"**{d['total_tax']:,.2f} €**"
        ]
    })

df_compare = make_df("Ohne Schaukel (A 100%)", scenario_no_split)\
    .merge(make_df("Slider-Verteilung", scenario_slider), on="Kennzahl")\
    .merge(make_df("Optimale Verteilung", best), on="Kennzahl")

st.dataframe(df_compare, use_container_width=True)

# =========================================
# Visualisierungen
# =========================================
st.header("Visualisierungen")

# 1) Steuerlastvergleich Balken
fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=["Ohne Schaukel (A 100%)", "Slider-Verteilung", "Optimale Verteilung"],
    y=[scenario_no_split["total_tax"], scenario_slider["total_tax"], best["total_tax"]],
    name="Gesamtsteuer"
))
fig1.update_layout(
    title="Gesamtsteuer je Szenario",
    xaxis_title="Szenario",
    yaxis_title="Steuer in €"
)
st.plotly_chart(fig1, use_container_width=True)

# 2) Gewinnverteilung A vs. B – aktueller Slider
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=["Person A", "Person B"],
    y=[scenario_slider["gain_a"], scenario_slider["gain_b"]],
    name="Zugeordneter Gewinn"
))
fig2.update_layout(
    title=f"Aktuelle Gewinnverteilung (A {share_a}%, B {share_b}%)",
    xaxis_title="Person",
    yaxis_title="Betrag in €"
)
st.plotly_chart(fig2, use_container_width=True)

# 3) Steuerkomponenten (aktueller Slider)
fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=["A: Steuer (ohne KiSt)", "A: Kirchensteuer", "B: Steuer (ohne KiSt)", "B: Kirchensteuer"],
    y=[scenario_slider["tax_a_no_church"], scenario_slider["church_a"],
       scenario_slider["tax_b_no_church"], scenario_slider["church_b"]],
    name="Steuerkomponenten"
))
fig3.update_layout(
    title="Steuerkomponenten – Slider-Verteilung",
    xaxis_title="Komponente",
    yaxis_title="Betrag in €"
)
st.plotly_chart(fig3, use_container_width=True)

# =========================================
# Erläuterungen
# =========================================
with st.expander("Was wird hier vereinfacht? (Klicken zum Ein- / Ausklappen)"):
    st.markdown("""
- Es wird ein **Pauschalsteuersatz** für Kapitalerträge verwendet (Abgeltungsteuer + ggf. Soli + optionale Kirchensteuer als Zuschlag).
- **Sparer-Pauschbetrag** wird pro Person angesetzt. Andere Detailregeln (z. B. Verlustverrechnungstöpfe, Teileinkünfteverfahren,
  besondere Ausnahmen/Fristen, Quellensteuern) werden **nicht** abgebildet.
- Ob und wie eine Übertragung/Verteilung rechtlich zulässig und sinnvoll ist, hängt vom Einzelfall ab.  
  **Bitte fachlich beraten lassen**, bevor du echte Dispositionen triffst.
""")
