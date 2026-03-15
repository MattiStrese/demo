import streamlit as st

# Grunderwerbsteuersätze der deutschen Bundesländer (Stand: aktuell üblich)
steuersätze = {
    "Baden-Württemberg": 5.0,
    "Bayern": 3.5,
    "Berlin": 6.0,
    "Brandenburg": 6.5,
    "Bremen": 5.0,
    "Hamburg": 4.5,
    "Hessen": 6.0,
    "Mecklenburg-Vorpommern": 6.0,
    "Niedersachsen": 5.0,
    "Nordrhein-Westfalen": 6.5,
    "Rheinland-Pfalz": 5.0,
    "Saarland": 6.5,
    "Sachsen": 3.5,
    "Sachsen-Anhalt": 5.0,
    "Schleswig-Holstein": 6.5,
    "Thüringen": 6.5
}

st.title("🏠 Grunderwerbsteuer Rechner")

# Nutzereingaben
kaufpreis = st.number_input("Kaufpreis der Immobilie (€)", min_value=50000, max_value=5000000, value=300000, step=10000)
moebelwert = st.number_input("Wert der Möbel (€)", min_value=0, max_value=50000, value=10000, step=1000)
instandhaltungskosten = st.number_input("Instandhaltungskosten (€)", min_value=0, max_value=50000, value=5000, step=1000)

bundesland = st.selectbox("Bundesland wählen", list(steuersätze.keys()))

# Berechnung der Grunderwerbsteuer
steuerbasis = max(0, kaufpreis - moebelwert - instandhaltungskosten)
steuersatz = steuersätze[bundesland]
grunderwerbsteuer = steuerbasis * (steuersatz / 100)

# Ausgabe der Ergebnisse
st.subheader("Ergebnisse")
st.write(f"📌 Steuerpflichtiger Betrag: {steuerbasis:,.2f} €")
st.write(f"💰 Steuersatz für {bundesland}: {steuersatz} %")
st.write(f"🏡 Grunderwerbsteuer: {grunderwerbsteuer:,.2f} €")
