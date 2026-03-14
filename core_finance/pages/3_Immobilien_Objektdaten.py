import streamlit as st
import plotly.graph_objects as go

st.title("🏡 Objektdaten")

# Eingabebereich für Objektdaten
st.sidebar.header("Objektdetails")
kaufpreis: int = st.sidebar.number_input("Kaufpreis (€)",
                                            min_value=50000,
                                            max_value=2000000,
                                            value=200000,
                                            step=5000)
wohnfläche: int = st.sidebar.number_input("Wohnfläche (m²)",
                                            min_value=20,
                                            max_value=300,
                                            value=100,
                                            step=5)
mietpreis_qm: float = st.sidebar.number_input("Miete pro m² (€)",
                                                min_value=5.0,
                                                max_value=30.0,
                                                value=14.0,
                                                step=0.5)

# Berechnungen
miete_jahr: float = 12 *wohnfläche * mietpreis_qm

# Anzeige der Daten
st.write(f"🏠 **Kaufpreis:** {kaufpreis:,.2f} €") 
st.write(f"📏 **Wohnfläche:** {wohnfläche} m²")
st.write(f"💰 **Monatliche Mieteinnahmen:** {miete_jahr:,.2f} €")




bundesland = st.selectbox("Bundesland", [
    "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
    "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
    "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen",
    "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"
])

# Steuersätze (Stand 2024)
steuern = {
    "Baden-Württemberg": 5.0, 
    "Bayern": 3.5, 
    "Berlin": 6.0, 
    "Brandenburg": 6.5,
    "Bremen": 5.0, 
    "Hamburg": 5.5, 
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

# Berechnungen
steuer = kaufpreis * (steuern[bundesland] / 100)

grundbuch = kaufpreis * 0.05
notar = kaufpreis * 0.010
makler = kaufpreis * 0.035
gesamtkosten = kaufpreis + steuer + grundbuch + notar + makler

# Ausgabe
st.write(f"🏢 **Grunderwerbsteuer ({bundesland}):** {steuer:,.2f} €")
st.write(f"📜 **Notarkosten (~1.5%):** {notar:,.2f} €")
st.write(f"📜 **Eintragung Grundbuch (~0.5%):** {grundbuch:,.2f} €")
st.write(f"🏢 **Maklergebühr (~3.5%):** {makler:,.2f} €")
st.write(f"💰 **Gesamtkosten:** {gesamtkosten:,.2f} €")

# Visualisierung
fig = go.Figure(data=[go.Bar(x=["Steuer", 
                                "Notar", 
                                "Makler"],
                             y=[steuer,
                                notar, 
                                makler ])])

fig.update_layout(title="📊 Kaufnebenkosten Übersicht")
st.plotly_chart(fig)

# Grafik: Mieteinnahmen vs. Preis
fig = go.Figure()
fig.add_trace(go.Bar(x=["Jahresmieteinnahmen", 
                        "Kaufpreis"],
                     y=[miete_jahr, gesamtkosten],
                     marker_color=["green", 
                                   "blue"]))
fig.update_layout(title="📊 Verhältnis von Kaufpreis und Mieteinnahmen",
                  yaxis_title="€")
st.plotly_chart(fig)