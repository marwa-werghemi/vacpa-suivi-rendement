import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from datetime import datetime

# 🌿 Design & configuration de page
st.set_page_config(page_title="Suivi de rendement VACPA", layout="wide", page_icon="🌴🌴🌴")

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

# 🔗 Supabase - Configuration
SUPABASE_URL = "https://pavndhlnvfwoygmatqys.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdm5kaGxudmZ3b3lnbWF0cXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYzMDYyNzIsImV4cCI6MjA2MTg4MjI3Mn0.xUMJfDZdjZkTzYdz0MgZ040IdT_cmeJSWIDZ74NGt1k"
TABLE = "rendements"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

@st.cache_data(ttl=60)
def charger_donnees():
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*", headers=headers)
    if r.status_code == 200:
        df = pd.DataFrame(r.json())
        # Assure la présence des colonnes requises
        if 'ligne' not in df.columns:
            df['ligne'] = 1
        if 'numero_pesee' not in df.columns:
            df['numero_pesee'] = 1
        
        # Conversion robuste des colonnes numériques
        df["temps_min"] = pd.to_numeric(df["temps_min"], errors="coerce").fillna(0)
        df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="coerce").fillna(0)
        df["rendement"] = df["poids_kg"] / (df["temps_min"] / 60).replace(0, 1)
        
        # Conversion robuste des dates
        df['date_heure'] = pd.to_datetime(df['date_heure'], errors='coerce')
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        return df
    return pd.DataFrame()

if st.button("🔄 Recharger les données"):
    st.cache_data.clear()

df = charger_donnees()

# 🏷️ Titre
st.markdown(f"<h1 style='color:{VERT_FONCE}'>🌴 Suivi du Rendement - VACPA</h1>", unsafe_allow_html=True)

# 🌟 Statistiques globales
st.subheader("📊 Statistiques globales")
if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total KG", f"{df['poids_kg'].sum():.2f} kg")
    
    # Modification ici pour afficher la durée en heures et minutes
    total_minutes = df['temps_min'].sum()
    heures = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    col2.metric("Durée Totale", f"{heures}h {minutes}min")
    
    col3.metric("Rendement Moyen", f"{df['rendement'].mean():.2f} kg/h")
    col4.metric("Max Rendement", f"{df['rendement'].max():.2f} kg/h")
else:
    st.warning("Aucune donnée disponible.")

# 📅 Filtres
with st.expander("🔍 Filtres"):
    # Filtre par date
    if "created_at" in df.columns:
        date_min = df["created_at"].min().date() if not df.empty else datetime.today().date()
        date_max = df["created_at"].max().date() if not df.empty else datetime.today().date()
        start_date, end_date = st.date_input("Plage de dates", [date_min, date_max])
        df = df[(df["created_at"].dt.date >= start_date) & (df["created_at"].dt.date <= end_date)]
    
    # Filtre par ligne
    if 'ligne' in df.columns:
        lignes = sorted(df['ligne'].unique())
        selected_lignes = st.multiselect("Lignes de production", options=lignes, default=lignes)
        df = df[df['ligne'].isin(selected_lignes)] if selected_lignes else df

# ➕ Formulaire d'ajout
with st.form("ajout_form", clear_on_submit=True):
    cols = st.columns([1,1,1,1])
    with cols[0]:
        ligne = st.number_input("Ligne", min_value=1, value=1)
        operatrice = st.text_input("ID Opératrice", "op-")
    with cols[1]:
        poids = st.number_input("Poids (kg)", min_value=0.1, value=1.0, step=0.1)
        numero_pesee = st.number_input("N° Pesée", min_value=1, value=1)
    with cols[2]:
        heures = st.number_input("Heures", min_value=0, value=0)
        minutes = st.number_input("Minutes", min_value=0, max_value=59, value=30)
    
    if st.form_submit_button("💾 Enregistrer"):
        temps_total = heures * 60 + minutes
        data = {
            "operatrice_id": operatrice,
            "poids_kg": poids,
            "temps_min": temps_total,
            "ligne": ligne,
            "numero_pesee": numero_pesee,
            "date_heure": datetime.now().isoformat() + "Z"
        }
        
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/{TABLE}",
                headers=headers,
                json=data
            )
            if response.status_code == 201:
                st.success("Données enregistrées!")
                st.cache_data.clear()
            else:
                st.error(f"Erreur {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Erreur: {str(e)}")

