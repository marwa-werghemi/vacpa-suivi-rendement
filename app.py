import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

# --------------------------
# 🎨 CONFIGURATION DU DESIGN
# --------------------------
st.set_page_config(
    page_title="Dashboard VACPA",
    layout="wide",
    page_icon="🌿",
    initial_sidebar_state="collapsed"
)

# Couleurs modernes
COLORS = {
    "primary": "#2E86AB",
    "secondary": "#A23B72",
    "success": "#3BB273",
    "warning": "#F18F01",
    "danger": "#E71D36",
    "dark": "#2B2D42",
    "light": "#F7F7F7"
}

# Style CSS personnalisé
st.markdown(f"""
<style>
    /* Police moderne */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif;
    }}
    
    /* En-tête */
    .header {{
        background-color: {COLORS['primary']};
        color: white;
        padding: 1.5rem;
        border-radius: 0 0 15px 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    
    /* Cartes de statistiques */
    .metric-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: transform 0.2s;
        border-left: 4px solid {COLORS['primary']};
    }}
    
    .metric-card:hover {{
        transform: translateY(-5px);
    }}
    
    /* Boutons */
    .stButton>button {{
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }}
    
    /* Onglets */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 8px 16px;
        border-radius: 8px 8px 0 0 !important;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {COLORS['light']};
    }}
</style>
""", unsafe_allow_html=True)

