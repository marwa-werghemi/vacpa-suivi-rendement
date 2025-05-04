import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Infos Supabase (prises automatiquement depuis Streamlit Cloud Secrets)
url = st.secrets["supabase_url"] + "/rest/v1/rendements?select=*"
headers = {
    "apikey": st.secrets["supabase_key"],
    "Authorization": f"Bearer {st.secrets['supabase_key']}"
}

st.set_page_config(page_title="Dashboard VACPA", layout="wide")
st.title("📊 Dashboard de Suivi de Rendement - VACPA")

# Récupération des données
@st.cache_data
def charger_donnees():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("❌ Erreur de connexion à Supabase.")
        return pd.DataFrame()

df = charger_donnees()

if not df.empty:

    # 📌 Statistiques globales
    st.subheader("Statistiques Générales")
    col1, col2, col3 = st.columns(3)
    col1.metric("👩‍🔧 Nombre d'opératrices", df["operatrice_id"].nunique())
    col2.metric("⚖️ Poids total (kg)", round(df["poids_kg"].sum(), 2))
    col3.metric("📈 Poids moyen (kg)", round(df["poids_kg"].mean(), 2))

    # 🏆 Top 10 opératrices
    st.subheader("🏅 Top 10 Opératrices par Poids Total")
    top_operatrices = df.groupby("operatrice_id")["poids_kg"].sum().reset_index()
    top_operatrices = top_operatrices.sort_values(by="poids_kg", ascending=False).head(10)

    fig_bar = px.bar(top_operatrices,
                     x="operatrice_id",
                     y="poids_kg",
                     color="poids_kg",
                     color_continuous_scale="greens",
                     labels={"poids_kg": "Poids total (kg)", "operatrice_id": "Opératrice"},
                     title="Top 10 Opératrices")
    st.plotly_chart(fig_bar, use_container_width=True)

    # 💚 Meilleure opératrice
    best = top_operatrices.iloc[0]
    st.success(f"🏆 Meilleure opératrice : **{best['operatrice_id']}** avec **{best['poids_kg']} kg**")

    # 📊 Histogramme complet de toutes les opératrices
    st.subheader("📊 Rendement de Toutes les Opératrices")
    all_operatrices = df.groupby("operatrice_id")["poids_kg"].sum().reset_index()
    fig_all = px.bar(all_operatrices,
                     x="operatrice_id",
                     y="poids_kg",
                     color="poids_kg",
                     color_continuous_scale="greens",
                     title="Rendement Total par Opératrice")
    st.plotly_chart(fig_all, use_container_width=True)

    # 📈 Évolution dans le temps (si tu as une colonne de date, tu peux activer ceci)
    # df['date'] = pd.to_datetime(df['date'])  # décommente si tu ajoutes une colonne "date"
    # st.line_chart(df.groupby("date")["poids_kg"].sum())

    # 📄 Données brutes
    st.subheader("📄 Données brutes")
    st.dataframe(df)

else:
    st.warning("Aucune donnée disponible pour le moment.")