# 📊 Visualisations
if not df.empty:
    st.markdown(f"<h3 style='color:{VERT_MOYEN}'>📊 Analyses Visuelles</h3>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Tableau", "📈 Courbes", "📊 Histogrammes", "🏆 Top Performances"])
    
    with tab1:  # Onglet Tableau
        cols_to_show = ["ligne", "numero_pesee", "operatrice_id", "poids_kg", "temps_min", "rendement", "date_heure", "created_at"]
        cols_to_show = [col for col in cols_to_show if col in df.columns]
        st.dataframe(
            df[cols_to_show]
            .sort_values('date_heure', ascending=False)
            .style.format({
                'poids_kg': '{:.1f}',
                'rendement': '{:.1f}'
            }),
            height=500
        )
    
    with tab2:  # Onglet Courbes
        st.subheader("Évolution temporelle")
        df_clean = df.dropna(subset=['date_heure'])
        df_clean['date'] = df_clean['date_heure'].dt.date
        
        if not df_clean.empty:
            df_evolution = df_clean.groupby(['date', 'operatrice_id']).agg({
                'poids_kg': 'sum',
                'rendement': 'mean'
            }).reset_index()
            
            top_operatrices = df_clean['operatrice_id'].value_counts().nlargest(5).index.tolist()
            selected_ops = st.multiselect(
                "Choisir les opératrices à afficher",
                options=df_clean['operatrice_id'].unique(),
                default=top_operatrices,
                key="curve_select"
            )
            
            if selected_ops:
                df_filtered = df_evolution[df_evolution['operatrice_id'].isin(selected_ops)]
                
                fig_poids = px.line(
                    df_filtered,
                    x='date',
                    y='poids_kg',
                    color='operatrice_id',
                    title='Poids total par jour',
                    labels={'poids_kg': 'Poids (kg)', 'date': 'Date'}
                )
                st.plotly_chart(fig_poids, use_container_width=True)
                
                fig_rendement = px.line(
                    df_filtered,
                    x='date',
                    y='rendement',
                    color='operatrice_id',
                    title='Rendement moyen par jour',
                    labels={'rendement': 'Rendement (kg/h)', 'date': 'Date'}
                )
                st.plotly_chart(fig_rendement, use_container_width=True)
            else:
                st.warning("Sélectionnez au moins une opératrice")
        else:
            st.warning("Aucune donnée valide avec des dates disponibles")
    
    with tab3:  # Onglet Histogrammes
        st.subheader("Distribution des données")
        
        col1, col2 = st.columns(2)
        with col1:
            fig_poids = px.histogram(
                df,
                x="poids_kg",
                nbins=20,
                title="Distribution des poids (kg)",
                labels={"poids_kg": "Poids (kg)", "count": "Fréquence"}
            )
            st.plotly_chart(fig_poids, use_container_width=True)
            
            if 'ligne' in df.columns:
                fig_ligne = px.histogram(
                    df,
                    x="ligne",
                    y="poids_kg",
                    histfunc='sum',
                    title="Poids total par ligne",
                    labels={"ligne": "Ligne", "poids_kg": "Poids total (kg)"}
                )
                st.plotly_chart(fig_ligne, use_container_width=True)
        
        with col2:
            fig_temps = px.histogram(
                df,
                x="temps_min",
                nbins=20,
                title="Distribution du temps (minutes)",
                labels={"temps_min": "Temps (minutes)", "count": "Fréquence"}
            )
            st.plotly_chart(fig_temps, use_container_width=True)
            
            fig_rendement = px.histogram(
                df,
                x="rendement",
                nbins=20,
                title="Distribution des rendements (kg/h)",
                labels={"rendement": "Rendement (kg/h)", "count": "Fréquence"}
            )
            st.plotly_chart(fig_rendement, use_container_width=True)
    
    with tab4:  # Onglet Top Performances
        st.subheader("Performance par ligne")
        if 'ligne' in df.columns:
            fig_ligne_bar = px.bar(
                df.groupby('ligne').agg({'poids_kg': 'sum', 'rendement': 'mean'}).reset_index(),
                x='ligne',
                y='poids_kg',
                color='ligne',
                title='Production totale par ligne',
                labels={'ligne': 'Ligne', 'poids_kg': 'Poids total (kg)'}
            )
            st.plotly_chart(fig_ligne_bar, use_container_width=True)
        
        st.subheader("Top 10 opératrices")
        top = df.groupby("operatrice_id").agg(
            poids_total=("poids_kg", "sum"),
            rendement_moyen=("rendement", "mean")
        ).sort_values("poids_total", ascending=False).head(10)
        
        fig_top = px.bar(
            top,
            x=top.index,
            y="poids_total",
            color="rendement_moyen",
            title="Top 10 opératrices par poids total",
            labels={"operatrice_id": "Opératrice", "poids_total": "Poids total (kg)"}
        )
        st.plotly_chart(fig_top, use_container_width=True)

else:
    st.info("Aucune donnée disponible à afficher.")

# ➖ Bouton de déconnexion
if st.button("🚪 Quitter l'application"):
    st.session_state.connecte = False
    st.rerun()
