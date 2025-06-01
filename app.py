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
# Styles CSS
st.markdown("""
<style>
    .stDataFrame {
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stDataFrame th {
        background-color: #2E86AB;
        color: white !important;
    }
    .stDataFrame tr:nth-child(even) {
        background-color: #f5f5f5;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-left: 4px solid #2E86AB;
    }
</style>
""", unsafe_allow_html=True)
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

# Initialiser les seuils dans session_state
if 'seuils' not in st.session_state:
    st.session_state.seuils = {
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
                seuil_sous_perf = st.session_state.seuils["rendement"]["moyen"]
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
            max(0, kpis.get("non_productivite", 0) - st.session_state.seuils["non_productivite"]) + 
            max(0, kpis.get("sous_performance", 0) - st.session_state.seuils["sous_performance"]) +
            max(0, kpis.get("variabilite", 0) - st.session_state.seuils["variabilite"]) * 2 +
            max(0, kpis.get("nb_pannes", 0) - st.session_state.seuils["pannes"]) * 5 +
            max(0, kpis.get("ratio_erreurs", 0) - st.session_state.seuils["erreurs"])
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
def display_performance_charts(df_rendement):
    if not df_rendement.empty and 'operatrice_id' in df_rendement.columns:
        st.markdown("### 📊 Performance des Opératrices")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("#### Top 10 des Opératrices")
            perf_operatrices = df_rendement.groupby('operatrice_id').agg(
                rendement_moyen=('rendement', 'mean'),
                total_kg=('poids_kg', 'sum'),
                nb_pesees=('numero_pesee', 'count')
            ).reset_index()
            
            top_operatrices = perf_operatrices.sort_values('rendement_moyen', ascending=False).head(10)
            
            fig = px.bar(
                top_operatrices,
                x='operatrice_id',
                y='rendement_moyen',
                color='total_kg',
                labels={
                    'operatrice_id': 'Opératrice',
                    'rendement_moyen': 'Rendement moyen (kg/h)',
                    'total_kg': 'Poids total (kg)'
                },
                color_continuous_scale='Viridis',
                height=500
            )
            
            fig.update_layout(
                plot_bgcolor='white',
                xaxis_title="Opératrice",
                yaxis_title="Rendement moyen (kg/h)",
                margin=dict(l=20, r=20, t=40, b=60)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Légende")
            st.markdown("""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
                <p><span style="color: #440154; font-weight: bold;">■</span> Haut rendement</p>
                <p><span style="color: #21918c; font-weight: bold;">■</span> Rendement moyen</p>
                <p><span style="color: #fde725; font-weight: bold;">■</span> Bas rendement</p>
                <p>La hauteur = rendement moyen</p>
                <p>La couleur = poids total</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### Détail des Rendements")
        df_tableau = df_rendement.groupby('operatrice_id').agg(
            Rendement_moyen=('rendement', 'mean'),
            Poids_total=('poids_kg', 'sum'),
            Nombre_pesees=('numero_pesee', 'count'),
            Derniere_date=('date', 'max')
        ).reset_index()
        
        df_tableau['Rendement_moyen'] = df_tableau['Rendement_moyen'].round(2)
        
        st.dataframe(
            df_tableau.sort_values('Rendement_moyen', ascending=False),
            column_config={
                "operatrice_id": "Opératrice",
                "Rendement_moyen": st.column_config.NumberColumn("Rendement (kg/h)", format="%.2f"),
                "Poids_total": st.column_config.NumberColumn("Poids total (kg)", format="%.1f"),
                "Nombre_pesees": "Pesées",
                "Derniere_date": "Dernière activité"
            },
            hide_index=True,
            use_container_width=True
        )
# --------------------------
# 🔐 PAGE DE CONNEXION
# --------------------------
if not st.session_state.authenticated:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://www.boudjebeldates.com/wp-content/uploads/2022/08/boudjebel-vacpa-deglet-noor-logo-png.png", width=300)
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
        if kpis.get("rendement_ligne1", 0) < st.session_state.seuils["rendement"]["moyen"]:
            alertes.append({
                "type": "Rendement",
                "message": f"Rendement ligne 1 faible: {kpis['rendement_ligne1']:.1f} kg/h",
                "gravite": "high",
                "icon": "📉"
            })
        
        if kpis.get("rendement_ligne2", 0) < st.session_state.seuils["rendement"]["moyen"]:
            alertes.append({
                "type": "Rendement", 
                "message": f"Rendement ligne 2 faible: {kpis['rendement_ligne2']:.1f} kg/h",
                "gravite": "high",
                "icon": "📉"
            })
        
        if kpis.get("non_productivite", 0) > st.session_state.seuils["non_productivite"]:
            alertes.append({
                "type": "Productivité",
                "message": f"Taux de non-productivité élevé: {kpis['non_productivite']:.1f}%",
                "gravite": "medium",
                "icon": "⏱️"
            })
        
        if kpis.get("sous_performance", 0) > st.session_state.seuils["sous_performance"]:
            alertes.append({
                "type": "Performance",
                "message": f"% opératrices sous-performantes: {kpis['sous_performance']:.1f}%",
                "gravite": "medium",
                "icon": "👎"
            })
        
        if kpis.get("variabilite", 0) > st.session_state.seuils["variabilite"]:
            alertes.append({
                "type": "Consistance",
                "message": f"Variabilité du rendement élevée: {kpis['variabilite']:.1f} kg/h",
                "gravite": "medium",
                "icon": "📊"
            })
        
        if kpis.get("nb_pannes", 0) >= st.session_state.seuils["pannes"]:
            alertes.append({
                "type": "Pannes",
                "message": f"Nombre de pannes signalées: {kpis['nb_pannes']}",
                "gravite": "high",
                "icon": "🔧"
            })
        
        if kpis.get("ratio_erreurs", 0) > st.session_state.seuils["erreurs"]:
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
    
    with col2:
        # Actions rapides
        st.markdown("### 🚀 Actions rapides")
        with st.expander("➕ Nouvelle pesée", expanded=True):
            with st.form("operateur_pesee_form", clear_on_submit=True):
                # Charger la liste des opérateurs depuis la table des rendements
                response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/{TABLE_RENDEMENT}?select=operatrice_id",
                    headers=headers
                )
                
                operateurs = ["operateur", "marwa"]  # Valeurs par défaut
                if response.status_code == 200:
                    operateurs = list(set([op['operatrice_id'] for op in response.json()]))
                
                # Sélection de l'opérateur
                operatrice_id = st.selectbox(
                    "Opérateur",
                    options=operateurs,
                    index=operateurs.index(st.session_state.username) if st.session_state.username in operateurs else 0
                )
                
                ligne = st.selectbox("Ligne", [1, 2])
                poids_kg = st.number_input("Poids (kg)", min_value=0.1, value=1.0, step=0.1)
                numero_pesee = st.number_input("N° Pesée", min_value=1, value=1)
                heure_travail = st.number_input("Heures travaillées", min_value=0.1, value=5.0, step=0.1)
                commentaire = st.text_input("Commentaire (optionnel)")
                
                submitted = st.form_submit_button("💾 Enregistrer la pesée")
                
                if submitted:
                    # Vérifier si une pesée avec ce numéro existe déjà pour aujourd'hui
                    check_url = f"{SUPABASE_URL}/rest/v1/{TABLE_RENDEMENT}?select=id&operatrice_id=eq.{operatrice_id}&date=eq.{datetime.now().date().isoformat()}&numero_pesee=eq.{numero_pesee}"
                    check_response = requests.get(check_url, headers=headers)
                    
                    if check_response.status_code == 200 and len(check_response.json()) > 0:
                        st.error("Une pesée avec ce numéro existe déjà pour aujourd'hui. Veuillez utiliser un numéro différent.")
                    else:
                        data = {
                            "operatrice_id": operatrice_id,
                            "poids_kg": poids_kg,
                            "ligne": ligne,
                            "numero_pesee": numero_pesee,
                            "date": datetime.now().date().isoformat(),
                            "heure_travail": heure_travail,
                            "commentaire_pesee": commentaire,
                            "created_at": datetime.now().isoformat() + "Z",
                            "type_produit": "marcadona"
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
                            st.error(f"Erreur de connexion: {str(e)}")

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
      st.markdown("#### 🏆 Top 10 des opératrices (affichage visuel simple)")

      if not df_rendement.empty and 'operatrice_id' in df_rendement.columns:
        import plotly.graph_objects as go

        # Calcul du rendement moyen par opératrice
        perf_operatrices = df_rendement.groupby('operatrice_id')['rendement'].mean().reset_index()
        perf_operatrices = perf_operatrices.sort_values(by='rendement', ascending=False).reset_index(drop=True)
        top10 = perf_operatrices.head(10)

        # Couleurs personnalisées pour chaque opératrice
        couleurs = [
            "#FFD700", "#C0C0C0", "#CD7F32", "#FF69B4", "#FF8C00",
            "#00CED1", "#ADFF2F", "#9370DB", "#00FA9A", "#4682B4"
        ]

        # Création du graphique
        fig = go.Figure(go.Bar(
            x=top10['operatrice_id'],
            y=top10['rendement'],
            marker=dict(color=couleurs[:len(top10)]),
            text=top10['rendement'].round(1).astype(str) + " kg/h",
            textposition='outside',
            width=0.85
        ))

        fig.update_layout(
            height=500,
            plot_bgcolor='white',
            margin=dict(l=20, r=20, t=40, b=60),
            showlegend=False,
            xaxis=dict(
                tickfont=dict(size=16, color='black'),
                title='',
                showline=False,
                showticklabels=True,
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                visible=False  # ❌ Masquer complètement l'axe des ordonnées
            ),
        )

        st.plotly_chart(fig, use_container_width=True)
      else:
        st.warning("⚠️ Aucune donnée de rendement disponible pour le classement.")

    st.stop()
# Nouvelle section expandable
    with st.expander("📊 Voir les performances de l'équipe", expanded=False):
        display_performance_charts(df_rendement)
# --------------------------
# 👨‍💼 INTERFACE ADMIN/MANAGER
# --------------------------
# Section KPI principaux
# Section Indicateurs clés - Version professionnelle
st.markdown("### 📊 Tableau de bord des performances")

# Création d'une grille responsive
with st.container():
    # Première ligne - Rendements et productivité
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        rendement_l1 = kpis.get("rendement_ligne1", 0)
        color = COLORS["success"] if rendement_l1 >= st.session_state.seuils["rendement"]["haut"] else COLORS["warning"] if rendement_l1 >= st.session_state.seuils["rendement"]["moyen"] else COLORS["danger"]
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {color}">
            <div style="font-size: 14px; color: #555; margin-bottom: 5px;">Rendement Ligne 1</div>
            <div style="font-size: 24px; font-weight: bold; color: {color}">{rendement_l1:.1f} kg/h</div>
            <div style="font-size: 12px; color: #777;">Cible: {st.session_state.seuils['rendement']['haut']} kg/h</div>
            <progress value="{rendement_l1}" max="6" style="width: 100%; height: 6px;"></progress>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        rendement_l2 = kpis.get("rendement_ligne2", 0)
        color = COLORS["success"] if rendement_l2 >= st.session_state.seuils["rendement"]["haut"] else COLORS["warning"] if rendement_l2 >= st.session_state.seuils["rendement"]["moyen"] else COLORS["danger"]
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {color}">
            <div style="font-size: 14px; color: #555; margin-bottom: 5px;">Rendement Ligne 2</div>
            <div style="font-size: 24px; font-weight: bold; color: {color}">{rendement_l2:.1f} kg/h</div>
            <div style="font-size: 12px; color: #777;">Cible: {st.session_state.seuils['rendement']['haut']} kg/h</div>
            <progress value="{rendement_l2}" max="6" style="width: 100%; height: 6px;"></progress>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        non_prod = kpis.get("non_productivite", 0)
        color = COLORS["success"] if non_prod < st.session_state.seuils["non_productivite"] else COLORS["danger"]
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {color}">
            <div style="font-size: 14px; color: #555; margin-bottom: 5px;">Non-productivité</div>
            <div style="font-size: 24px; font-weight: bold; color: {color}">{non_prod:.1f}%</div>
            <div style="font-size: 12px; color: #777;">Seuil: {st.session_state.seuils['non_productivite']}%</div>
            <progress value="{non_prod}" max="100" style="width: 100%; height: 6px;"></progress>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        sous_perf = kpis.get("sous_performance", 0)
        color = COLORS["success"] if sous_perf < st.session_state.seuils["sous_performance"] else COLORS["danger"]
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {color}">
            <div style="font-size: 14px; color: #555; margin-bottom: 5px;">Sous-performance</div>
            <div style="font-size: 24px; font-weight: bold; color: {color}">{sous_perf:.1f}%</div>
            <div style="font-size: 12px; color: #777;">Seuil: {st.session_state.seuils['sous_performance']}%</div>
            <progress value="{sous_perf}" max="100" style="width: 100%; height: 6px;"></progress>
        </div>
        """, unsafe_allow_html=True)

    # Deuxième ligne - Autres indicateurs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        variabilite = kpis.get("variabilite", 0)
        color = COLORS["success"] if variabilite < st.session_state.seuils["variabilite"] else COLORS["danger"]
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {color}">
            <div style="font-size: 14px; color: #555; margin-bottom: 5px;">Variabilité</div>
            <div style="font-size: 24px; font-weight: bold; color: {color}">{variabilite:.1f} kg/h</div>
            <div style="font-size: 12px; color: #777;">Seuil: {st.session_state.seuils['variabilite']} kg/h</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pannes = kpis.get("nb_pannes", 0)
        color = COLORS["success"] if pannes < st.session_state.seuils["pannes"] else COLORS["danger"]
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {color}">
            <div style="font-size: 14px; color: #555; margin-bottom: 5px;">Pannes</div>
            <div style="font-size: 24px; font-weight: bold; color: {color}">{pannes}</div>
            <div style="font-size: 12px; color: #777;">Seuil: {st.session_state.seuils['pannes']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        erreurs = kpis.get("ratio_erreurs", 0)
        color = COLORS["success"] if erreurs < st.session_state.seuils["erreurs"] else COLORS["danger"]
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {color}">
            <div style="font-size: 14px; color: #555; margin-bottom: 5px;">Taux d'erreurs</div>
            <div style="font-size: 24px; font-weight: bold; color: {color}">{erreurs:.1f}%</div>
            <div style="font-size: 12px; color: #777;">Seuil: {st.session_state.seuils['erreurs']}%</div>
            <progress value="{erreurs}" max="100" style="width: 100%; height: 6px;"></progress>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        mtbf = kpis.get("mtbf", 0)
        color = COLORS["primary"]
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {color}">
            <div style="font-size: 14px; color: #555; margin-bottom: 5px;">MTBF</div>
            <div style="font-size: 24px; font-weight: bold; color: {color}">{mtbf:.1f} min</div>
            <div style="font-size: 12px; color: #777;">Temps moyen entre pannes</div>
        </div>
        """, unsafe_allow_html=True)
display_performance_charts(df_rendement)
# Ajout d'une légende visuelle
st.markdown("""
<div style="display: flex; justify-content: flex-end; gap: 15px; margin-top: 10px;">
    <div style="display: flex; align-items: center;">
        <div style="width: 12px; height: 12px; background-color: #3BB273; border-radius: 2px; margin-right: 5px;"></div>
        <span style="font-size: 12px;">Dans les normes</span>
    </div>
    <div style="display: flex; align-items: center;">
        <div style="width: 12px; height: 12px; background-color: #F18F01; border-radius: 2px; margin-right: 5px;"></div>
        <span style="font-size: 12px;">Attention</span>
    </div>
    <div style="display: flex; align-items: center;">
        <div style="width: 12px; height: 12px; background-color: #E71D36; border-radius: 2px; margin-right: 5px;"></div>
        <span style="font-size: 12px;">Hors norme</span>
    </div>
</div>
""", unsafe_allow_html=True)
# Formulaire pour ajouter un nouveau produit
with st.expander("➕ Ajouter un nouveau produit", expanded=False):
        with st.form("nouveau_produit_form", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                reference = st.text_input("Référence*", max_chars=20)
                lot = st.text_input("Lot*", max_chars=15)
                ligne = st.selectbox("Ligne*", [1, 2])
            with cols[1]:
                operateur = st.text_input("Opérateur*", max_chars=50)
                etat = st.selectbox("État*", ['En préparation', 'En cours', 'En contrôle', 'Terminé'])
                date_expiration = st.date_input("Date expiration")
            
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("💾 Enregistrer le produit")
            
            if submitted:
                if not reference or not lot or not operateur:
                    st.error("Les champs marqués d'un * sont obligatoires")
                else:
                    data = {
                        "reference": reference,
                        "lot": lot,
                        "ligne": ligne,
                        "operateur": operateur,
                        "etat": etat,
                        "date_expiration": date_expiration.isoformat() if date_expiration else None,
                        "notes": notes if notes else None
                    }
                    
                    try:
                        response = requests.post(
                            f"{SUPABASE_URL}/rest/v1/produits",
                            headers=headers,
                            json=data
                        )
                        if response.status_code == 201:
                            st.success("Produit enregistré avec succès!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Erreur {response.status_code}: {response.text}")
                    except Exception as e:
                        st.error(f"Erreur lors de l'enregistrement: {str(e)}")
            else:
                  st.info("Aucun produit enregistré dans la base de données")


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

tab1, tab2 = st.tabs(["Pannes/Erreurs", "Paramètres"])

with tab1:
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
                    "date_heure": datetime.now().isoformat(),  # Ajout de la date/heure
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
with tab2:
    if st.session_state.role in ["admin", "manager"]:
        with st.expander("⚙️ Paramètres des seuils", expanded=True):
            # Rendement (float)
            st.session_state.seuils["rendement"]["haut"] = st.number_input(
                "Seuil haut rendement (kg/h)", 
                value=float(st.session_state.seuils["rendement"]["haut"]), 
                step=0.1,
                format="%.1f"
            )
            st.session_state.seuils["rendement"]["moyen"] = st.number_input(
                "Seuil moyen rendement (kg/h)", 
                value=float(st.session_state.seuils["rendement"]["moyen"]), 
                step=0.1,
                format="%.1f"
            )
            
            # Non-productivité (int)
            st.session_state.seuils["non_productivite"] = int(st.number_input(
                "Seuil non-productivité (%)",
                value=int(st.session_state.seuils["non_productivite"]),
                step=1
            ))
            
            # Sous-performance (int)
            st.session_state.seuils["sous_performance"] = int(st.number_input(
                "Seuil sous-performance (%)",
                value=int(st.session_state.seuils["sous_performance"]),
                step=1
            ))
            
            # Variabilité (float)
            st.session_state.seuils["variabilite"] = st.number_input(
                "Seuil variabilité (kg/h)",
                value=float(st.session_state.seuils["variabilite"]),
                step=0.1,
                format="%.1f"
            )
            
            # Pannes (int)
            st.session_state.seuils["pannes"] = int(st.number_input(
                "Seuil nombre de pannes",
                value=int(st.session_state.seuils["pannes"]),
                step=1
            ))
            
            # Erreurs (int)
            st.session_state.seuils["erreurs"] = int(st.number_input(
                "Seuil taux d'erreurs (%)",
                value=int(st.session_state.seuils["erreurs"]),
                step=1
            ))
            
            if st.button("Appliquer les nouveaux seuils"):
                st.cache_data.clear()  # Force le recalcul des KPI
                st.rerun()  # Recharge la page
# --------------------------
# 📅 Filtres (uniquement pour admin/manager)
# --------------------------
if st.session_state.role in ["admin", "manager"]:
    with st.expander("🔍 Filtres"):
        # Vérifie si toutes les colonnes nécessaires existent
        dates_rendement = df_rendement["created_at"] if "created_at" in df_rendement.columns else None
        dates_pannes = df_pannes["created_at"] if "created_at" in df_pannes.columns else None
        dates_erreurs = df_erreurs["created_at"] if "created_at" in df_erreurs.columns else None

        # Choisir une date de référence pour initialiser les filtres
        all_dates = pd.concat([d for d in [dates_rendement, dates_pannes, dates_erreurs] if d is not None])
        if not all_dates.empty:
            date_min = all_dates.min().date()
            date_max = all_dates.max().date()
        else:
            date_min = date_max = datetime.today().date()

        start_date, end_date = st.date_input("Plage de dates", [date_min, date_max])

        # Appliquer les filtres à chaque table
        if dates_rendement is not None:
            df_rendement = df_rendement[
                (df_rendement["created_at"].dt.date >= start_date) &
                (df_rendement["created_at"].dt.date <= end_date)
            ]

        if "created_at" in df_pannes.columns:
            df_pannes = df_pannes[
                (df_pannes["created_at"].dt.date >= start_date) &
                (df_pannes["created_at"].dt.date <= end_date)
            ]
        if "created_at" in df_erreurs.columns:
            df_erreurs = df_erreurs[
                (df_erreurs["created_at"].dt.date >= start_date) &
                (df_erreurs["created_at"].dt.date <= end_date)
            ]
