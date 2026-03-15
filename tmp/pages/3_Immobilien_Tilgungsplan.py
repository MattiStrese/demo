import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("📉 Tilgungsplan mit Sondertilgungen")

# Eingaben
darlehenssumme = st.number_input("Darlehenssumme (€)", 
                                 min_value=10000, 
                                 max_value=2000000, 
                                 value=36000, 
                                 step=5000)
# Eingaben
disagio = st.number_input("Disagio (€)", 
                                 min_value=5000, 
                                 max_value=20000, 
                                 value=10000, 
                                 step=5000)
darlehenssumme += disagio
zinssatz = st.slider("Zinssatz (%)", 
                     min_value=0.5,
                     max_value=10.0, 
                     value=3.88, 
                     step=0.1)
monatliche_rate = st.slider("Monatliche Annuität (€)", 
                            min_value=1000,
                            max_value=5000, 
                            value=1470, 
                            step=50)

# tilgungssatz = st.slider("Anfänglicher Tilgungssatz (%)", min_value=1.0, max_value=10.0, value=2.0, step=0.1)
laufzeit = st.slider("Laufzeit (Jahre)", min_value=5, max_value=40, value=25)
#sondertilgung = st.number_input("Jährliche Sondertilgung (€)", min_value=0, max_value=50000, value=0, step=500)

# Berechnung
zins = zinssatz / 100
tilgung = (monatliche_rate * 12) - (zins * darlehenssumme)
#monatliche_rate = darlehenssumme * (zins + tilgung) / 12

st.subheader("Individuelle Sondertilgungen pro Jahr")
sondertilgungen = {}
for jahr in range(1, laufzeit + 1):
    sondertilgungen[jahr] = st.number_input(f"Sondertilgung für Jahr {jahr} (€)", 
                                            min_value=0, 
                                            max_value=50000, 
                                            value=0, 
                                            step=500)


jahre = []
restschuld = []
zinszahlungen = []
tilgungszahlungen = []
zinszahlungen_monat = []
tilgungszahlungen_monat = []

S_n = darlehenssumme
jahr = 1

while S_n > 0 and jahr <= laufzeit:
    zinszahlung_jahr = S_n * zins
    tilgungszahlung_jahr = 12 * monatliche_rate - zinszahlung_jahr
    sondertilgung = sondertilgungen.get(jahr, 0)
    gesamt_tilgung = tilgungszahlung_jahr + sondertilgung

    if S_n - gesamt_tilgung < 0:
        gesamt_tilgung = S_n

    S_n -= gesamt_tilgung

    jahre.append(jahr)
    restschuld.append(max(0, S_n))
    zinszahlungen.append(zinszahlung_jahr)
    tilgungszahlungen.append(gesamt_tilgung)
    zinszahlungen_monat.append(int(zinszahlung_jahr/12))
    tilgungszahlungen_monat.append(int(gesamt_tilgung/12))
    jahr += 1

# DataFrame
tilgungsplan = pd.DataFrame({"Jahr": jahre,
                             "Restschuld (€)": restschuld,
                             "Zinsen pro Monat (€)": zinszahlungen_monat,
                             "Tilgung inkl. Sondertilgung pro Monat (€)": tilgungszahlungen_monat})

st.subheader("Tilgungsplan")
st.dataframe(tilgungsplan)

# Visualisierung
fig = go.Figure()
fig.add_trace(go.Scatter(x=jahre, y=restschuld, mode='lines', name='Restschuld', line=dict(color='red')))
fig.add_trace(go.Scatter(x=jahre, y=zinszahlungen, mode='lines', name='Zinszahlungen', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=jahre, y=tilgungszahlungen, mode='lines', name='Tilgung inkl. Sondertilgung', line=dict(color='green')))
fig.update_layout(title="📉 Tilgungsplan mit Sondertilgungen", xaxis_title="Jahr", yaxis_title="Betrag (€)")
st.plotly_chart(fig)

st.subheader("Neue Laufzeit")
st.write(f"🕒 Das Darlehen ist nach {len(jahre)} Jahren abbezahlt (statt {laufzeit} Jahre).")
