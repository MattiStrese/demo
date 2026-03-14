import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def steuer_progression(zvE: float) -> float:
    """
    Tarifliche Einkommensteuer (ESt) nach §32a EStG (vereinfachte Parametrisierung wie in deinem Code).
    zvE = zu versteuerndes Einkommen (Jahreswert).
    """
    if zvE <= 12096:
        est = 0.0
    elif zvE <= 17443:
        y = (zvE - 12096) / 10000
        est = (932.3 * y + 1400) * y
    elif zvE <= 68480:
        z = (zvE - 17443) / 10000
        est = (176.64 * z + 2397) * z + 1015.13
    elif zvE <= 277825:
        est = 0.42 * zvE - 10911.92
    else:
        est = 0.45 * zvE - 19246.67
    return float(max(est, 0.0))


# ─────────────────────────────────────────────────────────────
# Globale Annahmen (vereinfachtes Modell)
# ─────────────────────────────────────────────────────────────

WERBUNGSKOSTEN_PAUSCHBETRAG = 1_230  # Arbeitnehmer-Pauschbetrag

# Beitragssätze (AN-Anteil, grob/typisch)
RV_RATE = 0.093
AV_RATE = 0.013
KV_RATE = 0.073
KV_ZUSATZ = 0.017
PV_RATE = 0.017

# Beitragsbemessungsgrenzen (Jahr, grob/typisch)
BBG_RV_AV = 90_600
BBG_KV_PV = 62_100


def calc_sozialabgaben_an(brutto_jahr: float) -> dict:
    """Sozialabgaben (AN-Anteil) inkl. BBG, Jahreswerte."""
    rv_bem = min(brutto_jahr, BBG_RV_AV)
    kv_bem = min(brutto_jahr, BBG_KV_PV)

    renten = rv_bem * RV_RATE
    arbeitslos = rv_bem * AV_RATE
    kranken = kv_bem * (KV_RATE + KV_ZUSATZ)
    pflege = kv_bem * PV_RATE

    total = renten + arbeitslos + kranken + pflege
    return {
        "rentenversicherung": renten,
        "arbeitslosenversicherung": arbeitslos,
        "krankenversicherung": kranken,
        "pflegeversicherung": pflege,
        "sozialabgaben": total,
    }


def calc_netto_arbeit(brutto_jahr: float, steuerklassen_faktor: float) -> dict:
    """
    Vereinfacht:
    - zvE = brutto - Sozialabgaben - Werbungskosten-Pauschbetrag
    - ESt = steuer_progression(zvE) * steuerklassen_faktor  (Hinweis: real ist Steuerklasse kein Jahresfaktor)
    - netto = brutto - Sozialabgaben - ESt
    """
    sozial = calc_sozialabgaben_an(brutto_jahr)
    zvE = max(brutto_jahr - sozial["sozialabgaben"] - WERBUNGSKOSTEN_PAUSCHBETRAG, 0.0)
    est = steuer_progression(zvE) * steuerklassen_faktor
    netto = brutto_jahr - sozial["sozialabgaben"] - est

    return {
        **sozial,
        "zvE": zvE,
        "einkommensteuer": est,
        "netto_jahr": netto,
        "netto_monat": netto / 12.0,
        "abzuege_gesamt": sozial["sozialabgaben"] + WERBUNGSKOSTEN_PAUSCHBETRAG,
    }


# ─────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="Steuerübersicht", layout="wide")
st.title("💰 Umfassende steuerliche Übersicht in Deutschland")

st.markdown(
    """
Diese interaktive Seite simuliert die steuerliche Behandlung verschiedener Einkunftsarten in Deutschland.  
Neben den bereits bekannten Kategorien werden auch weitere Einnahmen berücksichtigt:
- **Einkünfte aus selbständiger Arbeit**
- **Einkünfte aus Gewerbebetrieb**
- **Einkünfte aus Land- und Forstwirtschaft**
- **Sonstige Einkünfte** (z. B. Renten, Pensionen)

Hinweis: Der Bereich **Nichtselbständige Arbeit** ist hier bewusst **vereinfacht** (Pauschbetrag, Sozialabgaben, Progression).
"""
)