# --------------------------
# 🔐 AUTHENTIFICATION
# --------------------------
CREDENTIALS = {
    "admin": {"password": "vacpa2025", "role": "admin"},
    "manager": {"password": "manager123456789", "role": "manager"},
    "operateur": {"password": "operateur456789", "role": "operateur"},
    "marwa": {"password": "vacpa2025", "role": "operateur"}
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None

if not st.session_state.authenticated:
    # Page de connexion épurée
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://via.placeholder.com/300x400?text=VACPA+Logo", width=300)
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
# 🧩 COMPOSANTS REUTILISABLES
# --------------------------
def metric_card(title, value, delta=None, icon="📊"):
    """Composant de carte métrique moderne"""
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <div style="font-size: 24px;">{icon}</div>
            <h3 style="margin: 0; color: {COLORS['dark']}">{title}</h3>
        </div>
        <div style="font-size: 28px; font-weight: 600; color: {COLORS['primary']}">{value}</div>
        {f'<div style="color: {COLORS["success"]}; font-size: 14px;">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)

# --------------------------
# 🏠 PAGE PRINCIPALE
# --------------------------
# En-tête personnalisé
st.markdown(f"""
<div class="header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin: 0;">Bienvenue, {st.session_state.username}</h1>
            <p style="margin: 0; opacity: 0.8;">{st.session_state.role.capitalize()} - VACPA Dashboard</p>
        </div>
        <div>
            {datetime.now().strftime("%d %B %Y")}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --------------------------
# 📊 TABLEAU DE BORD OPERATEUR
# --------------------------
if st.session_state.role == "operateur":
    # Section principale en 2 colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Statistiques personnelles
        st.markdown("### 📈 Vos performances")
        
        # Cartes métriques en grille
        cols = st.columns(3)
        with cols[0]:
            metric_card("Rendement moyen", "4.2 kg/h", "+0.3 vs hier", "⚡")
        with cols[1]:
            metric_card("Total produit", "126 kg", icon="📦")
        with cols[2]:
            metric_card("Pesées aujourd'hui", "24", "3 en attente", "✍️")
        
        # Graphique de performance
        st.markdown("#### Votre progression")
        # Exemple de données - à remplacer par vos données réelles
        data = pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=30),
            "Rendement": np.random.normal(4.2, 0.3, 30)
        })
        fig = px.line(data, x="Date", y="Rendement", 
                     height=300, template="plotly_white")
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Actions rapides
        st.markdown("### 🚀 Actions rapides")
        
        with st.expander("➕ Nouvelle pesée", expanded=True):
            with st.form("quick_pesee"):
                ligne = st.selectbox("Ligne", [1, 2])
                poids = st.number_input("Poids (kg)", min_value=0.1)
                submitted = st.form_submit_button("Enregistrer")
                if submitted:
                    st.success("Pesée enregistrée!")
        
        with st.expander("⚠️ Signaler un problème"):
            with st.form("quick_issue"):
                issue_type = st.selectbox("Type", ["Panne", "Erreur", "Autre"])
                description = st.text_area("Description")
                submitted = st.form_submit_button("Envoyer")
                if submitted:
                    st.success("Problème signalé!")
    
    # Onglets secondaires
    tab1, tab2 = st.tabs(["📅 Historique", "🏆 Classement"])
    
    with tab1:
        st.markdown("#### Votre activité récente")
        # Exemple de données tabulaires
        data = pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5),
            "Ligne": [1, 2, 1, 2, 1],
            "Poids (kg)": [12.5, 14.2, 11.8, 13.5, 12.9],
            "Rendement": [4.2, 4.5, 3.9, 4.3, 4.1]
        })
        st.dataframe(data, hide_index=True, use_container_width=True)
    
    with tab2:
        st.markdown("#### Classement des opérateurs")
        # Exemple de classement
        data = pd.DataFrame({
            "Opérateur": ["Op1", "Op2", "Op3", "Vous", "Op5"],
            "Rendement": [4.8, 4.6, 4.5, 4.2, 4.1]
        })
        st.dataframe(data, hide_index=True, use_container_width=True)

    st.stop()

# --------------------------
# 👨‍💼 TABLEAU DE BORD ADMIN
# --------------------------
# Section principale en 3 colonnes
st.markdown("### 📊 Aperçu global")

# Première ligne de métriques
cols = st.columns(4)
with cols[0]:
    metric_card("Rendement L1", "4.5 kg/h", "+0.2", "📈")
with cols[1]:
    metric_card("Rendement L2", "4.1 kg/h", "-0.1", "📉")
with cols[2]:
    metric_card("Productivité", "92%", icon="⚡")
with cols[3]:
    metric_card("Alertes", "3", icon="⚠️")

# Deuxième ligne avec graphiques
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Rendement par ligne")
    # Exemple de données
    data = pd.DataFrame({
        "Date": pd.date_range(start="2023-01-01", periods=7),
        "Ligne 1": np.random.normal(4.5, 0.2, 7),
        "Ligne 2": np.random.normal(4.1, 0.3, 7)
    })
    fig = px.line(data, x="Date", y=["Ligne 1", "Ligne 2"], 
                 template="plotly_white", height=300)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Répartition des performances")
    data = pd.DataFrame({
        "Performance": ["Excellente", "Bonne", "Moyenne", "Faible"],
        "Count": [15, 23, 12, 5]
    })
    fig = px.pie(data, values="Count", names="Performance", 
                height=300, hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

# Section de gestion
st.markdown("### 🛠️ Gestion")

tab1, tab2, tab3 = st.tabs(["Opérateurs", "Alertes", "Paramètres"])

with tab1:
    st.markdown("#### Liste des opérateurs")
    # Exemple de données
    data = pd.DataFrame({
        "ID": ["OP001", "OP002", "OP003"],
        "Nom": ["Alice", "Bob", "Charlie"],
        "Ligne": [1, 2, 1],
        "Rendement": [4.5, 4.2, 4.7]
    })
    st.dataframe(data, hide_index=True, use_container_width=True)

with tab2:
    st.markdown("#### Alertes récentes")
    alerts = [
        {"type": "Panne", "ligne": 1, "date": "10:30", "status": "Non résolue"},
        {"type": "Erreur", "ligne": 2, "date": "09:15", "status": "Résolue"},
        {"type": "Performance", "ligne": 1, "date": "Hier", "status": "En cours"}
    ]
    for alert in alerts:
        with st.container(border=True):
            cols = st.columns([1,3,2])
            with cols[0]:
                st.markdown(f"**{alert['type']}**")
            with cols[1]:
                st.markdown(f"Ligne {alert['ligne']} - {alert['date']}")
            with cols[2]:
                st.button("Détails", key=f"alert_{alert['type']}_{alert['date']}")

with tab3:
    if st.session_state.role in ["admin", "manager"]:
        with st.expander("🔧 Paramètres des seuils"):
            st.number_input("Seuil haut rendement (kg/h)", value=4.5)
            st.number_input("Seuil bas rendement (kg/h)", value=4.0)
            st.number_input("Seuil alertes", value=3)

# --------------------------
# 🎨 SIDEBAR MODERNE
# --------------------------
with st.sidebar:
    st.markdown(f"### {st.session_state.username}")
    st.markdown(f"*{st.session_state.role.capitalize()}*")
    st.divider()
    
    st.markdown("#### Navigation")
    if st.button("🏠 Accueil"):
        pass
    if st.button("📊 Tableau de bord"):
        pass
    if st.button("⚙️ Paramètres"):
        pass
    
    st.divider()
    
    if st.button("🚪 Déconnexion", type="primary"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()
