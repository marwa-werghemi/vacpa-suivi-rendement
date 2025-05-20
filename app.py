# 📦 Modules requis
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# ⚙️ Configuration de la page
st.set_page_config(page_title="Suivi de rendement VACPA", layout="wide")

# 🛡️ Authentification simple
MOT_DE_PASSE = "vacpa2025"
if "connecte" not in st.session_state:
    st.session_state.connecte = False
if not st.session_state.connecte:
    st.title("🔐 Accès sécurisé")
    mot_de_passe = st.text_input("Entrez le mot de passe", type="password")
    if mot_de_passe == MOT_DE_PASSE:
        st.success("Accès autorisé")
        st.session_state.connecte = True
    elif mot_de_passe:
        st.error("Mot de passe incorrect")
    st.stop()

# 🔌 Connexion Supabase
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
TABLE_NAME = "rendements"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# 🔁 Charger les données
@st.cache_data(ttl=60)
def charger_donnees():
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*", headers=headers)
    if r.status_code == 200:
        df = pd.DataFrame(r.json())
        if not df.empty:
            df["rendement"] = df["poids_kg"] / df["temps_min"] * 60  # kg/h
        return df
    else:
        st.error("Erreur lors du chargement des données.")
        return pd.DataFrame()

if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()

df = charger_donnees()

# ➕ Ajout de rendement
st.subheader("Ajouter un nouveau rendement")
with st.form("ajout"):
    col1, col2 = st.columns(2)
    with col1:
        operatrice_id = st.text_input("ID Opératrice")
        poids = st.number_input("Poids (kg)", min_value=0.0)
    with col2:
        heures = st.number_input("Heures", min_value=0)
        minutes = st.number_input("Minutes", min_value=0, max_value=59)

    if st.form_submit_button("Ajouter"):
        temps = heures * 60 + minutes
        data = {"operatrice_id": operatrice_id, "poids_kg": poids, "temps_min": temps}
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers={**headers, "Content-Type": "application/json"}, json=data)
        if r.status_code == 201:
            st.success("Rendement ajouté")
            st.cache_data.clear()
        else:
            st.error("Erreur lors de l'ajout")

# 📊 Tableau + Export
st.subheader("Données enregistrées")
if not df.empty:
    # Filtres
    operatrice_filter = st.multiselect("Filtrer par ID", options=sorted(df["operatrice_id"].unique()))
    if operatrice_filter:
        df = df[df["operatrice_id"].isin(operatrice_filter)]

    st.dataframe(df, use_container_width=True)

    # Export
    def export_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Rendement")
        return output.getvalue()

    st.download_button("⬇️ Exporter Excel", data=export_excel(df), file_name="rendement.xlsx")

    # Statistiques
    st.subheader("Statistiques globales")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total KG", f"{df['poids_kg'].sum():.2f} kg")
    col2.metric("Durée Totale", f"{df['temps_min'].sum():.0f} min")
    col3.metric("Rendement Moyen", f"{df['rendement'].mean():.2f} kg/h")
    col4.metric("Max Rendement", f"{df['rendement'].max():.2f} kg/h")

    # 📉 Graphique rendement par opératrice
    st.subheader("Classement des opératrices")
    top = df.groupby("operatrice_id")["poids_kg"].sum().sort_values(ascending=False).head(10)
    fig = px.bar(top, x=top.index, y=top.values, labels={"x": "Opératrice", "y": "Poids Total (kg)"}, title="Top 10 des opératrices")
    st.plotly_chart(fig, use_container_width=True)

    # 📉 Evolution du rendement
    st.subheader("Évolution du rendement")
    df_time = df.copy()
    df_time["horodatage"] = pd.to_datetime(df_time["created_at"], errors="coerce")
    df_time = df_time.dropna(subset=["horodatage"])
    fig2 = px.line(df_time.sort_values("horodatage"), x="horodatage", y="rendement", color="operatrice_id", title="Rendement dans le temps")
    st.plotly_chart(fig2, use_container_width=True)

# 🔚 Quitter
if st.button("🚪 Quitter l'application"):
    st.stop()


