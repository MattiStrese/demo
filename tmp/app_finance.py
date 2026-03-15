import streamlit as st

# Allgemeine Seiteneinstellungen
st.set_page_config(
    page_title="Immobilien Tools",
    page_icon="🏡",
    layout="wide"
)

st.title("Willkommen beim Immobilien Rechner")
st.markdown("""
Wähle eine Seite in der Seitenleiste, um eine spezifische Berechnung anzuzeigen:
- 💰 Ausgabenreduktion
- 💰 Steuern - EST
- 🏠 Immobilien - Objektdaten
- 📉 Immobilien - Tilgungsplan
- 💰 Immobilien - Kaufnebenkosten
- 💰 Immobilien - Cashflow
- 🏢 Immobilien - Rendite & Wertentwicklung
""")
