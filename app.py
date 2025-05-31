import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import plotly.graph_objects as go
import random
from time import time
import threading

# Configuration de la page DOIT être la première commande Streamlit
st.set_page_config(
    page_title="Dashboard VACPA",
    layout="wide",
    page_icon="🌿",
    initial_sidebar_state="expanded"
)

# Définir COLORS avant toute utilisation
COLORS = {
    "primary": "#2E86AB",
    "secondary": "#A23B72",
    "success": "#3BB273",
    "warning": "#F18F01",
    "danger": "#E71D36",
    "dark": "#2B2D42",
    "light": "#F7F7F7"
}

# Configuration des images d'arrière-plan
BACKGROUND_IMAGES = [
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTHueKsv77XOgyIBCLduL85hnWI-8r1S178IbRPb_L2HcV4pCby0iYFdoxuPAg_-mtvvLc&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS23gzzTNbiGkFWcPFxluKCOBIkQ0Xwon4Y7Q&s",
    "https://www.boudjebeldates.com/wp-content/uploads/2022/09/Dattes-boudjebel-1.jpg",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvoBI3DM3c7U8k05bJiloMMlz9T43QwXy8Oc9D_qP6kFKH-ZCKAGY2DqFzxJOw2SUC73s&usqp=CAU",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRL-vpFuP2Mw4xe1B4C8YJXmNzwiUbxyPSQe9nIsZZ_z4I_-6BOj6swM2NR1eKbvjI1HgI&usqp=CAU",
    "https://res.cloudinary.com/one-degree-organic-foods/image/fetch/c_fit,h_720,w_1280,d_farmer_default.png/https://onedegreeorganics.com/wp-content/uploads/2023/01/DSC01006-scaled.jpg",
    "https://res.cloudinary.com/one-degree-organic-foods/image/fetch/c_fit,h_720,w_1280,d_farmer_default.png/https://onedegreeorganics.com/wp-content/uploads/2023/01/DSC00973-scaled.jpg"
]

def get_randomized_url(url):
    """Ajoute un timestamp pour éviter le cache du navigateur"""
    return f"{url}?random={int(time())}"

# CSS avec arrière-plan dynamique
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.88), rgba(255,255,255,0.88)), 
                    url("{get_randomized_url(random.choice(BACKGROUND_IMAGES))}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        transition: background-image 1.2s ease-in-out;
    }}
    
    .header {{
        background-color: {COLORS['primary']};
        color: white;
        padding: 1.5rem;
        border-radius: 0 0 15px 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    
    .metric-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: transform 0.2s;
        border-left: 4px solid {COLORS['primary']};
    }}
    
    [data-testid="stSidebar"] {{
        background-color: {COLORS['light']};
    }}
