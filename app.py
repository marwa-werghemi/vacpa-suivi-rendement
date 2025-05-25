import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# 🌿 Design & configuration de page
st.set_page_config(page_title="Suivi de rendement VACPA", layout="wide", page_icon="🌴")

# 🌿 Couleurs
VERT_FONCE = "#1b4332"
VERT_CLAIR = "#d8f3dc"
VERT_MOYEN = "#52b788"

# 🔐 Authentification simple
MOT_DE_PASSE = "vacpa2025"
if "connecte" not in st.session_state:
    st.session_state.connecte = False
if not st.session_state.connecte:
    st.markdown(f"<h2 style='color:{VERT_FONCE}'>🔐 Accès sécurisé</h2>", unsafe_allow_html=True)
    mdp = st.text_input("Entrez le mot de passe", type="password")
    if mdp == MOT_DE_PASSE:
        st.session_state.connecte = True
        st.success("✅ Accès autorisé")
    elif mdp:
        st.error("❌ Mot de passe incorrect")
    st.stop()

# 🔗 Supabase (tes infos)
SUPABASE_URL = "https://pavndhlnvfwoygmatqys.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdm5kaGxudmZ3b3lnbWF0cXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYzMDYyNzIsImV4cCI6MjA2MTg4MjI3Mn0.xUMJfDZdjZkTzYdz0MgZ040IdT_cmeJSWIDZ74NGt1k"
TABLE = "rendements"
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

@st.cache_data(ttl=60)
def charger_donnees():
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*", headers=headers)
    return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()

if st.button("🔄 Recharger les données"):
    st.cache_data.clear()

df = charger_donnees()

# 🏷️ Titre
st.markdown(f"<h1 style='color:{VERT_FONCE}'>🌴 Suivi du Rendement - VACPA</h1>", unsafe_allow_html=True)

# 🌟 Statistiques globales
st.subheader("📊 Statistiques globales")
if not df.empty:
    df["temps_min"] = df["temps_min"].astype(float)
    df["poids_kg"] = df["poids_kg"].astype(float)
    df["rendement"] = df["poids_kg"] / (df["temps_min"] / 60)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total KG", f"{df['poids_kg'].sum():.2f} kg")
    col2.metric("Durée Totale", f"{df['temps_min'].sum():.0f} min")
    col3.metric("Rendement Moyen", f"{df['rendement'].mean():.2f} kg/h")
    col4.metric("Max Rendement", f"{df['rendement'].max():.2f} kg/h")
else:
    st.warning("Aucune donnée disponible.")

# 📅 Filtre par date
if "created_at" in df.columns:
    with st.expander("📅 Filtrer par date"):
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        date_min = df["created_at"].min().date()
        date_max = df["created_at"].max().date()
        start_date, end_date = st.date_input("Plage de dates", [date_min, date_max])
        df = df[(df["created_at"].dt.date >= start_date) & (df["created_at"].dt.date <= end_date)]

# ➕ Formulaire d'ajout
st.markdown(f"<h3 style='color:{VERT_MOYEN}'>🧺 Ajouter un Pesée</h3>", unsafe_allow_html=True)
with st.form("ajout_rendement"):
    col1, col2, col3 = st.columns(3)
    with col1:
        operatrice_id = st.text_input("ID opératrice (ex: op-1, op-2)")
    with col2:
        poids_kg = st.number_input("Poids (kg)", min_value=0.0, step=0.1, format="%.1f")
    with col3:
        heures = st.number_input("Heures", min_value=0)
        minutes = st.number_input("Minutes", min_value=0, max_value=59)

    if st.form_submit_button("✅ Enregistrer"):
        # Validation des champs
        if not operatrice_id.startswith('op-'):
            st.error("L'ID opératrice doit commencer par 'op-'")
        elif poids_kg <= 0:
            st.error("Le poids doit être supérieur à 0")
        elif heures == 0 and minutes == 0:
            st.error("La durée ne peut pas être 0")
        else:
            temps_total = heures * 60 + minutes
            nouveau = {
                "operatrice_id": operatrice_id, 
                "poids__._": poids_kg, 
                "temps__._": temps_total
            }
            r = requests.post(
                f"{SUPABASE_URL}/rest/v1/{TABLE}",
                headers={**headers, "Content-Type": "application/json"},
                json=nouveau
            )
            if r.status_code == 201:
                st.success("✅ Rendement enregistré avec succès")
                st.cache_data.clear()
            else:
                st.error(f"❌ Erreur lors de l'enregistrement (code {r.status_code})")
                st.text(r.text)  # Affiche le détail de l'erreur

# 📄 Tableau des données
st.markdown(f"<h3 style='color:{VERT_MOYEN}'>📄 Données enregistrées</h3>", unsafe_allow_html=True)
if not df.empty:
    st.dataframe(df)

    # 📤 Export Excel
    def exporter_excel(df_export):
        df_export = df_export.copy()
        if "created_at" in df_export.columns:
            df_export["created_at"] = df_export["created_at"].astype(str)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Rendements")
        return buffer.getvalue()

    st.download_button("⬇️ Télécharger en Excel", data=exporter_excel(df),
                       file_name="rendements.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 🏆 Top opératrices
    st.markdown(f"<h3 style='color:{VERT_MOYEN}'>🏆 Top 10 des opératrices</h3>", unsafe_allow_html=True)
    top = df.groupby("operatrice_id")["poids_kg"].sum().sort_values(ascending=False).head(10).reset_index()
    fig1 = px.bar(top, x="operatrice_id", y="poids_kg", color="operatrice_id",
                  color_discrete_sequence=px.colors.qualitative.Vivid,
                  title="Poids total par opératrice")
    st.plotly_chart(fig1, use_container_width=True)

    best = top.iloc[0]
    st.success(f"🌟 Meilleure opératrice : **{best['operatrice_id']}** avec **{best['poids_kg']} kg**")

    # 📈 Évolution du rendement
    st.markdown(f"<h3 style='color:{VERT_MOYEN}'>📈 Évolution du rendement dans le temps</h3>", unsafe_allow_html=True)
    if "created_at" in df.columns:
        evolution = df.groupby(df["created_at"].dt.date)["poids_kg"].sum().reset_index()
        evolution.columns = ["Date", "Poids total (kg)"]
        fig2 = px.line(evolution, x="Date", y="Poids total (kg)", markers=True,
                       title="Rendement journalier",
                       line_shape="spline",
                       color_discrete_sequence=[VERT_FONCE])
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("ℹ️ Colonne 'created_at' manquante : impossible d'afficher l'évolution.")
# 🚪 Quitter
if st.button("🚪 Quitter"):
    st.session_state.connecte = False
    st.success("🔒 Vous avez été déconnecté.")
    st.stop()

