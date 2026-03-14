import streamlit as st
import plotly.graph_objects as go

st.title("💰 Detaillierte Cashflow-Berechnung")

# Einnahmen & Kosten
wohnfläche = st.number_input("Wohnfläche (m²)", 
                            min_value=20, 
                            max_value=300, 
                            value=80, 
                            step=5)
miete_pro_qm = st.number_input("Miete pro m² (€)", 
                            min_value=5.0, 
                            max_value=30.0, 
                            value=12.0, 
                            step=0.5)
mietausfallwagnis = st.slider("Mietausfallwagnis (%)", 
                            min_value=0, 
                            max_value=10, 
                            value=1, 
                            step=1)

mieteinnahmen_brutto = wohnfläche * miete_pro_qm * 12
mieteinnahmen_nach_ausfall = mieteinnahmen_brutto * (1.0 - (mietausfallwagnis / 100))

st.write(f"💸 **Mieteinnahmen (nach Ausfall):** {mieteinnahmen_nach_ausfall:,.2f} € / Jahr")
st.write(f"💸 **Mieteinnahmen (nach Ausfall):** {mieteinnahmen_nach_ausfall/12.0:,.2f} € / Monat")


# Darlehensdetails
darlehenssumme = st.number_input("Darlehenssumme (€)", 
                            min_value=100000, 
                            max_value=2000000, 
                            value=100000, 
                            step=5000)
zinssatz = st.slider("Zinssatz (%)", 
                            min_value=0.5, 
                            max_value=10.0, 
                            value=3.0, 
                            step=0.1)
tilgungssatz = st.slider("Tilgungssatz (%)", 
                            min_value=1.0, 
                            max_value=10.0, 
                            value=1.5, 
                            step=0.1)

zins = darlehenssumme * (zinssatz / 100)
tilgung = darlehenssumme * (tilgungssatz / 100)
gesamtkreditbelastung = zins + tilgung

# Steuerliche Aspekte
afa_pro_jahr = st.slider("AfA in % (Standard: 2%)", 
                            min_value=1.0, 
                            max_value=3.0, 
                            value=2.0, 
                            step=0.1)
kaufpreis = st.number_input("Kaufpreis der Immobilie (€)", 
                            min_value=50000, 
                            max_value=2000000, 
                            value=300000, 
                            step=5000)
grundstuecksanteil = st.slider("Anteil Grundstück (%)", 
                            min_value=0, 
                            max_value=50, 
                            value=20, 
                            step=1)

gebaeudeanteil = kaufpreis * (1. - grundstuecksanteil / 100)
afa_jaehrlich = gebaeudeanteil * (afa_pro_jahr / 100)
steuerliche_einkunft = mieteinnahmen_nach_ausfall - gesamtkreditbelastung - afa_jaehrlich
# **NEU: Steuerlast berechnen**
steuersatz = st.slider("Steuersatz (%)", min_value=0, max_value=50, value=30, step=1)
steuerbelastung = max(steuerliche_einkunft * (steuersatz / 100), 0)  # Keine negativen Steuern

# Verwaltungskosten & Rücklagen
verwaltungskosten = st.number_input("Verwaltungskosten (€ / Monat)", 
                            min_value=0, 
                            max_value=500, 
                            value=120, 
                            step=10)
sanierungsruecklage = st.number_input("Sanierungsrücklage (€ / Monat)", 
                            min_value=0, 
                            max_value=1000, 
                            value=wohnfläche, 
                            step=10)

# Gewinnmitnahme
gewinnmitnahme = st.number_input("Einmalige Gewinnmitnahme (€ / Jahr)", min_value=0, max_value=50000, value=0, step=1000)

monatliche_ausgaben = (gesamtkreditbelastung / 12) + verwaltungskosten + sanierungsruecklage
jaehrliche_ausgaben = monatliche_ausgaben * 12
cashflow_vor_steuer = mieteinnahmen_nach_ausfall - jaehrliche_ausgaben + gewinnmitnahme
cashflow_nach_steuer = cashflow_vor_steuer - steuerbelastung

# **Neue Ausgabe: Steuerbelastung**
st.subheader("📌 Steuerlast")
st.write(f"💰 **Jährliche Steuerbelastung:** {steuerbelastung:,.2f} €")
st.write(f"💰 **Monatliche Steuerbelastung:** {steuerbelastung / 12:,.2f} €")

# Ausgabe
st.subheader("📊 Cashflow-Übersicht pro Jahr")
st.write(f"🏠 **Mieteinnahmen (brutto):** {mieteinnahmen_brutto:,.2f} € / Jahr")
st.write(f"💸 **Mieteinnahmen (nach Ausfall):** {mieteinnahmen_nach_ausfall:,.2f} € / Jahr")
st.write(f"🏦 **Zinsbelastung:** {zins:,.2f} € / Jahr")
st.write(f"🏗 **Tilgung:** {tilgung:,.2f} € / Jahr")
st.write(f"📉 **Kreditbelastung:** {gesamtkreditbelastung:,.2f} € / Jahr")
st.write(f"📑 **AfA:** {afa_jaehrlich:,.2f} € / Jahr")
st.write(f"🔧 **Verwaltungskosten:** {verwaltungskosten * 12:,.2f} € / Jahr")
st.write(f"🏗 **Sanierungsrücklage:** {sanierungsruecklage * 12:,.2f} € / Jahr")
st.write(f"💰 **Gewinnmitnahme:** {gewinnmitnahme:,.2f} € / Jahr")
st.write(f"💵 **Cashflow vor Steuern:** {cashflow_vor_steuer:,.2f} € / Jahr")
st.write(f"💵 **Cashflow nach Steuern:** {cashflow_nach_steuer:,.2f} € / Jahr")

st.subheader("📊 Cashflow-Übersicht pro Monat")
st.write(f"💵 **Cashflow vor Steuern:** {cashflow_vor_steuer / 12:,.2f} € / Monat")
st.write(f"💵 **Cashflow nach Steuern:** {cashflow_nach_steuer / 12:,.2f} € / Monat")

# Visualisierung
fig = go.Figure()
fig.add_trace(go.Bar(
    x=["Mieteinnahmen (netto)", "Kreditbelastung", "AfA", "Verwaltung", "Rücklage", "Steuern", "Gewinnmitnahme", "Cashflow (nach Steuer)"],
    y=[mieteinnahmen_nach_ausfall, -gesamtkreditbelastung, -afa_jaehrlich, -verwaltungskosten * 12, -sanierungsruecklage * 12, -steuerbelastung, gewinnmitnahme, cashflow_nach_steuer],
    marker_color=["green", "red", "blue", "red", "red", "purple", "orange", "blue"]
))
fig.update_layout(title="📊 Cashflow-Übersicht nach Steuer", yaxis_title="Betrag (€)")
st.plotly_chart(fig)
