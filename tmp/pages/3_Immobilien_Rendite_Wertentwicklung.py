import streamlit as st
import plotly.graph_objects as go

st.title("🏢 Rendite & Wertentwicklung")

# Eingaben
kaufpreis = st.number_input("Kaufpreis der Immobilie (€)", min_value=50000, max_value=2000000, value=300000, step=5000)
nebenkosten_prozent = st.slider("Kaufnebenkosten (% vom Kaufpreis)", min_value=1.0, max_value=15.0, value=10.0, step=0.5)
jahresmiete = st.number_input("Jahreskaltmiete (€)", min_value=5000, max_value=100000, value=14400, step=500)
betriebskosten = st.number_input("Betriebskosten pro Jahr (€)", min_value=0, max_value=20000, value=3000, step=100)

# Renditeberechnungen
bruttomietrendite = (jahresmiete / kaufpreis) * 100
gesamtnebenkosten = kaufpreis * (nebenkosten_prozent / 100)
nettomietrendite = ((jahresmiete - betriebskosten) / (kaufpreis + gesamtnebenkosten)) * 100

st.subheader("Rendite-Berechnungen")
st.write(f"📊 **Bruttomietrendite:** {bruttomietrendite:.2f} %")
st.write(f"📊 **Nettomietrendite:** {nettomietrendite:.2f} %")

# Wertentwicklung
jahre_haltedauer = st.slider("Geplante Haltedauer (Jahre)", min_value=1, max_value=40, value=10)
wertsteigerung = st.slider("Jährliche Wertsteigerung (%)", min_value=-5.0, max_value=10.0, value=2.0, step=0.1)
zukuenftiger_wert = kaufpreis * ((1 + wertsteigerung / 100) ** jahre_haltedauer)

st.subheader("Wertentwicklung")
st.write(f"🏡 **Aktueller Kaufpreis:** {kaufpreis:,.2f} €")
st.write(f"📈 **Geschätzter Wert nach {jahre_haltedauer} Jahren:** {zukuenftiger_wert:,.2f} €")

# Gesamtrendite (ROI)
gesamt_netto_miete = (jahresmiete - betriebskosten) * jahre_haltedauer
gesamtinvestition = kaufpreis + gesamtnebenkosten
verkaufserloes = zukuenftiger_wert
verkaufsgewinn = verkaufserloes - kaufpreis
gesamtgewinn = verkaufsgewinn + gesamt_netto_miete
roi = (gesamtgewinn / gesamtinvestition) * 100

st.subheader("Gesamtrendite (ROI)")
st.write(f"💰 **Kumulierte Nettomieteinnahmen:** {gesamt_netto_miete:,.2f} € über {jahre_haltedauer} Jahre")
st.write(f"💰 **Gesamtinvestition:** {gesamtinvestition:,.2f} €")
st.write(f"💰 **Verkaufsgewinn:** {verkaufsgewinn:,.2f} €")
st.write(f"💰 **Gesamtgewinn:** {gesamtgewinn:,.2f} €")
st.write(f"📊 **ROI:** {roi:.2f} %")

# Visualisierung der Wertentwicklung
jahre_liste = list(range(0, jahre_haltedauer + 1))
werte_liste = [kaufpreis * ((1 + wertsteigerung / 100) ** jahr) for jahr in jahre_liste]

fig = go.Figure()
fig.add_trace(go.Scatter(x=jahre_liste, y=werte_liste, mode='lines+markers', name="Immobilienwert"))
fig.update_layout(title="📈 Entwicklung des Immobilienwertes", xaxis_title="Jahre", yaxis_title="Wert (€)")
st.plotly_chart(fig)
