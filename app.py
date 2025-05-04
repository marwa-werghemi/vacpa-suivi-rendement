import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ⛔️ Masquer les warnings Streamlit
st.set_option('deprecation.showfileUploaderEncoding', False)

# 🎯 Titre principal
st.title("📊 Suivi de rendement - VACPA")

# 🔐 Connexion à Supabase via secrets
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
TABLE_NAME = "rendements"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# 🔁 Fonction pour charger les données
@st.cache_data(ttl=60)
def charger_donnees():
    response = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*", headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("❌ Erreur de connexion à Supabase.")
        return pd.DataFrame()

# 📌 Bouton d'actualisation
if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()

# ✅ Chargement des données
df = charger_donnees()

# 📤 Bouton d'export Excel
def exporter_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Rendement')
    st.download_button("⬇️ Exporter en Excel", output.getvalue(), file_name="rendement.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# 📅 Formulaire d'ajout de données
st.subheader("➕ Ajouter un nouveau rendement")

with st.form("formulaire_rendement"):
    operatrice_id = st.text_input("ID opératrice")
    poids_kg = st.number_input("Poids (kg)", min_value=0.0, step=0.1)
    heures = st.number_input("Heures travaillées", min_value=0, step=1)
    minutes = st.number_input("Minutes travaillées", min_value=0, max_value=59, step=1)

    submitted = st.form_submit_button("✅ Ajouter")

    if submitted:
        temps_minutes = heures * 60 + minutes
        new_data = {
            "operatrice_id": operatrice_id,
            "poids_kg": poids_kg,
            "temps_min": temps_minutes
        }
        insert_response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers={**headers, "Content-Type": "application/json"}, json=new_data)
        if insert_response.status_code == 201:
            st.success("✅ Rendement ajouté avec succès !")
            st.cache_data.clear()
        else:
            st.error("❌ Échec de l'ajout.")

# 🧾 Affichage des données
st.subheader("📄 Données de rendement")
if not df.empty:
    st.dataframe(df)
    exporter_excel(df)

    # 🏆 Top 10 opératrices
    st.subheader("🏅 Top 10 des opératrices (poids total)")
    top_10 = df.groupby("operatrice_id")["poids_kg"].sum().sort_values(ascending=False).head(10)
    st.bar_chart(top_10)

    meilleure = top_10.idxmax()
    st.success(f"🌟 Meilleure opératrice : **{meilleure}** avec **{top_10.max():.2f} kg**")

# 🔚 Bouton Quitter
if st.button("🚪 Quitter l’application"):
    st.stop()
