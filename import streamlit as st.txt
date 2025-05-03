import streamlit as st
import pandas as pd
import requests

# Infos Supabase
url = "https://pavndhlnvfwoygmatqys.supabase.co"
headers = {
    "apikey": "TA_CLE_ANON",
    "Authorization": "Bearer TA_CLE_ANON"
}

st.title("Suivi de rendement - VACPA")

# Récupération des données
@st.cache_data
def charger_donnees():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("Erreur de connexion à Supabase.")
        return pd.DataFrame()

df = charger_donnees()

# Affichage
st.write("Données de rendement :")
st.dataframe(df)

# Graphique
if not df.empty:
    st.bar_chart(df.groupby("operatrice_id")["poids_kg"].sum())