</style>
""", unsafe_allow_html=True)

# --------------------------
# 🔐 AUTHENTIFICATION & CONFIG
# --------------------------
CREDENTIALS = {
    "admin": {"password": "vacpa2025", "role": "admin"},
    "manager": {"password": "manager123456789", "role": "manager"},
    "operateur": {"password": "operateur456789", "role": "operateur"},
    "marwa": {"password": "vacpa2025", "role": "operateur"}
}

SEUILS = {
    "rendement": {"haut": 4.5, "moyen": 4.0},
    "non_productivite": 20,
    "sous_performance": 25,
    "variabilite": 5,
    "pannes": 3,
    "erreurs": 10
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.alertes = []

# --------------------------
# 🔗 SUPABASE CONFIG
# --------------------------
SUPABASE_URL = "https://pavndhlnvfwoygmatqys.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdm5kaGxudmZ3b3lnbWF0cXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYzMDYyNzIsImV4cCI6MjA2MTg4MjI3Mn0.xUMJfDZdjZkTzYdz0MgZ040IdT_cmeJSWIDZ74NGt1k"
TABLE_RENDEMENT = "rendements"
TABLE_PANNES = "pannes"
TABLE_ERREURS = "erreurs"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --------------------------
# 🧩 FONCTIONS UTILITAIRES
# --------------------------
@st.cache_data(ttl=60)
def charger_donnees():
    dfs = {}
    
    try:
        # Chargement des données depuis Supabase
        for table in [TABLE_RENDEMENT, TABLE_PANNES, TABLE_ERREURS]:
            response = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?select=*", headers=headers)
            
            if response.status_code == 200:
                df = pd.DataFrame(response.json())
                
                # Conversions de type
                date_columns = [col for col in df.columns if 'date' in col.lower()]
                for col in date_columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                
                if 'created_at' in df.columns:
                    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
                
                # Calculs spécifiques pour la table rendement
                if table == TABLE_RENDEMENT:
                    # Gestion des colonnes manquantes avec valeurs par défaut
                    if 'poids_kg' not in df.columns:
                        df['poids_kg'] = 0
                    if 'heure_travail' not in df.columns:
                        df['heure_travail'] = 5.0
                    
                    # Conversion numérique
                    df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="coerce").fillna(0)
                    df["heure_travail"] = pd.to_numeric(df["heure_travail"], errors="coerce").fillna(5.0)
                    
                    # Calcul du rendement
                    df["rendement"] = df["poids_kg"] / df["heure_travail"]
                    
                    # Classification du rendement
                    bins = [0, 3.5, 4.0, 4.5, float('inf')]
                    labels = ["Critique", "Faible", "Acceptable", "Excellent"]
                    df["niveau_rendement"] = pd.cut(df["rendement"],
                                                  bins=bins,
                                                  labels=labels)
                
                dfs[table] = df
            else:
                st.error(f"Erreur {response.status_code} lors du chargement de {table}")
                dfs[table] = pd.DataFrame()  # Retourner un DataFrame vide en cas d'erreur
                
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        return {TABLE_RENDEMENT: pd.DataFrame(), 
                TABLE_PANNES: pd.DataFrame(), 
                TABLE_ERREURS: pd.DataFrame()}
    
    return dfs

def metric_card(title, value, delta=None, icon="📊", color=COLORS["primary"]):
    """Composant de carte métrique moderne avec couleur personnalisée"""
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {color}">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <div style="font-size: 24px;">{icon}</div>
            <h3 style="margin: 0; color: {COLORS['dark']}">{title}</h3>
        </div>
        <div style="font-size: 28px; font-weight: 600; color: {color}">{value}</div>
        {f'<div style="color: {COLORS["success"] if ("+" in str(delta)) else COLORS["danger"]}; font-size: 14px;">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)

# --------------------------
# 🔐 PAGE DE CONNEXION
# --------------------------
if not st.session_state.authenticated:
    col1, col2 = st.columns([1, 2])
    with col2:
        st.markdown("<div style='height: 100px'></div>", unsafe_allow_html=True)
        with st.container():
            st.markdown("### Connexion à l'espace personnel")
            username = st.text_input("Nom d'utilisateur", key="login_user")
            password = st.text_input("Mot de passe", type="password", key="login_pass")
            
            if st.button("Se connecter", type="primary"):
                if username in CREDENTIALS and CREDENTIALS[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = CREDENTIALS[username]["role"]
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
    st.stop()

# --------------------------
# 📊 CHARGEMENT DES DONNÉES
# --------------------------
if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()

try:
    data = charger_donnees()
    df_rendement = data.get(TABLE_RENDEMENT, pd.DataFrame())
    df_pannes = data.get(TABLE_PANNES, pd.DataFrame())
    df_erreurs = data.get(TABLE_ERREURS, pd.DataFrame())
except Exception as e:
    st.error(f"Erreur critique lors du chargement des données: {str(e)}")
    st.stop()

# --------------------------
# 🎨 EN-TÊTE PRINCIPAL
# --------------------------
st.markdown(f"""
<div class="header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin: 0;">Suivi de Rendement VACPA</h1>
            <p style="margin: 0; opacity: 0.8;">Connecté en tant que {st.session_state.username} ({st.session_state.role})</p>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 24px;">{datetime.now().strftime("%d %B %Y")}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --------------------------
