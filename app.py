import streamlit as st

# Configuration de la page DOIT être la première commande Streamlit
st.set_page_config(
    page_title="Dashboard VACPA",
    layout="wide",
    page_icon="🌿",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import requests
import plotly.graph_objects as go
import random
from time import time
import threading
from time import time, sleep

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

# Thread pour rotation automatique
def rotate_background():
    while True:
        sleep(60)  # Change toutes les 60 secondes
        st.experimental_rerun()

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
    
    /* Votre CSS existant */
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

# Démarrer le thread (une seule fois)
if not hasattr(st.session_state, 'bg_thread'):
    st.session_state.bg_thread = threading.Thread(target=rotate_background, daemon=True)
    st.session_state.bg_thread.start()

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
                
                # Debug: Afficher les colonnes disponibles
                st.session_state[f'debug_{table}_columns'] = df.columns.tolist()
                
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
        # Retourner des DataFrames vides pour toutes les tables en cas d'erreur
        return {TABLE_RENDEMENT: pd.DataFrame(), 
                TABLE_PANNES: pd.DataFrame(), 
                TABLE_ERREURS: pd.DataFrame()}
    
    return dfs

def calculer_kpis(df_rendement, df_pannes, df_erreurs):
    kpis = {
        "rendement_ligne1": 0,
        "rendement_ligne2": 0,
        "non_productivite": 0,
        "sous_performance": 0,
        "variabilite": 0,
        "nb_pannes": 0,
        "mtbf": 0,
        "ratio_erreurs": 0,
        "score_global": 0
    }
    
    try:
        if not df_rendement.empty:
            # Vérification des colonnes nécessaires
            required_columns = ['ligne', 'rendement', 'operatrice_id']
            missing_columns = [col for col in required_columns if col not in df_rendement.columns]
            
            if missing_columns:
                st.warning(f"Colonnes manquantes dans df_rendement: {missing_columns}")
            else:
                # Rendement par ligne
                if 1 in df_rendement["ligne"].unique():
                    kpis["rendement_ligne1"] = df_rendement[df_rendement["ligne"] == 1]["rendement"].mean()
                
                if 2 in df_rendement["ligne"].unique():
                    kpis["rendement_ligne2"] = df_rendement[df_rendement["ligne"] == 2]["rendement"].mean()
                
                # Non-productivité
                total_pesees = len(df_rendement)
                if 'niveau_rendement' in df_rendement.columns:
                    non_productives = len(df_rendement[df_rendement["niveau_rendement"].isin(["Faible", "Critique"])])
                    kpis["non_productivite"] = (non_productives / total_pesees) * 100 if total_pesees > 0 else 0
                
                # Sous-performance
                seuil_sous_perf = SEUILS["rendement"]["moyen"]
                sous_perf = df_rendement[df_rendement["rendement"] < seuil_sous_perf]["operatrice_id"].nunique()
                total_operatrices = df_rendement["operatrice_id"].nunique()
                kpis["sous_performance"] = (sous_perf / total_operatrices) * 100 if total_operatrices > 0 else 0
                
                # Variabilité
                kpis["variabilite"] = df_rendement["rendement"].std()
        
        if not df_pannes.empty:
            # Pannes
            kpis["nb_pannes"] = len(df_pannes)
            
            # MTBF
            if len(df_pannes) > 1 and 'date_heure' in df_pannes.columns:
                try:
                    deltas = df_pannes["date_heure"].sort_values().diff().dt.total_seconds() / 60
                    kpis["mtbf"] = deltas.mean()
                except:
                    kpis["mtbf"] = 0
        
        if not df_erreurs.empty:
            # Erreurs
            kpis["ratio_erreurs"] = (len(df_erreurs) / len(df_rendement)) * 100 if not df_rendement.empty else 0
        
        # Score global
        kpis["score_global"] = min(100, max(0, 100 - (
            max(0, kpis.get("non_productivite", 0) - SEUILS["non_productivite"]) + 
            max(0, kpis.get("sous_performance", 0) - SEUILS["sous_performance"]) +
            max(0, kpis.get("variabilite", 0) - SEUILS["variabilite"]) * 2 +
            max(0, kpis.get("nb_pannes", 0) - SEUILS["pannes"]) * 5 +
            max(0, kpis.get("ratio_erreurs", 0) - SEUILS["erreurs"])
        )))
    
    except Exception as e:
        st.error(f"Erreur lors du calcul des KPIs: {str(e)}")
    
    return kpis

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

    kpis = calculer_kpis(df_rendement, df_pannes, df_erreurs)
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
            <div>Score global: <strong>{kpis.get('score_global', 0):.0f}/100</strong></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --------------------------
# 🔔 SECTION ALERTES AMÉLIORÉE
# --------------------------
def check_alertes(kpis):
    alertes = []
    
    try:
        if kpis.get("rendement_ligne1", 0) < SEUILS["rendement"]["moyen"]:
            alertes.append({
                "type": "Rendement",
                "message": f"Rendement ligne 1 faible: {kpis['rendement_ligne1']:.1f} kg/h",
                "gravite": "high",
                "icon": "📉"
            })
        
        if kpis.get("rendement_ligne2", 0) < SEUILS["rendement"]["moyen"]:
            alertes.append({
                "type": "Rendement", 
                "message": f"Rendement ligne 2 faible: {kpis['rendement_ligne2']:.1f} kg/h",
                "gravite": "high",
                "icon": "📉"
            })
        
        if kpis.get("non_productivite", 0) > SEUILS["non_productivite"]:
            alertes.append({
                "type": "Productivité",
                "message": f"Taux de non-productivité élevé: {kpis['non_productivite']:.1f}%",
                "gravite": "medium",
                "icon": "⏱️"
            })
        
        if kpis.get("sous_performance", 0) > SEUILS["sous_performance"]:
            alertes.append({
                "type": "Performance",
                "message": f"% opératrices sous-performantes: {kpis['sous_performance']:.1f}%",
                "gravite": "medium",
                "icon": "👎"
            })
        
        if kpis.get("variabilite", 0) > SEUILS["variabilite"]:
            alertes.append({
                "type": "Consistance",
                "message": f"Variabilité du rendement élevée: {kpis['variabilite']:.1f} kg/h",
                "gravite": "medium",
                "icon": "📊"
            })
        
        if kpis.get("nb_pannes", 0) >= SEUILS["pannes"]:
            alertes.append({
                "type": "Pannes",
                "message": f"Nombre de pannes signalées: {kpis['nb_pannes']}",
                "gravite": "high",
                "icon": "🔧"
            })
        
        if kpis.get("ratio_erreurs", 0) > SEUILS["erreurs"]:
            alertes.append({
                "type": "Erreurs",
                "message": f"Ratio erreurs élevé: {kpis['ratio_erreurs']:.1f}%",
                "gravite": "high",
                "icon": "❌"
            })
    except Exception as e:
        st.error(f"Erreur lors de la vérification des alertes: {str(e)}")
    
    return alertes

def display_alertes(alertes):
    if not alertes:
        st.success("✅ Aucune alerte en cours - Toutes les métriques sont dans les normes")
        return
    
    with st.expander(f"🚨 Alertes ({len(alertes)})", expanded=True):
        for alerte in alertes:
            # Définir la couleur en fonction de la gravité
            if alerte.get("gravite") == "high":
                border_color = COLORS["danger"]
                bg_color = "#FFF5F5"
            elif alerte.get("gravite") == "medium":
                border_color = COLORS["warning"]
                bg_color = "#FFF9E6"
            else:
                border_color = COLORS["secondary"]
                bg_color = "#F5F5FF"
            
            st.markdown(f"""
            <div style="
                border-left: 4px solid {border_color};
                background-color: {bg_color};
                padding: 1rem;
                margin-bottom: 0.75rem;
                border-radius: 8px;
                display: flex;
                align-items: center;
                gap: 12px;
            ">
                <div style="font-size: 24px;">{alerte.get('icon', '⚠️')}</div>
                <div>
                    <div style="font-weight: 600; color: {COLORS['dark']}">{alerte['type']}</div>
                    <div>{alerte['message']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("Marquer comme lues", key="clear_alerts", type="secondary"):
            st.session_state.alertes = []
            st.rerun()

# --------------------------
# 🎨 SIDEBAR (placée avant la section opérateur)
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
# Afficher les alertes après la sidebar et avant le contenu principal
# --------------------------
nouvelles_alertes = check_alertes(kpis)

# Mise à jour des alertes en session
if not hasattr(st.session_state, 'alertes'):
    st.session_state.alertes = []

# Ajouter seulement les nouvelles alertes qui n'existent pas déjà
for alerte in nouvelles_alertes:
    if alerte['message'] not in [a['message'] for a in st.session_state.alertes]:
        st.session_state.alertes.append(alerte)

# Afficher les alertes
display_alertes(st.session_state.alertes)

# --------------------------
# 👷 INTERFACE OPERATEUR
# --------------------------
if st.session_state.role == "operateur":
    # Section principale en 2 colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Statistiques personnelles
        st.markdown(f"### 📈 Bonjour {st.session_state.username}")
        
        if not df_rendement.empty:
            df_operateur = df_rendement[df_rendement['operatrice_id'] == st.session_state.username]
            
            if not df_operateur.empty:
                # Cartes métriques en grille
                cols = st.columns(3)
                with cols[0]:
                    metric_card("Votre rendement", f"{df_operateur['rendement'].mean():.1f} kg/h", 
                               icon="⚡", color=COLORS["primary"])
                with cols[1]:
                    metric_card("Total produit", f"{df_operateur['poids_kg'].sum():.1f} kg", 
                               icon="📦", color=COLORS["secondary"])
                with cols[2]:
                    metric_card("Pesées", f"{len(df_operateur)}", 
                               icon="✍️", color=COLORS["success"])
                
                # Graphique de performance
                st.markdown("#### Votre progression")
                if 'date' in df_operateur.columns:
                    fig = px.line(
                        df_operateur.sort_values('date'),
                        x='date',
                        y='rendement',
                        height=300,
                        template="plotly_white"
                    )
                    fig.update_layout(
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis_title="Date",
                        yaxis_title="Rendement (kg/h)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Vous n'avez pas encore enregistré de pesée aujourd'hui.")
        # Formulaire de signalement
        with st.expander("⚠️ Signaler un problème"):
            with st.form("operateur_probleme_form"):
                type_probleme = st.selectbox("Type de problème", ["Panne", "Erreur", "Problème qualité", "Autre"])
                ligne = st.selectbox("Ligne concernée", [1, 2])
                gravite = st.select_slider("Gravité", options=["Léger", "Modéré", "Grave", "Critique"])
                description = st.text_area("Description détaillée")
                
                submitted = st.form_submit_button("⚠️ Envoyer le signalement")
                
                if submitted:
                    table = TABLE_PANNES if type_probleme == "Panne" else TABLE_ERREURS
                    data = {
                        "ligne": ligne,
                        "type_erreur": type_probleme,
                        "gravite": gravite,
                        "description": description,
                        "operatrice_id": st.session_state.username,
                        "date_heure": datetime.now().isoformat() + "Z",
                        "created_at": datetime.now().isoformat() + "Z"
                    }
                    
                    try:
                        response = requests.post(
                            f"{SUPABASE_URL}/rest/v1/{table}",
                            headers=headers,
                            json=data
                        )
                        if response.status_code == 201:
                            st.success("Signalement envoyé au responsable!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Erreur {response.status_code}: {response.text}")
                    except Exception as e:
                        st.error(f"Erreur: {str(e)}")
    with col2:
        # Formulaire simplifié pour les opérateurs
        with st.form("operateur_pesee_form", clear_on_submit=True):
            cols = st.columns(3)
            with cols[0]:
                ligne = st.selectbox("Ligne", [1, 2])
                poids_kg = st.number_input("Poids (kg)", min_value=0.1, value=1.0, step=0.1)
            with cols[1]:
                numero_pesee = st.number_input("N° Pesée", min_value=1, value=1)
                heure_travail = st.number_input("Heures travaillées", min_value=0.1, value=5.0, step=0.1)
            with cols[2]:
                date_pesee = st.date_input("Date", datetime.now().date())
                commentaire = st.text_input("Commentaire (optionnel)")
            
            submitted = st.form_submit_button("💾 Enregistrer")
            
            if submitted:
                data = {
                    "operatrice_id": st.session_state.username,
                    "poids_kg": poids_kg,
                    "ligne": ligne,
                    "numero_pesee": numero_pesee,
                    "date": date_pesee.isoformat(),
                    "heure_travail": heure_travail,
                    "commentaire_pesee": commentaire,
                    "created_at": datetime.now().isoformat() + "Z",
                    "rendement": poids_kg / heure_travail,
                    "niveau_rendement": "Excellent" if (poids_kg / heure_travail) >= 4.5 else 
                                        "Acceptable" if (poids_kg / heure_travail) >= 4.0 else
                                        "Faible" if (poids_kg / heure_travail) >= 3.5 else "Critique"
                }
                
                try:
                    response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/{TABLE_RENDEMENT}",
                        headers=headers,
                        json=data
                    )
                    if response.status_code == 201:
                        st.success("Pesée enregistrée avec succès!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Erreur {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement: {str(e)}")
    
   
    # Onglets secondaires
      tab1, tab2 = st.tabs(["📅 Historique", "🏆 Classement"])
    with tab1:
        st.markdown("#### Votre activité récente")
        if not df_rendement.empty:
            df_mes_pesees = df_rendement[df_rendement['operatrice_id'] == st.session_state.username]
            if not df_mes_pesees.empty:
                st.dataframe(
                    df_mes_pesees.sort_values('date', ascending=False).head(20),
                    column_config={
                        "date": "Date",
                        "ligne": "Ligne",
                        "poids_kg": st.column_config.NumberColumn("Poids (kg)", format="%.1f kg"),
                        "numero_pesee": "N° Pesée",
                        "rendement": st.column_config.NumberColumn("Rendement (kg/h)", format="%.1f"),
                        "niveau_rendement": "Niveau"
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Aucune pesée enregistrée")
        
        st.markdown("#### Vos signalements")
        if not df_pannes.empty or not df_erreurs.empty:
            df_mes_pannes = df_pannes[df_pannes['operatrice_id'] == st.session_state.username]
            df_mes_erreurs = df_erreurs[df_erreurs['operatrice_id'] == st.session_state.username]
            
            if not df_mes_pannes.empty or not df_mes_erreurs.empty:
                df_signals = pd.concat([
                    df_mes_pannes.assign(type="Panne"),
                    df_mes_erreurs.assign(type="Erreur")
                ])
                
                st.dataframe(
                    df_signals.sort_values('date_heure', ascending=False).head(10),
                    column_config={
                        "date_heure": "Date/Heure",
                        "type_erreur": "Type",
                        "ligne": "Ligne",
                        "description": "Description",
                        "gravite": "Gravité"
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Aucun signalement enregistré")
    
    with tab2:
        st.markdown("#### Classement des opérateurs")
        if not df_rendement.empty and 'operatrice_id' in df_rendement.columns:
            perf_operatrices = df_rendement.groupby('operatrice_id')['rendement'].mean().reset_index()
            perf_operatrices = perf_operatrices.sort_values('rendement', ascending=False)
            
            # Mettre en évidence l'utilisateur courant
            perf_operatrices["Vous"] = perf_operatrices["operatrice_id"] == st.session_state.username
            
            fig = px.bar(
                perf_operatrices.head(10),
                x='rendement',
                y='operatrice_id',
                orientation='h',
                color='Vous',
                color_discrete_map={True: COLORS['primary'], False: COLORS['secondary']},
                labels={'operatrice_id': 'Opératrice', 'rendement': 'Rendement moyen (kg/h)'},
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Aucune donnée disponible pour le classement")

    st.stop()

# --------------------------
# 👨‍💼 INTERFACE ADMIN/MANAGER
# --------------------------
# Section KPI principaux
st.markdown("### 📊 Indicateurs clés")

# Première ligne de métriques
cols = st.columns(4)
with cols[0]:
    color = COLORS["success"] if kpis.get("rendement_ligne1", 0) >= SEUILS["rendement"]["haut"] else COLORS["warning"] if kpis.get("rendement_ligne1", 0) >= SEUILS["rendement"]["moyen"] else COLORS["danger"]
    metric_card("Rendement L1", f"{kpis.get('rendement_ligne1', 0):.1f} kg/h", 
               f"Cible: {SEUILS['rendement']['haut']} kg/h", "📈", color)

with cols[1]:
    color = COLORS["success"] if kpis.get("rendement_ligne2", 0) >= SEUILS["rendement"]["haut"] else COLORS["warning"] if kpis.get("rendement_ligne2", 0) >= SEUILS["rendement"]["moyen"] else COLORS["danger"]
    metric_card("Rendement L2", f"{kpis.get('rendement_ligne2', 0):.1f} kg/h", 
               f"Cible: {SEUILS['rendement']['haut']} kg/h", "📉", color)

with cols[2]:
    color = COLORS["success"] if kpis.get("non_productivite", 0) < SEUILS["non_productivite"] else COLORS["danger"]
    metric_card("Non-productivité", f"{kpis.get('non_productivite', 0):.1f}%", 
               f"Seuil: {SEUILS['non_productivite']}%", "⏱️", color)

with cols[3]:
    color = COLORS["success"] if kpis.get("ratio_erreurs", 0) < SEUILS["erreurs"] else COLORS["danger"]
    metric_card("Taux d'erreurs", f"{kpis.get('ratio_erreurs', 0):.1f}%", 
               f"Seuil: {SEUILS['erreurs']}%", "❌", color)

# Deuxième ligne de métriques
cols = st.columns(4)
with cols[0]:
    color = COLORS["success"] if kpis.get("sous_performance", 0) < SEUILS["sous_performance"] else COLORS["danger"]
    metric_card("Sous-performance", f"{kpis.get('sous_performance', 0):.1f}%", 
               f"Seuil: {SEUILS['sous_performance']}%", "👎", color)

with cols[1]:
    color = COLORS["success"] if kpis.get("variabilite", 0) < SEUILS["variabilite"] else COLORS["danger"]
    metric_card("Variabilité", f"{kpis.get('variabilite', 0):.1f} kg/h", 
               f"Seuil: {SEUILS['variabilite']} kg/h", "📊", color)

with cols[2]:
    color = COLORS["success"] if kpis.get("nb_pannes", 0) < SEUILS["pannes"] else COLORS["danger"]
    metric_card("Pannes", f"{kpis.get('nb_pannes', 0)}", 
               f"Seuil: {SEUILS['pannes']}", "🔧", color)

with cols[3]:
    if "mtbf" in kpis:
        metric_card("MTBF", f"{kpis['mtbf']:.1f} min", "Temps moyen entre pannes", "⏳", COLORS["primary"])
    else:
        metric_card("MTBF", "N/A", "Pas assez de données", "⏳", COLORS["secondary"])

# Section visualisations
st.markdown("### 📈 Visualisations")

tab1, tab2, tab3, tab4 = st.tabs(["Rendements", "Performance", "Pannes", "Erreurs"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Évolution temporelle")
        if not df_rendement.empty and 'date' in df_rendement.columns:
            df_rendement['jour'] = df_rendement['date'].dt.date
            df_rend_jour = df_rendement.groupby(['jour', 'ligne'])['rendement'].mean().reset_index()
            
            fig = px.line(
                df_rend_jour,
                x='jour',
                y='rendement',
                color='ligne',
                labels={'jour': 'Date', 'rendement': 'Rendement (kg/h)'},
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Distribution")
        if not df_rendement.empty:
            fig = px.histogram(
                df_rendement,
                x='rendement',
                color='ligne',
                nbins=20,
                barmode='overlay',
                labels={'rendement': 'Rendement (kg/h)'},
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("#### Performance par opératrice")
    if not df_rendement.empty and 'operatrice_id' in df_rendement.columns:
        perf_operatrices = df_rendement.groupby('operatrice_id').agg(
            rendement_moyen=('rendement', 'mean'),
            total_kg=('poids_kg', 'sum'),
            nb_pesees=('numero_pesee', 'count')
        ).reset_index()
        
        fig = px.scatter(
            perf_operatrices,
            x='nb_pesees',
            y='rendement_moyen',
            size='total_kg',
            color='rendement_moyen',
            hover_name='operatrice_id',
            labels={
                'nb_pesees': 'Nombre de pesées',
                'rendement_moyen': 'Rendement moyen (kg/h)',
                'total_kg': 'Total produit (kg)'
            },
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    if not df_pannes.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Pannes par ligne")
            pannes_ligne = df_pannes.groupby('ligne').size().reset_index(name='count')
            fig = px.pie(
                pannes_ligne,
                values='count',
                names='ligne',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Chronologie des pannes")
            if 'date_heure' in df_pannes.columns:
                df_pannes['heure'] = df_pannes['date_heure'].dt.hour
                pannes_heure = df_pannes.groupby('heure').size().reset_index(name='count')
                fig = px.bar(
                    pannes_heure,
                    x='heure',
                    y='count',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

with tab4:
    if not df_erreurs.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Types d'erreurs")
            erreurs_type = df_erreurs.groupby('type_erreur').size().reset_index(name='count')
            fig = px.bar(
                erreurs_type,
                x='type_erreur',
                y='count',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Gravité des erreurs")
            if 'gravite' in df_erreurs.columns:
                erreurs_gravite = df_erreurs.groupby('gravite').size().reset_index(name='count')
                fig = px.pie(
                    erreurs_gravite,
                    values='count',
                    names='gravite',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

# Section gestion
st.markdown("### 🛠️ Gestion")

tab1, tab2, tab3 = st.tabs(["Opérateurs", "Pannes/Erreurs", "Paramètres"])
with tab2:
    # Signalement de problème (admin)
    with st.expander("⚠️ Signaler un problème technique", expanded=False):
        with st.form("probleme_form"):
            cols = st.columns(2)
            with cols[0]:
                type_probleme = st.selectbox("Type de problème", ["Panne", "Erreur", "Problème qualité", "Autre"])
                ligne = st.selectbox("Ligne concernée", [1, 2])
            with cols[1]:
                gravite = st.select_slider("Gravité", options=["Léger", "Modéré", "Grave", "Critique"])
            
            description = st.text_area("Description détaillée")
            
            submitted = st.form_submit_button("⚠️ Envoyer le signalement")
            
            if submitted:
                table = TABLE_PANNES if type_probleme == "Panne" else TABLE_ERREURS
                data = {
                    "ligne": ligne,
                    "type_erreur": type_probleme,
                    "gravite": gravite,
                    "description": description,
                    "operatrice_id": st.session_state.username,
                    "date_heure": datetime.now().isoformat() + "Z",
                    "created_at": datetime.now().isoformat() + "Z"
                }
                
                try:
                    response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/{table}",
                        headers=headers,
                        json=data
                    )
                    if response.status_code == 201:
                        st.success("Signalement enregistré!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Erreur {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")

with tab3:
    if st.session_state.role in ["admin", "manager"]:
        with st.expander("⚙️ Paramètres des seuils", expanded=True):
            SEUILS["rendement"]["haut"] = st.number_input("Seuil haut rendement (kg/h)", value=4.5, step=0.1)
            SEUILS["rendement"]["moyen"] = st.number_input("Seuil moyen rendement (kg/h)", value=4.0, step=0.1)
            SEUILS["non_productivite"] = st.number_input("Seuil non-productivité (%)", value=20)
            SEUILS["sous_performance"] = st.number_input("Seuil sous-performance (%)", value=25)
            SEUILS["variabilite"] = st.number_input("Seuil variabilité (kg/h)", value=5.0, step=0.1)
            SEUILS["pannes"] = st.number_input("Seuil alertes pannes", value=3)
            SEUILS["erreurs"] = st.number_input("Seuil erreurs (%)", value=10)
# 📅 Filtres (uniquement pour admin/manager)
if st.session_state.role in ["admin", "manager"] and not df_rendement.empty:
    with st.expander("🔍 Filtres"):
        if "date" in df_rendement.columns:
            date_min = df_rendement["date"].min().date() if not df_rendement.empty else datetime.today().date()
            date_max = df_rendement["date"].max().date() if not df_rendement.empty else datetime.today().date()
            start_date, end_date = st.date_input("Plage de dates", [date_min, date_max])
            df_rendement = df_rendement[(df_rendement["date"].dt.date >= start_date )& 
                                       (df_rendement["date"].dt.date <= end_date)]
        
        if 'ligne' in df_rendement.columns:
            lignes = sorted(df_rendement['ligne'].unique())
            selected_lignes = st.multiselect("Lignes de production", options=lignes, default=lignes)
            df_rendement = df_rendement[df_rendement['ligne'].isin(selected_lignes)] if selected_lignes else df_rendement

# ➕ Formulaire d'ajout de pesée
if st.session_state.role in ["admin", "manager"]:
    st.subheader("➕ Ajouter une nouvelle pesée")
    with st.form("ajout_pesee_form", clear_on_submit=True):
        cols = st.columns([1, 1, 1, 1])
        with cols[0]:
            ligne = st.selectbox("Ligne", [1, 2], key="pesee_ligne")
            operatrice_id = st.text_input("ID Opératrice", key="pesee_operatrice")
        with cols[1]:
            poids_kg = st.number_input("Poids (kg)", min_value=0.1, value=1.0, step=0.1, key="pesee_poids")
            numero_pesee = st.number_input("N° Pesée", min_value=1, value=1, key="pesee_numero")
        with cols[2]:
            date_pesee = st.date_input("Date de pesée", datetime.now().date(), key="pesee_date")
            heure_travail = st.number_input("Heures travaillées", min_value=0.1, value=5.0, step=0.1, key="pesee_heures")
        with cols[3]:
            commentaire = st.text_input("Commentaire (optionnel)", key="pesee_commentaire")
        
        submitted = st.form_submit_button("💾 Enregistrer la pesée")
        
        if submitted:
            # Validation des champs obligatoires
            if not operatrice_id:
                st.error("L'ID opératrice est obligatoire")
            else:
                rendement = poids_kg / heure_travail
                niveau_rendement = "Excellent" if rendement >= 4.5 else \
                                 "Acceptable" if rendement >= 4.0 else \
                                 "Faible" if rendement >= 3.5 else "Critique"
                
                data = {
                    "operatrice_id": operatrice_id,
                    "poids_kg": poids_kg,
                    "ligne": ligne,
                    "numero_pesee": numero_pesee,
                    "date": date_pesee.isoformat(),
                    "heure_travail": heure_travail,
                    "commentaire_pesee": commentaire,
                    "created_at": datetime.now().isoformat() + "Z",
                
                }
                
                try:
                    response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/{TABLE_RENDEMENT}",
                        headers=headers,
                        json=data
                    )
                    if response.status_code == 201:
                        st.success("Pesée enregistrée avec succès!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Erreur {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement: {str(e)}")

