import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from datetime import datetime

# 🌿 Configuration de la page
st.set_page_config(page_title="Suivi de rendement VACPA", layout="wide", page_icon="🌴🌴🌴")

# 🌿 Palette de couleurs
VERT_FONCE = "#1b4332"
VERT_CLAIR = "#d8f3dc"
VERT_MOYEN = "#52b788"
COLORS = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24

# 🔐 Authentification
MOT_DE_PASSE = "vacpa2025"
if "connecte" not in st.session_state:
    st.session_state.connecte = False
if not st.session_state.connecte:
    st.markdown(f"<h2 style='color:{VERT_FONCE}'>🔐 Accès sécurisé</h2>", unsafe_allow_html=True)
    mdp = st.text_input("Entrez le mot de passe", type="password")
    if mdp == MOT_DE_PASSE:
        st.session_state.connecte = True
        st.rerun()
    elif mdp:
        st.error("❌ Mot de passe incorrect")
    st.stop()

# 🔗 Configuration Supabase
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
            
            # Gestion des dates
            df['date_heure'] = pd.to_datetime(df['date_heure'], errors='coerce')
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
            
            # Colonnes par défaut
            if 'ligne' not in df.columns:
                df['ligne'] = 1
            if 'numero_pesee' not in df.columns:
                df['numero_pesee'] = 1
                
            return df
    except Exception as e:
        st.error(f"Erreur de chargement: {str(e)}")
    return pd.DataFrame()

# Interface principale
st.title("🌴 Suivi de Rendement VACPA")

# Chargement des données
if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()
df = charger_donnees()

# Statistiques globales
if not df.empty:
    cols = st.columns(4)
    cols[0].metric("Total KG", f"{df['poids_kg'].sum():.2f} kg")
    cols[1].metric("Durée Totale", f"{df['temps_min'].sum():.0f} min") 
    cols[2].metric("Rendement Moyen", f"{df['rendement'].mean():.2f} kg/h")
    cols[3].metric("Max Rendement", f"{df['rendement'].max():.2f} kg/h")
else:
    st.warning("Aucune donnée disponible")

# Filtres
with st.expander("🔍 Filtres", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        if "created_at" in df.columns:
            date_range = st.date_input(
                "Plage de dates",
                value=[df['created_at'].min().date(), df['created_at'].max().date()],
                min_value=df['created_at'].min().date(),
                max_value=df['created_at'].max().date()
            )
    with col2:
        if 'ligne' in df.columns:
            lignes = st.multiselect(
                "Lignes de production",
                options=sorted(df['ligne'].unique()),
                default=sorted(df['ligne'].unique())
            )

# Formulaire d'ajout
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
            response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE}", headers=headers, json=data)
            if response.status_code == 201:
                st.success("Données enregistrées!")
                st.cache_data.clear()
            else:
                st.error(f"Erreur {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Erreur: {str(e)}")

# Visualisations
if not df.empty:
    tab1, tab2, tab3 = st.tabs(["📋 Tableau", "📊 Histogrammes", "📈 Tendances"])
    
    with tab1:
        st.dataframe(
            df.sort_values('date_heure', ascending=False),
            height=600,
            column_config={
                "poids_kg": st.column_config.NumberColumn(format="%.1f kg"),
                "rendement": st.column_config.NumberColumn(format="%.1f kg/h")
            }
        )
    
    with tab2:
        st.subheader("Distributions colorées")
        
        # Histogramme du poids par ligne
        fig1 = px.histogram(
            df,
            x="poids_kg",
            color="ligne",
            nbins=20,
            title="Répartition du poids par ligne",
            labels={"poids_kg": "Poids (kg)", "ligne": "Ligne"},
            color_discrete_sequence=COLORS,
            barmode="group"
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Histogramme du rendement
        fig2 = px.histogram(
            df,
            x="rendement",
            color="rendement",
            nbins=20,
            title="Distribution des rendements",
            color_continuous_scale=px.colors.sequential.Plasma,
            labels={"rendement": "Rendement (kg/h)"}
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Histogramme combiné
        fig3 = px.histogram(
            df,
            x="operatrice_id",
            y="poids_kg",
            color="ligne",
            histfunc="sum",
            title="Production par opératrice et ligne",
            labels={"operatrice_id": "Opératrice", "poids_kg": "Poids total (kg)"},
            color_discrete_sequence=COLORS
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with tab3:
        st.subheader("Évolutions temporelles")
        df['date'] = pd.to_datetime(df['date_heure']).dt.date
        
        # Sélection des opératrices
        top_ops = df['operatrice_id'].value_counts().nlargest(5).index.tolist()
        selected_ops = st.multiselect(
            "Opératrices à afficher",
            options=df['operatrice_id'].unique(),
            default=top_ops
        )
        
        if selected_ops:
            df_filtered = df[df['operatrice_id'].isin(selected_ops)]
            
            # Courbe de production
            fig4 = px.line(
                df_filtered.groupby(['date', 'operatrice_id'])['poids_kg'].sum().reset_index(),
                x="date",
                y="poids_kg",
                color="operatrice_id",
                title="Production quotidienne",
                labels={"poids_kg": "Poids (kg)", "date": "Date"},
                color_discrete_sequence=COLORS
            )
            st.plotly_chart(fig4, use_container_width=True)
            
            # Courbe de rendement
            fig5 = px.line(
                df_filtered.groupby(['date', 'operatrice_id'])['rendement'].mean().reset_index(),
                x="date",
                y="rendement",
                color="operatrice_id",
                title="Rendement moyen",
                labels={"rendement": "Rendement (kg/h)", "date": "Date"},
                color_discrete_sequence=COLORS
            )
            st.plotly_chart(fig5, use_container_width=True)

# Déconnexion
if st.button("🚪 Déconnexion"):
    st.session_state.connecte = False
    st.rerun()