# 🎨 SIDEBAR
# --------------------------
with st.sidebar:
    st.markdown(f"### {st.session_state.username}")
    st.markdown(f"*{st.session_state.role.capitalize()}*")
    st.divider()
    
    st.markdown("#### Navigation")
    if st.button("🏠 Tableau de bord"):
        pass
    
    if st.session_state.role in ["admin", "manager"]:
        if st.button("📊 Statistiques"):
            pass
        if st.button("👥 Gestion opérateurs"):
            pass
    
    st.divider()
    
    if st.button("🔄 Actualiser les données", key="refresh_sidebar"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🚪 Déconnexion", type="primary"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

# --------------------------
# 👷 INTERFACE OPÉRATEUR
# --------------------------
if st.session_state.role == "operateur":
    st.subheader(f"👋 Bienvenue {st.session_state.username}")
    
    # Onglets pour les opérateurs
    tab1, tab2, tab3 = st.tabs(["📝 Nouvelle pesée", "⚠️ Signaler problème", "📜 Historique"])
    
    with tab1:
        # Formulaire simplifié pour les opérateurs
        with st.form("operateur_pesee_form", clear_on_submit=True):
            cols = st.columns(3)
            with cols[0]:
                ligne = st.selectbox("Ligne", [1, 2], key="op_ligne")
                operatrice_id = st.text_input("ID Opératrice", value=st.session_state.username, key="op_id")
            with cols[1]:
                poids_kg = st.number_input("Poids (kg)", min_value=0.1, value=1.0, step=0.1, key="op_poids")
                numero_pesee = st.number_input("N° Pesée", min_value=1, value=1, key="op_numero")
            with cols[2]:
                heure_travail = st.number_input("Temps travaillé (h)", min_value=0.1, value=1.0, step=0.1, key="op_temps")
                date_pesee = st.date_input("Date", datetime.now().date(), key="op_date")
                heure_pesee = st.time_input("Heure", datetime.now().time(), key="op_heure")
            
            submitted = st.form_submit_button("💾 Enregistrer", type="primary")
            
            if submitted:
                if not operatrice_id:
                    st.error("L'ID opératrice est obligatoire")
                else:
                    # Formatage des données pour correspondre exactement à votre schéma de base de données
                    data = {
                        "operatrice_id": operatrice_id,
                        "poids_kg": float(poids_kg),
                        "ligne": int(ligne),
                        "numero_pesee": int(numero_pesee),
                        "heure_travail": float(heure_travail),
                        "date": date_pesee.isoformat(),
                        "created_at": datetime.now().isoformat() + "Z"
                    }
                    
                    try:
                        response = requests.post(
                            f"{SUPABASE_URL}/rest/v1/{TABLE_RENDEMENT}",
                            headers=headers,
                            json=data
                        )
                        
                        if response.status_code in (200, 201):
                            st.success("Pesée enregistrée avec succès!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Erreur {response.status_code}: {response.text}")
                    except Exception as e:
                        st.error(f"Erreur lors de l'enregistrement: {str(e)}")

# --------------------------
# 👨‍💼 INTERFACE ADMIN/MANAGER
# --------------------------
if st.session_state.role in ["admin", "manager"]:
    st.markdown("### ➕ Ajouter une nouvelle pesée")
    with st.form("ajout_pesee_form", clear_on_submit=True):
        cols = st.columns([1, 1, 1, 1])
        
        with cols[0]:
            ligne = st.selectbox("Ligne de production", [1, 2], key="admin_ligne")
            operatrice_id = st.text_input("ID Opératrice", key="admin_operatrice")
        
        with cols[1]:
            poids_kg = st.number_input("Poids (kg)", min_value=0.1, value=1.0, step=0.1, key="admin_poids")
            temps_travail = st.number_input("Temps travaillé (heures)", min_value=0.1, value=1.0, step=0.1, key="admin_temps")
        
        with cols[2]:
            date_pesee = st.date_input("Date", datetime.now().date(), key="admin_date")
        
        with cols[3]:
            numero_pesee = st.number_input("N° Pesée", min_value=1, value=1, key="admin_numero")
            commentaire = st.text_input("Commentaire (optionnel)", key="admin_comment")
        
        submitted = st.form_submit_button("💾 Enregistrer", type="primary")
        
        if submitted:
            # Validation des champs obligatoires
            if not operatrice_id:
                st.error("L'ID opératrice est obligatoire")
            elif poids_kg <= 0:
                st.error("Le poids doit être supérieur à 0")
            elif temps_travail <= 0:
                st.error("Le temps travaillé doit être supérieur à 0")
            else:
                # Préparation des données selon votre schéma exact
                data = {
                    "operatrice_id": operatrice_id,
                    "poids_kg": float(poids_kg),
                    "ligne": int(ligne),
                    "numero_pesee": int(numero_pesee),
                    "heure_travail": float(temps_travail),
                    "date": date_pesee.isoformat(),
                    "commentaire_pesee": commentaire if commentaire else None,
                    "created_at": datetime.now().isoformat() + "Z"
                }
                
                try:
                    response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/{TABLE_RENDEMENT}",
                        headers=headers,
                        json=data
                    )
                    
                    if response.status_code in (200, 201):
                        st.success("Pesée enregistrée avec succès!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Erreur {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement: {str(e)}")
