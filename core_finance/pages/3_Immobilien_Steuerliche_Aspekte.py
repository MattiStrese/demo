import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("💼 Steuerliche Aspekte")

st.markdown("""
In diesem Bereich erhältst du einen Überblick über die steuerlichen Vorteile einer Immobilieninvestition.
Berechnet werden:
- Der Gebäudeanteil (Kaufpreis abzüglich Grundstücksanteil)
- Die jährliche Abschreibung (AfA) basierend auf dem Gebäudeanteil und dem gewählten AfA-Satz
- Die jährliche Steuerersparnis bei einem angegebenen Einkommensteuersatz
- Eine Übersicht der kumulativen AfA und der daraus resultierenden Steuerersparnis über einen bestimmten Zeitraum
""")

# Eingaben
kaufpreis = st.number_input("Kaufpreis der Immobilie (€)", min_value=50000, max_value=2000000, value=300000, step=5000)
grundstueck_anteil = st.slider("Anteil Grundstück (%)", min_value=0, max_value=50, value=20, step=1)
afa_rate = st.slider("AfA-Satz (%)", min_value=1.0, max_value=5.0, value=2.0, step=0.1)
einkommensteuersatz = st.slider("Einkommensteuersatz (%)", min_value=0, max_value=50, value=30, step=1)
afa_dauer = st.slider("AfA-Dauer (Jahre)", min_value=1, max_value=50, value=50)

# Berechnungen
gebaeudewert = kaufpreis * (1 - grundstueck_anteil / 100)
afa_jahr = gebaeudewert * (afa_rate / 100)
steuerersparnis_jahr = afa_jahr * (einkommensteuersatz / 100)

st.subheader("Ergebnisse")
st.write(f"🏢 **Gebäudeanteil:** {gebaeudewert:,.2f} €")
st.write(f"📉 **Jährliche AfA:** {afa_jahr:,.2f} €")
st.write(f"💸 **Jährliche Steuerersparnis (bei {einkommensteuersatz}% Steuersatz):** {steuerersparnis_jahr:,.2f} €")

# Berechnung kumulativer Werte
jahre = list(range(1, afa_dauer + 1))
kumulative_afa = []
kumulative_steuerersparnis = []
for jahr in jahre:
    # Die kumulative AfA darf den Gebäudeanteil nicht überschreiten.
    kumuliert = min(afa_jahr * jahr, gebaeudewert)
    kumulative_afa.append(kumuliert)
    kumulative_steuerersparnis.append(kumuliert * (einkommensteuersatz / 100))

# DataFrame zur Übersicht
df = pd.DataFrame({
    "Jahr": jahre,
    "Kumulative AfA (in €)": kumulative_afa,
    "Kumulative Steuerersparnis (in €)": kumulative_steuerersparnis
})
st.dataframe(df)

# Visualisierung
fig = go.Figure()
fig.add_trace(go.Scatter(x=jahre, y=kumulative_afa, mode='lines+markers', name='Kumulative AfA'))
fig.add_trace(go.Scatter(x=jahre, y=kumulative_steuerersparnis, mode='lines+markers', name='Kumulative Steuerersparnis'))
fig.update_layout(
    title="Entwicklung der AfA und Steuerersparnis über die Jahre",
    xaxis_title="Jahr",
    yaxis_title="Betrag (€)"
)
st.plotly_chart(fig)
