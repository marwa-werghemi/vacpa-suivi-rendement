import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from datetime import datetime

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

# 🔗 Supabase - Configuration corrigée
SUPABASE_URL = "https://pavndhlnvfwoygmatqys.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdm5kaGxudmZ3b3lnbWF0cXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYzMDYyNzIsImV4cCI6MjA2MTg4MjI3Mn0.xUMJfDZdjZkTzYdz0MgZ040IdT_cmeJSWIDZ74NGt1k"
TABLE = "rendements"

# Headers corrigés avec les paramètres de sécurité
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

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
    # Conversion des types de données
    df["temps_min"] = pd.to_numeric(df["temps_min"], errors="coerce").fillna(0)
    df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="coerce").fillna(0)
    df["rendement"] = df["poids_kg"] / (df["temps_min"] / 60).replace(0, 1)  # Évite la division par zéro

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
        date_min = df["created_at"].min().date() if not df.empty else datetime.now().date()
        date_max = df["created_at"].max().date() if not df.empty else datetime.now().date()
        start_date, end_date = st.date_input("Plage de dates", [date_min, date_max])
        df = df[(df["created_at"].dt.date >= start_date) & (df["created_at"].dt.date <= end_date)]

# ➕ Formulaire d'ajout corrigé
st.markdown(f"<h3 style='color:{VERT_MOYEN}'>🧺 Ajouter un Pesée</h3>", unsafe_allow_html=True)
with st.form("ajout_rendement", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        operatrice_id = st.text_input("ID opératrice", placeholder="op-1", key="operatrice_id")
    with col2:
        poids_kg = st.number_input("Poids (kg)", min_value=0.1, step=0.1, value=1.0, key="poids_kg")
    with col3:
        heures = st.number_input("Heures", min_value=0, value=0, key="heures")
        minutes = st.number_input("Minutes", min_value=0, max_value=59, value=30, key="minutes")

    if st.form_submit_button("✅ Enregistrer"):
        if not operatrice_id or not operatrice_id.startswith('op-'):
            st.error("L'ID opératrice doit commencer par 'op-'")
        elif poids_kg <= 0:
            st.error("Le poids doit être supérieur à 0")
        elif heures == 0 and minutes == 0:
            st.error("La durée ne peut pas être 0")
        else:
            temps_total = heures * 60 + minutes
            nouveau = {
                "operatrice_id": operatrice_id.strip(),
                "poids_kg": float(poids_kg),
                "temps_min": int(temps_total),
                "date_heure": datetime.now().isoformat() + "Z"
            }
            
            try:
                r = requests.post(
                    f"{SUPABASE_URL}/rest/v1/{TABLE}",
                    headers=headers,
                    json=nouveau
                )
                
                if r.status_code == 201:
                    st.success("✅ Enregistré avec succès!")
                    st.balloons()
                    st.cache_data.clear()
                else:
                    st.error(f"Erreur {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Erreur de connexion: {str(e)}")

# 📄 Tableau des données avec export Excel corrigé
st.markdown(f"<h3 style='color:{VERT_MOYEN}'>📄 Données enregistrées</h3>", unsafe_allow_html=True)
if not df.empty:
    # Colonnes à afficher
    cols_to_show = ["operatrice_id", "date_heure", "poids_kg", "temps_min", "rendement", "created_at"]
    cols_to_show = [col for col in cols_to_show if col in df.columns]
    
    # Affichage du dataframe
    st.dataframe(df[cols_to_show])

    # 📤 Export Excel corrigé
    def exporter_excel(df_export):
        # Crée une copie pour éviter les modifications accidentelles
        df_export = df_export.copy()
        
        # Convertit les colonnes datetime en strings
        for col in df_export.select_dtypes(include=['datetime']):
            df_export[col] = df_export[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Convertit les autres types problématiques
        df_export = df_export.applymap(lambda x: str(x) if pd.isna(x) else x)
        
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Rendements')
        return buffer.getvalue()

    st.download_button(
        "⬇️ Télécharger en Excel",
        data=exporter_excel(df[cols_to_show]),
        file_name="rendements.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 🏆 Top opératrices
    st.markdown(f"<h3 style='color:{VERT_MOYEN}'>🏆 Top 10 des opératrices</h3>", unsafe_allow_html=True)
    top = df.groupby("operatrice_id").agg(
        poids_total=("poids_kg", "sum"),
        rendement_moyen=("rendement", "mean")
    ).sort_values("poids_total", ascending=False).head(10).reset_index()
    
    fig1 = px.bar(top, x="operatrice_id", y="poids_total", 
                 color="rendement_moyen",
                 title="Poids total par opératrice (couleur = rendement moyen)",
                 labels={"poids_total": "Poids total (kg)", "rendement_moyen": "Rendement moyen (kg/h)"})
    st.plotly_chart(fig1, use_container_width=True)

    # 📈 Évolution du rendement
    st.markdown(f"<h3 style='color:{VERT_MOYEN}'>📈 Évolution du rendement</h3>", unsafe_allow_html=True)
    if "created_at" in df.columns:
        df_jour = df.groupby(df["created_at"].dt.date).agg(
            poids_total=("poids_kg", "sum"),
            rendement_moyen=("rendement", "mean")
        ).reset_index()
        
        fig2 = px.line(df_jour, x="created_at", y=["poids_total", "rendement_moyen"],
                      title="Évolution journalière",
                      labels={"value": "Valeur", "variable": "Métrique"},
                      markers=True)
        st.plotly_chart(fig2, use_container_width=True)

# 🚪 Quitter
if st.button("🚪 Quitter"):
    st.session_state.connecte = False
    st.rerun()