st.markdown("#### Allgemeine Steuersätze (für die anderen Kategorien im Demo-Modell)")
effective_income_tax = st.slider(
    "Effektiver Einkommensteuersatz (für nichtkapitalbezogene Einkünfte) in %",
    min_value=0,
    max_value=50,
    value=23,
    step=1,
)
abgeltung_tax = st.slider(
    "Abgeltungsteuer (für Kapitalerträge) in %",
    min_value=0,
    max_value=30,
    value=25,
    step=1,
)
gewerbesteuer_rate = st.slider(
    "Gewerbesteuer (für Gewerbebetrieb) in %",
    min_value=0,
    max_value=20,
    value=3,
    step=1,
)

# ─────────────────────────────────────────────────────────────
# 1. Arbeit (vereinfacht) inkl. Sozialabgaben
# ─────────────────────────────────────────────────────────────

st.header("1. Nichtselbständige Arbeit (vereinfacht, inkl. Sozialabgaben)")
with st.expander("Eingaben und Berechnungen", expanded=True):
    basis = st.radio("Rechenbasis", options=["Monatlich", "Jährlich"], horizontal=True)
    faktor = 12 if basis == "Monatlich" else 1

    steuerklasse = st.selectbox("Steuerklasse", options=["I", "II", "III", "IV", "V", "VI"], index=0)

    # Slider bleibt im gewünschten 50k..90k Bereich (auf Jahresbasis); bei Monatsansicht entsprechend skaliert.
    brutto_input = st.slider(
        f"Bruttolohn ({basis.lower()}, €)",
        min_value=50_000 // faktor,
        max_value=90_000 // faktor,
        value=67_000 // faktor,
        step=1_000 // faktor,
    )

    brutto_jahr = float(brutto_input * faktor)

    # Vereinfachter Steuerklassen-Faktor (nur zur Visualisierung im Modell)
    steuerklassen_faktor = {
        "I": 1.00,
        "II": 0.95,
        "III": 0.75,
        "IV": 1.00,
        "V": 1.25,
        "VI": 1.30,
    }[steuerklasse]

    res_arbeit = calc_netto_arbeit(brutto_jahr=brutto_jahr, steuerklassen_faktor=steuerklassen_faktor)

    st.write(f"**Brutto ({basis.lower()}):** {brutto_input:,.0f} €")
    st.write(f"**Brutto (jährlich):** {brutto_jahr:,.0f} €")

    st.markdown("### 🧾 Sozialabgaben (AN-Anteil, Jahr)")
    st.write(f"Rentenversicherung: {res_arbeit['rentenversicherung']:,.0f} €")
    st.write(f"Arbeitslosenversicherung: {res_arbeit['arbeitslosenversicherung']:,.0f} €")
    st.write(f"Krankenversicherung (inkl. Zusatz): {res_arbeit['krankenversicherung']:,.0f} €")
    st.write(f"Pflegeversicherung: {res_arbeit['pflegeversicherung']:,.0f} €")
    st.write(f"**Summe Sozialabgaben:** {res_arbeit['sozialabgaben']:,.0f} €")

    st.markdown("### 🧮 Steuerbasis (Modell)")
    st.write(f"Werbungskosten (Pauschbetrag): {WERBUNGSKOSTEN_PAUSCHBETRAG:,.0f} €")
    st.write(f"Zu versteuerndes Einkommen (Jahr): {res_arbeit['zvE']:,.0f} €")
    st.write(f"Einkommensteuer (Jahr, vereinfacht): {res_arbeit['einkommensteuer']:,.0f} €")

    st.markdown("### 💸 Nettoübersicht")
    if basis == "Jährlich":
        st.metric("Netto pro Jahr", f"{res_arbeit['netto_jahr']:,.0f} €")
        st.metric("Netto pro Monat", f"{res_arbeit['netto_monat']:,.0f} €")
    else:
        st.metric("Netto pro Monat", f"{res_arbeit['netto_monat']:,.0f} €")
        st.metric("Netto pro Jahr", f"{res_arbeit['netto_jahr']:,.0f} €")

    # Text-Grenzbetrachtung (+1.000 € jährlich)
    delta_brutto = 1_000.0
    res_next = calc_netto_arbeit(brutto_jahr=brutto_jahr + delta_brutto, steuerklassen_faktor=steuerklassen_faktor)
    netto_diff = res_next["netto_jahr"] - res_arbeit["netto_jahr"]
    st.caption(f"➡️ +1.000 € Brutto (jährlich) ⇒ ca. **{netto_diff:,.0f} € Netto** zusätzlich")

