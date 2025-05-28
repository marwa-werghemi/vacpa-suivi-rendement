import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Suivi de rendement VACPA", layout="wide", page_icon="🌴")

# Authentification
MOT_DE_PASSE = "vacpa2025"
if not st.session_state.get("connecte", False):
    st.markdown("<h2 style='color:#1b4332'>🔐 Accès sécurisé</h2>", unsafe_allow_html=True)
    mdp = st.text_input("Entrez le mot de passe", type="password")
    if mdp == MOT_DE_PASSE:
        st.session_state.connecte = True
        st.rerun()
    elif mdp:
        st.error("Mot de passe incorrect")
    st.stop()

# Configuration Supabase
SUPABASE_URL = "https://pavndhlnvfwoygmatqys.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdm5kaGxudmZ3b3lnbWF0cXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYzMDYyNzIsImV4cCI6MjA2MTg4MjI3Mn0.xUMJfDZdjZkTzYdz0MgZ040IdT_cmeJSWIDZ74NGt1k"
TABLE = "rendements"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

@st.cache_data(ttl=300)
def charger_donnees():
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*", headers=headers)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            
            # Nettoyage des données
            df["temps_min"] = pd.to_numeric(df["temps_min"], errors="coerce").fillna(0)
            df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="coerce").fillna(0)
            df["rendement"] = df["poids_kg"] / (df["temps_min"] / 60).replace(0, 1)
            
            # Conversion des dates
            df['date_heure'] = pd.to_datetime(df['date_heure'], errors='coerce')
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
            
            return df.dropna(subset=['date_heure'])
    except Exception as e:
        st.error(f"Erreur de chargement: {str(e)}")
    return pd.DataFrame()

# Interface
st.title("🌴 Suivi de Rendement VACPA")

# Chargement des données
if st.button("🔄 Actualiser"):
    st.cache_data.clear()
df = charger_donnees()

# Filtres
if not df.empty:
    with st.expander("🔍 Filtres", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            date_debut = st.date_input("Date début", df['date_heure'].min().date())
            date_fin = st.date_input("Date fin", df['date_heure'].max().date())
        with col2:
            operatrices = st.multiselect(
                "Opératrices",
                options=sorted(df['operatrice_id'].unique()),
                default=sorted(df['operatrice_id'].unique())[:3]
            )
            lignes = st.multiselect(
                "Lignes",
                options=sorted(df['ligne'].unique()) if 'ligne' in df.columns else [],
                default=sorted(df['ligne'].unique()) if 'ligne' in df.columns else []
            )
    
    # Application des filtres
    mask = (
        (df['date_heure'].dt.date >= date_debut) &
        (df['date_heure'].dt.date <= date_fin) &
        (df['operatrice_id'].isin(operatrices))
    
    if 'ligne' in df.columns:
        mask &= df['ligne'].isin(lignes)
    
    df_filtre = df[mask]

# Visualisations
if not df.empty and not df_filtre.empty:
    tab1, tab2 = st.tabs(["📈 Courbes de production", "📊 Statistiques"])
    
    with tab1:
        st.subheader("Évolution quotidienne")
        
        # Préparation des données
        df_jour = df_filtre.groupby([
            pd.Grouper(key='date_heure', freq='D'),
            'operatrice_id'
        ]).agg({'poids_kg':'sum', 'rendement':'mean'}).reset_index()
        
        # Graphique poids
        fig1 = px.line(
            df_jour,
            x="date_heure",
            y="poids_kg",
            color="operatrice_id",
            title="Poids total par jour",
            labels={"poids_kg": "Poids (kg)", "date_heure": "Date"},
            markers=True
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Graphique rendement
        fig2 = px.line(
            df_jour,
            x="date_heure",
            y="rendement",
            color="operatrice_id",
            title="Rendement moyen par jour",
            labels={"rendement": "Rendement (kg/h)", "date_heure": "Date"},
            markers=True
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("Répartition des données")
        
        col1, col2 = st.columns(2)
        with col1:
            # Histogramme poids
            fig3 = px.histogram(
                df_filtre,
                x="poids_kg",
                nbins=20,
                title="Distribution des poids",
                color="operatrice_id"
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            # Histogramme rendement
            fig4 = px.histogram(
                df_filtre,
                x="rendement",
                nbins=20,
                title="Distribution des rendements",
                color="operatrice_id"
            )
            st.plotly_chart(fig4, use_container_width=True)

elif not df.empty:
    st.warning("Aucune donnée ne correspond aux filtres sélectionnés")
else:
    st.info("Aucune donnée disponible")

# Déconnexion
if st.button("🚪 Déconnexion"):
    st.session_state.connecte = False
    st.rerun()
