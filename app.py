import streamlit as st
import pandas as pd
import requests

# Chargement des secrets Streamlit
supabase_url = st.secrets["supabase_url"]
supabase_key = st.secrets["supabase_key"]

headers = {
    "apikey": supabase_key,
    "Authorization": f"Bearer {supabase_key}"
}

# URL d'accès à la table rendements
data_url = f"{supabase_url}/rest/v1/rendements?select=*"

st.title("Suivi de rendement - VACPA")

@st.cache_data
def charger_donnees():
    response = requests.get(data_url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("❌ Erreur de connexion à Supabase.")
        return pd.DataFrame()

df = charger_donnees()

# Affichage des données
if not df.empty:
    st.success("✅ Données chargées avec succès !")
    st.write("### 📊 Données de rendement :")
    st.dataframe(df)

    st.write("### 🔝 Top 10 opératrices par poids total (kg)")
    top10 = df.groupby("operatrice_id")["poids_kg"].sum().sort_values(ascending=False).head(10)
    st.bar_chart(top10)

    st.write("### 🥇 Meilleure opératrice")
    best_id = top10.idxmax()
    best_value = top10.max()
    st.markdown(f"<h3 style='color: green'>ID : {best_id} avec {best_value} kg</h3>", unsafe_allow_html=True)

else:
    st.warning("⚠️ Aucune donnée disponible pour le moment.")