# Grafische Grenzbetrachtung (50k..100k)
st.header("📈 Grenzbetrachtung: Nettozuwachs pro +1.000 € Brutto (50.000–100.000 €)")

BRUTTO_MIN = 50_000
BRUTTO_MAX = 80_000
STEP = 1000

brutto_values = np.arange(BRUTTO_MIN, BRUTTO_MAX + STEP, STEP, dtype=float)
netto_diffs = []

for b in brutto_values:
    r0 = calc_netto_arbeit(brutto_jahr=b, steuerklassen_faktor=steuerklassen_faktor)
    r1 = calc_netto_arbeit(brutto_jahr=b + STEP, steuerklassen_faktor=steuerklassen_faktor)
    netto_diffs.append(r1["netto_jahr"] - r0["netto_jahr"])

df_grenze = pd.DataFrame(
    {
        "Bruttolohn (Jahr, €)": brutto_values,
        "Nettozuwachs bei +1.000 € (€, Jahr)": netto_diffs,
    }
)

fig_grenze = go.Figure()
fig_grenze.add_trace(
    go.Scatter(
        x=df_grenze["Bruttolohn (Jahr, €)"],
        y=df_grenze["Nettozuwachs bei +1.000 € (€, Jahr)"],
        mode="lines+markers",
        name="Nettozuwachs",
    )
)
fig_grenze.update_layout(
    title="Zusätzlicher Nettoeffekt pro +1.000 € Brutto (inkl. Sozialabgaben & BBG im Modell)",
    xaxis_title="Bruttolohn (jährlich, €)",
    yaxis_title="Zusätzlicher Netto (€, pro +1.000 € Brutto)",
    hovermode="x unified",
)
st.plotly_chart(fig_grenze, use_container_width=True)
# ─────────────────────────────────────────────────────────────
# Netto vs. Brutto (40k – 100k)
# ─────────────────────────────────────────────────────────────

st.header("📊 Nettojahresgehalt in Abhängigkeit vom Bruttogehalt")

BRUTTO_MIN_NET = 50_000
BRUTTO_MAX_NET = 80_000
STEP_NET = 1_000

brutto_vals = np.arange(BRUTTO_MIN_NET, BRUTTO_MAX_NET + STEP_NET, STEP_NET, dtype=float)
netto_vals = []

for brutto in brutto_vals:
    res = calc_netto_arbeit(brutto_jahr=brutto, steuerklassen_faktor=steuerklassen_faktor)
    netto_vals.append(res["netto_jahr"])

df_netto = pd.DataFrame(
    {
        "Bruttogehalt (jährlich, €)": brutto_vals,
        "Nettojahresgehalt (€)": netto_vals,
    }
)

fig_netto = go.Figure()

fig_netto.add_trace(
    go.Scatter(
        x=df_netto["Bruttogehalt (jährlich, €)"],
        y=df_netto["Nettojahresgehalt (€)"],
        mode="lines+markers",
        name="Nettojahresgehalt",
    )
)

fig_netto.update_layout(
    title="Nettojahresgehalt in Abhängigkeit vom Bruttogehalt",
    xaxis_title="Bruttogehalt (jährlich, €)",
    yaxis_title="Nettojahresgehalt (€)",
    hovermode="x unified",
)

