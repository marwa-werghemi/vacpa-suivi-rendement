import streamlit as st
import pandas as pd
import requests
from io import BytesIO
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
            
            # Correction des noms de colonnes (d'après votre capture)
            colonnes_corrigees = {
                'polds__. fio...': 'poids_kg',
                'temps__. i...': 'temps_min',
                'da... ti...': 'date_heure',
                'cr... ti...': 'created_at'
            }
            df = df.rename(columns=colonnes_corrigees)
            
            # Conversion des types
            df['poids_kg'] = pd.to_numeric(df['poids_kg'], errors='coerce')
            df['temps_min'] = pd.to_numeric(df['temps_min'], errors='coerce')
            
            # Calcul du rendement
            df['rendement'] = df['poids_kg'] / (df['temps_min'] / 60).replace(0, 1)
            
            return df
    except Exception as e:
        st.error(f"Erreur de chargement: {str(e)}")
    return pd.DataFrame()

# Interface principale
st.title("🌴 Suivi de Rendement VACPA")

# Chargement des données
if st.button("🔄 Actualiser"):
    st.cache_data.clear()
df = charger_donnees()

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

# Affichage des données
if not df.empty:
    st.subheader("📊 Données enregistrées")
    
    # Colonnes à afficher (avec vérification)
    colonnes_affichees = [
        'ligne', 'numero_pesee', 'operatrice_id', 
        'poids_kg', 'temps_min', 'rendement', 
        'date_heure', 'created_at'
    ]
    colonnes_disponibles = [col for col in colonnes_affichees if col in df.columns]
    
    st.dataframe(
        df[colonnes_disponibles]
        .sort_values('date_heure', ascending=False)
        .style.format({
            'poids_kg': '{:.1f}',
            'rendement': '{:.1f}'
        }),
        height=500
    )
    
    # Visualisations
    st.subheader("📈 Analyses")
    
    tab1, tab2 = st.tabs(["Par ligne", "Top opératrices"])
    
    with tab1:
        if 'ligne' in df.columns:
            fig = px.bar(
                df.groupby('ligne')['poids_kg'].sum().reset_index(),
                x='ligne',
                y='poids_kg',
                title='Production par ligne'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        top = df.groupby('operatrice_id').agg(
            poids_total=('poids_kg', 'sum'),
            rendement_moyen=('rendement', 'mean')
        ).nlargest(10, 'poids_total')
        
        fig = px.bar(
            top,
            x=top.index,
            y='poids_total',
            title='Top 10 opératrices'
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Aucune donnée disponible")

if st.button("🚪 Déconnexion"):
    st.session_state.connecte = False
    st.rerun()
