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
                ligne = st.selectbox("Ligne", [1, 2])
                poids_kg = st.number_input("Poids (kg)", min_value=0.1, value=1.0, step=0.1)
            with cols[1]:
                numero_pesee = st.number_input("N° Pesée", min_value=1, value=1)
                heure_travail = st.number_input("Temps travaillé (h)", min_value=0.1, value=1.0, step=0.1)
            with cols[2]:
                date_pesee = st.date_input("Date", datetime.now().date())
                heure_pesee = st.time_input("Heure", datetime.now().time())
            
            submitted = st.form_submit_button("💾 Enregistrer")
            
            if submitted:
                datetime_pesee = datetime.combine(date_pesee, heure_pesee).isoformat() + "Z"
                rendement = poids_kg / heure_travail
                
                data = {
                    "operatrice_id": st.session_state.username,
                    "poids_kg": poids_kg,
                    "ligne": ligne,
                    "numero_pesee": numero_pesee,
                    "heure_travail": heure_travail,
                    "rendement": rendement,
                    "date_heure": datetime_pesee,
                    "created_at": datetime.now().isoformat() + "Z"
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
    
    with tab2:
        # Formulaire de signalement pour opérateurs
        with st.form("operateur_probleme_form"):
            type_probleme = st.selectbox("Type de problème", ["Panne", "Erreur", "Problème qualité", "Autre"])
            ligne = st.selectbox("Ligne concernée", [1, 2])
            gravite = st.select_slider("Gravité", options=["Léger", "Modéré", "Grave", "Critique"])
            description = st.text_area("Description détaillée")
            
            if st.form_submit_button("⚠️ Envoyer le signalement"):
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
    
    with tab3:
        # Historique des actions de l'opérateur
        st.subheader("Vos dernières pesées")
        
        if not df_rendement.empty:
            df_mes_pesees = df_rendement[df_rendement['operatrice_id'] == st.session_state.username]
            if not df_mes_pesees.empty:
                st.dataframe(
                    df_mes_pesees.sort_values('date_heure', ascending=False).head(20),
                    column_config={
                        "date_heure": "Date/Heure",
                        "ligne": "Ligne",
                        "poids_kg": st.column_config.NumberColumn("Poids (kg)", format="%.1f kg"),
                        "heure_travail": st.column_config.NumberColumn("Temps (h)", format="%.1f h"),
                        "rendement": st.column_config.NumberColumn("Rendement (kg/h)", format="%.1f")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Aucune pesée enregistrée")
    st.stop()

# --------------------------
# 👨‍💼 INTERFACE ADMIN/MANAGER
# --------------------------
# Section KPI principaux
st.markdown("### 📊 Indicateurs clés")

# Calcul des KPIs
if not df_rendement.empty:
    rendement_ligne1 = df_rendement[df_rendement['ligne'] == 1]['rendement'].mean()
    rendement_ligne2 = df_rendement[df_rendement['ligne'] == 2]['rendement'].mean()
else:
    rendement_ligne1 = rendement_ligne2 = 0

# Première ligne de métriques
cols = st.columns(4)
with cols[0]:
    color = COLORS["success"] if rendement_ligne1 >= SEUILS["rendement"]["haut"] else COLORS["warning"] if rendement_ligne1 >= SEUILS["rendement"]["moyen"] else COLORS["danger"]
    metric_card("Rendement L1", f"{rendement_ligne1:.1f} kg/h", 
               f"Cible: {SEUILS['rendement']['haut']} kg/h", "📈", color)

with cols[1]:
    color = COLORS["success"] if rendement_ligne2 >= SEUILS["rendement"]["haut"] else COLORS["warning"] if rendement_ligne2 >= SEUILS["rendement"]["moyen"] else COLORS["danger"]
    metric_card("Rendement L2", f"{rendement_ligne2:.1f} kg/h", 
               f"Cible: {SEUILS['rendement']['haut']} kg/h", "📉", color)

# --------------------------
# FORMULAIRE AJOUT PESÉE (ADMIN/MANAGER)
# --------------------------
st.markdown("### ➕ Ajouter une nouvelle pesée")
with st.form("ajout_pesee_form", clear_on_submit=True):
    cols = st.columns([1, 1, 1, 1])
    
    with cols[0]:
        ligne = st.selectbox("Ligne de production", [1, 2])
        operatrice_id = st.text_input("ID Opératrice", help="Identifiant de l'opératrice responsable")
    
    with cols[1]:
        poids_kg = st.number_input("Poids (kg)", min_value=0.1, value=1.0, step=0.1, 
                                 help="Poids des dattes en kilogrammes")
        temps_travail = st.number_input("Temps travaillé (heures)", min_value=0.1, value=1.0, 
                                      step=0.1, help="Durée du travail en heures")
    
    with cols[2]:
        date_pesee = st.date_input("Date de pesée", datetime.now().date())
        heure_pesee = st.time_input("Heure de pesée", datetime.now().time())
    
    with cols[3]:
        numero_pesee = st.number_input("Numéro de pesée", min_value=1, value=1)
        commentaire = st.text_input("Commentaire (optionnel)")
    
    submitted = st.form_submit_button("💾 Enregistrer la pesée")
    
    if submitted:
        # Validation des champs obligatoires
        if not operatrice_id:
            st.error("L'ID opératrice est obligatoire")
        elif poids_kg <= 0:
            st.error("Le poids doit être supérieur à 0")
        elif temps_travail <= 0:
            st.error("Le temps travaillé doit être supérieur à 0")
        else:
            # Calcul du rendement
            rendement = poids_kg / temps_travail
            
            # Création de la date/heure combinée
            datetime_pesee = datetime.combine(date_pesee, heure_pesee).isoformat() + "Z"
            
            # Préparation des données
            data = {
                "operatrice_id": operatrice_id,
                "poids_kg": float(poids_kg),
                "ligne": int(ligne),
                "numero_pesee": int(numero_pesee),
                "date_heure": datetime_pesee,
                "heure_travail": float(temps_travail),
                "rendement": float(rendement),
                "commentaire_pesee": commentaire if commentaire else None,
                "created_at": datetime.now().isoformat() + "Z"
            }
            
            try:
                # Envoi des données à Supabase
                response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/{TABLE_RENDEMENT}",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 201:
                    st.success("Pesée enregistrée avec succès!")
                    st.balloons()
                    
                    # Affichage des détails enregistrés
                    st.markdown("**Détails de la pesée enregistrée:**")
                    cols = st.columns(2)
                    with cols[0]:
                        st.metric("Opératrice", operatrice_id)
                        st.metric("Ligne", ligne)
                        st.metric("Poids", f"{poids_kg} kg")
                    with cols[1]:
                        st.metric("Temps travaillé", f"{temps_travail} h")
                        st.metric("Rendement", f"{rendement:.2f} kg/h")
                        st.metric("Date/Heure", datetime_pesee)
                    
                    # Réinitialisation du formulaire
                    st.experimental_rerun()
                else:
                    st.error(f"Erreur {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Erreur lors de l'enregistrement: {str(e)}")

# --------------------------
# VISUALISATION DES DONNÉES
# --------------------------
st.markdown("### 📈 Visualisation des données")

if not df_rendement.empty:
    # Filtres temporels
    with st.expander("🔍 Filtres", expanded=True):
        min_date = df_rendement['date_heure'].min().date()
        max_date = df_rendement['date_heure'].max().date()
        date_range = st.date_input("Période", [min_date, max_date])
        
        if len(date_range) == 2:
            df_filtered = df_rendement[
                (df_rendement['date_heure'].dt.date >= date_range[0]) & 
                (df_rendement['date_heure'].dt.date <= date_range[1])
            ]
        else:
            df_filtered = df_rendement
    
    # Graphiques
    tab1, tab2 = st.tabs(["Rendement par ligne", "Performance par opératrice"])
    
    with tab1:
        fig = px.line(
            df_filtered.groupby([df_filtered['date_heure'].dt.date, 'ligne'])['rendement'].mean().reset_index(),
            x='date_heure',
            y='rendement',
            color='ligne',
            title='Évolution du rendement moyen par ligne',
            labels={'date_heure': 'Date', 'rendement': 'Rendement (kg/h)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if 'operatrice_id' in df_filtered.columns:
            df_perf = df_filtered.groupby('operatrice_id').agg(
                rendement_moyen=('rendement', 'mean'),
                total_kg=('poids_kg', 'sum'),
                nb_pesees=('numero_pesee', 'count')
            ).reset_index()
            
            fig = px.bar(
                df_perf.sort_values('rendement_moyen', ascending=False),
                x='operatrice_id',
                y='rendement_moyen',
                color='nb_pesees',
                title='Rendement moyen par opératrice',
                labels={
                    'operatrice_id': 'Opératrice',
                    'rendement_moyen': 'Rendement moyen (kg/h)',
                    'nb_pesees': 'Nombre de pesées'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Aucune donnée de rendement disponible")
