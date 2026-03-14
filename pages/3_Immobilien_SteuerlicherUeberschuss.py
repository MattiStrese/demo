import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Titel und Einführung
st.title("Einkunftsüberschussrechnung für eine Immobilie")
st.markdown("""
Diese Seite ermöglicht es dir, interaktiv den steuerlichen Überschuss deiner Immobilie zu berechnen. Dabei werden die Einnahmen sowie verschiedene Werbungskosten berücksichtigt:
- **Raumkosten**
- **Instandhaltungskosten**
- **Abschreibungen (Gebäude & Möbel)**
- **Verschiedene Kosten**
- **Zinskosten** (falls ein Kredit besteht)
Am Ende wird der steuerliche Überschuss ermittelt und, bei Angabe eines Steuersatzes, die daraus resultierenden Steuerkosten in Euro berechnet.
""")

# Auswahl: Berechnung pro Monat oder Jahr
modus = st.selectbox("Berechnung für:", ["Monat", "Jahr"])

# Umrechnungsfaktor
if modus == "Monat":
    faktor = 1
    faktor_12 = 12
else:
    faktor = 12
    faktor_12 = 1

# Eingaben
st.header("Eingaben")

st.subheader("1. Einnahmen")
mieteinnahmen: float = st.number_input(f"Mieteinnahmen pro {modus} (in €)", value=852 * faktor, min_value=0, step=10)
nebenkosten_vorauszahlung: float = st.number_input(f"Nebenkostenvorauszahlung pro {modus} (in €)", value=120 * faktor, min_value=0, step=10)
mieteinnahmen += nebenkosten_vorauszahlung
st.write(f"**Gesamte Einnahmen pro {modus}:** {mieteinnahmen:,.2f} €")


st.subheader("2. Werbungskosten")
hausgeld: float = st.number_input(f"Hausgeld pro {modus} (in €)", value=0 * faktor, min_value=0, step=50)
instandhaltung: float = st.number_input(f"Instandhaltungskosten pro {modus} (in €)", value=100 * faktor, min_value=0, step=10)

# Abschreibung berechnen
kaufpreis: float = st.number_input("Kaufpreis Gebäude für Abschreibung (in €)", value=200000, min_value=0, step=1000)
afa_satz: float = 2.0  # 2 % pro Jahr
abschreibungen_gebaeude_pro_jahr: float = kaufpreis * (afa_satz / 100.0)
abschreibungen_gebaeude: float = abschreibungen_gebaeude_pro_jahr / faktor_12
st.write(f"**Abschreibungen Gebäude:** {abschreibungen_gebaeude:,.2f} € / {modus}")

abschreibungen_moebel: float = st.number_input(f"Abschreibungen Möbel pro {modus} (in €)", value=100 * faktor, min_value=0, step=10)
sonstige_kosten: float = st.number_input(f"Verschiedene Kosten pro {modus} (in €)", value=30 * faktor, min_value=0, step=50)

credit: bool = st.checkbox("Besteht ein Kredit?")
zinskosten: float = st.number_input(f"Zinskosten pro {modus} (in €)", value=100 * faktor if credit else 0, min_value=0, step=50) if credit else 0

# Berechnungen
gesamtwerbungskosten: float = hausgeld + instandhaltung + abschreibungen_gebaeude + abschreibungen_moebel + sonstige_kosten + zinskosten
steuerlicher_ueberschuss: float = mieteinnahmen - gesamtwerbungskosten

st.header("Berechnungen")
st.write(f"**Steuerlicher Überschuss pro {modus}:** {steuerlicher_ueberschuss:,.2f} €")

st.subheader("Steuerliche Belastung")
steuersatz: float = st.slider("Effektiver Steuersatz (in %)", min_value=0, max_value=50, value=30, step=1)
steuerkosten: float = steuerlicher_ueberschuss * (steuersatz / 100.0)
st.write(f"**Steuerkosten pro {modus}:** {steuerkosten:,.2f} €")

# Neue Übersichten:
# Übersicht Einnahmen & Ausgaben
st.header(f"Übersicht der Einnahmen und Ausgaben ({modus})")
st.write(f"**Gesamte Einnahmen pro {modus}:** {mieteinnahmen:,.2f} €")
st.write(f"**Gesamte Ausgaben pro {modus}:** {gesamtwerbungskosten:,.2f} €")

# Tabellenübersicht
st.header(f"Übersicht für {modus}")
data: dict[str, list] = {
    "Position": [
        "Mieteinnahmen",
        "Hausgeld",
        "Instandhaltungskosten",
        "Abschreibungen Gebäude",
        "Abschreibungen Möbel",
        "Verschiedene Kosten",
        "Zinskosten",
        "Gesamt Werbungskosten",
        "Steuerlicher Überschuss",
        "Steuersatz (%)",
        "Steuerkosten"
    ],
    "Betrag (€)": [
        mieteinnahmen,
        hausgeld,
        instandhaltung,
        abschreibungen_gebaeude,
        abschreibungen_moebel,
        sonstige_kosten,
        zinskosten,
        gesamtwerbungskosten,
        steuerlicher_ueberschuss,
        steuersatz,
        steuerkosten
    ]
}
df: pd.DataFrame = pd.DataFrame(data)
st.dataframe(df)

# Visualisierungen
st.header("Visualisierungen")

# 1. Aufschlüsselung der Werbungskosten
kosten_labels: list[str] = [
    "Hausgeld",
    "Instandhaltung",
    "Abschr. Gebäude",
    "Abschr. Möbel",
    "Verschiedene Kosten",
    "Zinskosten"
]
kosten_values: list[float] = [
    hausgeld,
    instandhaltung,
    abschreibungen_gebaeude,
    abschreibungen_moebel,
    sonstige_kosten,
    zinskosten
]

fig1: go.Figure = go.Figure()
fig1.add_trace(go.Bar(x=kosten_labels, y=kosten_values, name="Werbungskosten"))
fig1.update_layout(
    title=f"Aufschlüsselung der Werbungskosten ({modus})",
    xaxis_title="Kostenart",
    yaxis_title="Betrag in €"
)
st.plotly_chart(fig1)

# 2. Vergleich: Einnahmen, Werbungskosten, Überschuss und Steuerkosten
categories: list[str] = ["Mieteinnahmen", "Gesamt Werbungskosten", "Steuerlicher Überschuss", "Steuerkosten"]
values: list[float] = [mieteinnahmen, gesamtwerbungskosten, steuerlicher_ueberschuss, steuerkosten]

fig2: go.Figure = go.Figure()
fig2.add_trace(go.Bar(x=categories, y=values, name="Beträge"))
fig2.update_layout(
    title=f"Vergleich: Einnahmen, Werbungskosten, Überschuss und Steuerkosten ({modus})",
    xaxis_title="Position",
    yaxis_title="Betrag in €"
)
st.plotly_chart(fig2)