st.plotly_chart(fig_netto, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# 2. Kapitalerträge
# ─────────────────────────────────────────────────────────────

st.header("2. Kapitalerträge")
with st.expander("Eingaben und Berechnungen"):
    income_capital = st.number_input("Einkommen aus Kapitalerträgen (Brutto in €)", value=1000, min_value=0, step=500)
    wk_capital = st.number_input("Absetzbare Kosten für Kapitalerträge (€)", value=0, min_value=0, step=100)

    taxable_capital = max(income_capital - wk_capital, 0.0)
    tax_capital = taxable_capital * (abgeltung_tax / 100.0)
    net_capital = income_capital - tax_capital

    st.write(f"**Brutto:** {income_capital:,.2f} €")
    st.write(f"**Absetzbare Kosten:** {wk_capital:,.2f} €")
    st.write(f"**Zu versteuerndes Einkommen:** {taxable_capital:,.2f} €")
    st.write(f"**Steuer (Abgeltung {abgeltung_tax}%):** {tax_capital:,.2f} €")
    st.write(f"**Netto:** {net_capital:,.2f} €")

# ─────────────────────────────────────────────────────────────
# 3. Selbständig
# ─────────────────────────────────────────────────────────────

st.header("3. Einkünfte aus selbständiger Arbeit")
with st.expander("Eingaben und Berechnungen"):
    income_self = st.number_input("Bruttoeinnahmen aus selbständiger Arbeit (€)", value=0, min_value=0, step=1000)
    expenses_self = st.number_input("Betriebsausgaben für selbständige Arbeit (€)", value=0, min_value=0, step=100)

    taxable_self = max(income_self - expenses_self, 0.0)
    tax_self = taxable_self * (effective_income_tax / 100.0)
    net_self = income_self - tax_self

    st.write(f"**Bruttoeinnahmen:** {income_self:,.2f} €")
    st.write(f"**Betriebsausgaben:** {expenses_self:,.2f} €")
    st.write(f"**Gewinn/zu versteuerndes Einkommen:** {taxable_self:,.2f} €")
    st.write(f"**Steuer ({effective_income_tax}%):** {tax_self:,.2f} €")
    st.write(f"**Nettoeinkommen:** {net_self:,.2f} €")

# ─────────────────────────────────────────────────────────────
# 4. Gewerbe
# ─────────────────────────────────────────────────────────────

st.header("4. Einkünfte aus Gewerbebetrieb")
with st.expander("Eingaben und Berechnungen"):
    income_trade = st.number_input("Bruttoeinnahmen aus Gewerbebetrieb (€)", value=0, min_value=0, step=1000)
    expenses_trade = st.number_input("Betriebsausgaben für Gewerbebetrieb (€)", value=0, min_value=0, step=100)

    taxable_trade = max(income_trade - expenses_trade, 0.0)
    tax_trade_income = taxable_trade * (effective_income_tax / 100.0)
    gewerbesteuer = taxable_trade * (gewerbesteuer_rate / 100.0)
    tax_trade = tax_trade_income + gewerbesteuer
    net_trade = income_trade - tax_trade

    st.write(f"**Bruttoeinnahmen:** {income_trade:,.2f} €")
    st.write(f"**Betriebsausgaben:** {expenses_trade:,.2f} €")
    st.write(f"**Gewinn/zu versteuerndes Einkommen:** {taxable_trade:,.2f} €")
    st.write(f"**Einkommensteuer ({effective_income_tax}%):** {tax_trade_income:,.2f} €")
    st.write(f"**Gewerbesteuer ({gewerbesteuer_rate}%):** {gewerbesteuer:,.2f} €")
    st.write(f"**Gesamte Steuer:** {tax_trade:,.2f} €")
    st.write(f"**Nettoeinkommen:** {net_trade:,.2f} €")

# ─────────────────────────────────────────────────────────────
# 5. Land- und Forstwirtschaft
# ─────────────────────────────────────────────────────────────

st.header("5. Einkünfte aus Land- und Forstwirtschaft")
with st.expander("Eingaben und Berechnungen"):
    income_agri = st.number_input("Bruttoeinnahmen aus Land- und Forstwirtschaft (€)", value=0, min_value=0, step=1000)
    expenses_agri = st.number_input("Betriebsausgaben für Land- und Forstwirtschaft (€)", value=0, min_value=0, step=100)

    taxable_agri = max(income_agri - expenses_agri, 0.0)
    tax_agri = taxable_agri * (effective_income_tax / 100.0)
    net_agri = income_agri - tax_agri

    st.write(f"**Bruttoeinnahmen:** {income_agri:,.2f} €")
    st.write(f"**Betriebsausgaben:** {expenses_agri:,.2f} €")
    st.write(f"**Gewinn/zu versteuerndes Einkommen:** {taxable_agri:,.2f} €")
    st.write(f"**Steuer ({effective_income_tax}%):** {tax_agri:,.2f} €")
    st.write(f"**Nettoeinkommen:** {net_agri:,.2f} €")

# ─────────────────────────────────────────────────────────────
# 6. Sonstige Einkünfte
# ─────────────────────────────────────────────────────────────

st.header("6. Sonstige Einkünfte (z. B. Renten, Pensionen)")
with st.expander("Eingaben und Berechnungen"):
    income_other = st.number_input("Bruttoeinkünfte aus sonstigen Quellen (z. B. Renten) (€)", value=0, min_value=0, step=500)
    taxable_percent = st.slider("Steuerbarer Anteil dieser Einkünfte (%)", min_value=0, max_value=100, value=50, step=5)

    taxable_other = income_other * (taxable_percent / 100.0)
    tax_other = taxable_other * (effective_income_tax / 100.0)
    net_other = income_other - tax_other

    st.write(f"**Bruttoeinkünfte:** {income_other:,.2f} €")
    st.write(f"**Steuerbarer Anteil:** {taxable_other:,.2f} €")
    st.write(f"**Steuer ({effective_income_tax}% auf den steuerbaren Anteil):** {tax_other:,.2f} €")
    st.write(f"**Nettoeinkommen:** {net_other:,.2f} €")

# ─────────────────────────────────────────────────────────────
# Gesamte Übersicht (konsistent zu den Variablen in diesem Skript)
# ─────────────────────────────────────────────────────────────

st.header("Gesamte Übersicht")

# Für die Arbeit-Kategorie verwenden wir die Jahreswerte aus res_arbeit
brutto_arbeit_jahr = brutto_jahr
abzuege_arbeit = res_arbeit["abzuege_gesamt"]
taxable_arbeit = res_arbeit["zvE"]
tax_arbeit = res_arbeit["einkommensteuer"]
netto_arbeit = res_arbeit["netto_jahr"]

data = {
    "Kategorie": [
        "Nichtselbständige Arbeit (vereinfacht)",
        "Kapitalerträge",
        "Selbständige Arbeit",
        "Gewerbebetrieb",
        "Land- und Forstwirtschaft",
        "Sonstige Einkünfte",
    ],
    "Brutto (€)": [
        brutto_arbeit_jahr,
        income_capital,
        income_self,
        income_trade,
        income_agri,
        income_other,
    ],
    "Abzugsfähige Kosten/Ausgaben (€)": [
        abzuege_arbeit,
        wk_capital,
        expenses_self,
        expenses_trade,
        expenses_agri,
        "–",
    ],
    "Zu versteuerndes Einkommen (€)": [
        taxable_arbeit,
        taxable_capital,
        taxable_self,
        taxable_trade,
        taxable_agri,
        taxable_other,
    ],
    "Steuer (€)": [
        tax_arbeit,
        tax_capital,
        tax_self,
        tax_trade,
        tax_agri,
        tax_other,
    ],
    "Netto (€)": [
        netto_arbeit,
        net_capital,
        net_self,
        net_trade,
        net_agri,
        net_other,
    ],
}

df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True)

st.header("Visualisierung der Ergebnisse")
fig = go.Figure(
    data=[
        go.Bar(name="Brutto", x=df["Kategorie"], y=df["Brutto (€)"]),
        go.Bar(name="Steuer", x=df["Kategorie"], y=df["Steuer (€)"]),
        go.Bar(name="Netto", x=df["Kategorie"], y=df["Netto (€)"]),
    ]
)
fig.update_layout(
    barmode="group",
    title="Steuerliche Übersicht aller Einkunftsarten",
    xaxis_title="Einkunftsart",
    yaxis_title="Betrag in €",
)
st.plotly_chart(fig, use_container_width=True)
