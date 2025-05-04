import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# 🎯 Config Streamlit
st.set_page_config(page_title="Dashboard VACPA", layout="wide")
st.title("📊 Dashboard de Suivi de Rendement - VACPA")

# 🔐 Connexion Supabase via secrets
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
TABLE = "rendements"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# 📥 Charger données
@st.cache_data
def charger_donnees():
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return pd.DataFrame(r.json())
    else:
        st.error("❌ Erreur de connexion à Supabase.")
        return pd.DataFrame()

df = charger_donnees()

# 🧾 Ajouter des données
with st.expander("➕ Ajouter un rendement manuellement"):
    with st.form("form_rendement"):
        operatrice_id = st.text_input("ID opératrice")
        poids_kg = st.number_input("Poids (kg)", min_value=0.0, step=0.1)
        date_saisie = st.date_input("Date", value=datetime.today())
        envoyer = st.form_submit_button("📤 Enregistrer")

        if envoyer and operatrice_id and poids_kg > 0:
            new_data = {
                "operatrice_id": operatrice_id,
                "poids_kg": poids_kg,
                "date": str(date_saisie)
            }
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/{TABLE}",
                json=new_data,
                headers=headers
            )
            if response.status_code in [200, 201]:
                st.success("✅ Donnée ajoutée avec succès ! Recharge la page pour voir les résultats.")
            else:
                st.error(f"❌ Échec de l'ajout ({response.status_code})")

# 🧹 Nettoyage des données
if not df.empty:
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')

    # 🎛️ Filtres
    st.sidebar.header("🔎 Filtres")
    operatrices = df["operatrice_id"].unique()
    choix_operatrice = st.sidebar.multiselect("Filtrer par opératrice", operatrices, default=operatrices)

    if "date" in df.columns:
        min_date = df["date"].min()
        max_date = df["date"].max()
        date_range = st.sidebar.date_input("Filtrer par date", [min_date, max_date])
        if len(date_range) == 2:
            df = df[(df["date"] >= pd.to_datetime(date_range[0])) & (df["date"] <= pd.to_datetime(date_range[1]))]

    # Appliquer filtres
    df = df[df["operatrice_id"].isin(choix_operatrice)]

    # 📌 Statistiques globales
    st.subheader("📊 Statistiques Globales")
    col1, col2, col3 = st.columns(3)
    col1.metric("👩‍🔧 Opératrices", df["operatrice_id"].nunique())
    col2.metric("⚖️ Total Poids (kg)", round(df["poids_kg"].sum(), 2))
    col3.metric("📈 Poids Moyen", round(df["poids_kg"].mean(), 2))

    # 🏆 Top 10
    top = df.groupby("operatrice_id")["poids_kg"].sum().sort_values(ascending=False).head(10).reset_index()
    st.subheader("🏅 Top 10 Opératrices")
    fig_top = px.bar(top, x="operatrice_id", y="poids_kg", color="poids_kg",
                     color_continuous_scale="greens", title="Top 10 - Poids Total")
    st.plotly_chart(fig_top, use_container_width=True)

    # 💚 Meilleure opératrice
    best = top.iloc[0]
    st.success(f"🏆 Meilleure opératrice : **{best['operatrice_id']}** avec **{best['poids_kg']} kg**")

    # 📊 Histogramme global
    st.subheader("📊 Rendement par opératrice")
    all_op = df.groupby("operatrice_id")["poids_kg"].sum().reset_index()
    fig_all = px.bar(all_op, x="operatrice_id", y="poids_kg", color="poids_kg",
                     color_continuous_scale="greens", title="Histogramme complet")
    st.plotly_chart(fig_all, use_container_width=True)

    # 📈 Évolution dans le temps
    if "date" in df.columns:
        st.subheader("📅 Évolution quotidienne du rendement")
        line_df = df.groupby("date")["poids_kg"].sum().reset_index()
        fig_line = px.line(line_df, x="date", y="poids_kg", title="Poids total par jour", markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

    # 📄 Données brutes
    st.subheader("📄 Données brutes filtrées")
    st.dataframe(df)

else:
    st.warning("Aucune donnée disponible.")
