import streamlit as st
import pandas as pd
import requests

# Lecture des infos Supabase depuis les secrets
url = st.secrets["supabase_url"]
headers = {
    "apikey": st.secrets["supabase_key"],
    "Authorization": f"Bearer {st.secrets['supabase_key']}"
}

st.title("📊 Suivi de rendement - VACPA")

# Récupération des données
@st.cache_data
def charger_donnees():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            return pd.DataFrame(response.json())
        except Exception as e:
            st.error(f"Erreur lors de la conversion des données : {e}")
            return pd.DataFrame()
    else:
        st.error("❌ Erreur de connexion à Supabase.")
        return pd.DataFrame()

df = charger_donnees()

# Affichage des données
st.write("### Données de rendement :")
st.dataframe(df)

# Graphique si données disponibles
if not df.empty and "operatrice_id" in df.columns and "poids_kg" in df.columns:
    st.write("### Rendement par opératrice (somme des poids)")
    st.bar_chart(df.groupby("operatrice_id")["poids_kg"].sum())
else:
    st.warning("Colonnes 'operatrice_id' ou 'poids_kg' manquantes dans les données.")
