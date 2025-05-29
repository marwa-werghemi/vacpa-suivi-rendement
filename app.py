import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from datetime import datetime, timedelta

# 🌿 Design & configuration de page
st.set_page_config(page_title="Suivi de rendement VACPA", layout="wide", page_icon="🌴🌴🌴")

# 🌿 Couleurs
VERT_FONCE = "#1b4332"
VERT_CLAIR = "#d8f3dc"
VERT_MOYEN = "#52b788"
ORANGE = "#f77f00"
ROUGE = "#d62828"

# 🔐 Authentification améliorée avec username + password et rôles
CREDENTIALS = {
    "admin": {"password": "vacpa2025", "role": "admin"},
    "manager": {"password": "manager123", "role": "manager"},
    "operateur": {"password": "operateur456", "role": "operateur"},
    "marwa": {"password": "vacpa2025", "role": "operateur"}
}

# Seuils d'alerte
SEUILS = {
    "rendement": {"haut": 85, "moyen": 70},
    "non_productivite": 20,
    "sous_performance": 25,
    "variabilite": 5,  # kg/h (écart-type)
    "pannes": 3,
    "erreurs": 10  # %
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.alertes = []

if not st.session_state.authenticated:
    st.markdown(f"<h2 style='color:{VERT_FONCE}'>🔐 Connexion sécurisée</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Nom d'utilisateur")
    with col2:
        password = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        if username in CREDENTIALS and CREDENTIALS[username]["password"] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = CREDENTIALS[username]["role"]
            st.success(f"✅ Connecté en tant que {username} ({st.session_state.role})")
            st.rerun()
        else:
            st.error("❌ Identifiants incorrects")
    st.stop()

# Afficher le nom d'utilisateur connecté dans la sidebar
with st.sidebar:
    st.markdown(f"**Connecté en tant que :** `{st.session_state.username}`")
    st.markdown(f"**Rôle :** `{st.session_state.role}`")
    
    if st.session_state.role in ["admin", "manager"]:
        with st.expander("⚙️ Paramètres des alertes"):
            SEUILS["rendement"]["haut"] = st.number_input("Seuil haut rendement (%)", value=85)
            SEUILS["rendement"]["moyen"] = st.number_input("Seuil moyen rendement (%)", value=70)
            SEUILS["non_productivite"] = st.number_input("Seuil non-productivité (%)", value=20)
            SEUILS["sous_performance"] = st.number_input("Seuil sous-performance (%)", value=25)
            SEUILS["variabilite"] = st.number_input("Seuil variabilité (kg/h)", value=5.0)
            SEUILS["pannes"] = st.number_input("Seuil alertes pannes", value=3)
            SEUILS["erreurs"] = st.number_input("Seuil erreurs (%)", value=10)
    
    if st.button("🚪 Déconnexion"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

# 🔗 Supabase - Configuration
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

@st.cache_data(ttl=60)
def charger_donnees():
    # Charger les données de rendement
    r_rendement = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_RENDEMENT}?select=*", headers=headers)
    r_pannes = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_PANNES}?select=*", headers=headers)
    r_erreurs = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_ERREURS}?select=*", headers=headers)
    
    dfs = {}
    
    if r_rendement.status_code == 200:
        df = pd.DataFrame(r_rendement.json())
        if 'ligne' not in df.columns:
            df['ligne'] = 1
        if 'numero_pesee' not in df.columns:
            df['numero_pesee'] = 1
        
        df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="coerce").fillna(0)
        df["rendement"] = df["poids_kg"]  # Simplifié pour cet exemple
        
        df['date_heure'] = pd.to_datetime(df['date_heure'], errors='coerce')
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        dfs["rendement"] = df
    
    if r_pannes.status_code == 200:
        df_pannes = pd.DataFrame(r_pannes.json())
        df_pannes['date_heure'] = pd.to_datetime(df_pannes['date_heure'], errors='coerce')
        dfs["pannes"] = df_pannes
    
    if r_erreurs.status_code == 200:
        df_erreurs = pd.DataFrame(r_erreurs.json())
        df_erreurs['date_heure'] = pd.to_datetime(df_erreurs['date_heure'], errors='coerce')
        dfs["erreurs"] = df_erreurs
    
    return dfs

def calculer_kpis(df_rendement, df_pannes, df_erreurs):
    kpis = {}
    
    if not df_rendement.empty:
        # Rendement moyen par ligne
        kpis["rendement_ligne1"] = df_rendement[df_rendement["ligne"] == 1]["rendement"].mean()
        kpis["rendement_ligne2"] = df_rendement[df_rendement["ligne"] == 2]["rendement"].mean()
        
        # Taux de non-productivité
        kpis["non_productivite"] = (1 - (df_rendement["rendement"].mean() / 100)) * 100  # Exemple
        
        # % opératrices sous-performantes
        seuil_sous_perf = 50  # Exemple
        total_operatrices = df_rendement["operatrice_id"].nunique()
        sous_perf = df_rendement[df_rendement["rendement"] < seuil_sous_perf]["operatrice_id"].nunique()
        kpis["sous_performance"] = (sous_perf / total_operatrices) * 100 if total_operatrices > 0 else 0
        
        # Variabilité du rendement
        kpis["variabilite"] = df_rendement["rendement"].std()
    
    if not df_pannes.empty:
        # Nombre de pannes
        kpis["nb_pannes"] = len(df_pannes)
        
        # MTBF
        if len(df_pannes) > 1:
            deltas = df_pannes["date_heure"].sort_values().diff().dt.total_seconds() / 60
            kpis["mtbf"] = deltas.mean()
    
    if not df_erreurs.empty:
        # Ratio erreurs
        kpis["ratio_erreurs"] = (len(df_erreurs) / len(df_rendement)) * 100 if not df_rendement.empty else 0
    
    # Score global
    kpis["score_global"] = min(100, max(0, 100 - (
        max(0, kpis.get("non_productivite", 0) - SEUILS["non_productivite"]) + 
        max(0, kpis.get("sous_performance", 0) - SEUILS["sous_performance"]) +
        max(0, kpis.get("variabilite", 0) - SEUILS["variabilite"]) * 2 +
        max(0, kpis.get("nb_pannes", 0) - SEUILS["pannes"]) * 5 +
        max(0, kpis.get("ratio_erreurs", 0) - SEUILS["erreurs"]) )))
    return kpis

def get_color(value, seuil_haut, seuil_moyen, inverse=False):
    if inverse:
        if value >= seuil_haut: return VERT_FONCE
        if value >= seuil_moyen: return ORANGE
        return ROUGE
    else:
        if value >= seuil_haut: return ROUGE
        if value >= seuil_moyen: return ORANGE
        return VERT_FONCE

def check_alertes(kpis):
    alertes = []
    
    # Vérifier chaque KPI pour générer des alertes
    if kpis.get("rendement_ligne1", 0) < SEUILS["rendement"]["moyen"]:
        alertes.append(f"⚠️ Rendement ligne 1 faible: {kpis['rendement_ligne1']:.1f}%")
    
    if kpis.get("rendement_ligne2", 0) < SEUILS["rendement"]["moyen"]:
        alertes.append(f"⚠️ Rendement ligne 2 faible: {kpis['rendement_ligne2']:.1f}%")
    
    if kpis.get("non_productivite", 0) > SEUILS["non_productivite"]:
        alertes.append(f"🚨 Taux de non-productivité élevé: {kpis['non_productivite']:.1f}%")
    
    if kpis.get("sous_performance", 0) > SEUILS["sous_performance"]:
        alertes.append(f"👎 % opératrices sous-performantes: {kpis['sous_performance']:.1f}%")
    
    if kpis.get("variabilite", 0) > SEUILS["variabilite"]:
        alertes.append(f"📊 Variabilité du rendement élevée: {kpis['variabilite']:.1f} kg/h")
    
    if kpis.get("nb_pannes", 0) >= SEUILS["pannes"]:
        alertes.append(f"🔧 Nombre de pannes signalées: {kpis['nb_pannes']}")
    
    if kpis.get("ratio_erreurs", 0) > SEUILS["erreurs"]:
        alertes.append(f"❌ Ratio erreurs élevé: {kpis['ratio_erreurs']:.1f}%")
    
    return alertes

if st.button("🔄 Recharger les données"):
    st.cache_data.clear()

data = charger_donnees()
df_rendement = data.get("rendement", pd.DataFrame())
df_pannes = data.get("pannes", pd.DataFrame())
df_erreurs = data.get("erreurs", pd.DataFrame())

kpis = calculer_kpis(df_rendement, df_pannes, df_erreurs)
nouvelles_alertes = check_alertes(kpis)

# Ajouter les nouvelles alertes à l'historique
for alerte in nouvelles_alertes:
    if alerte not in st.session_state.alertes:
        st.session_state.alertes.append(alerte)
        st.toast(alerte, icon="⚠️")

# 🏷️ Titre
st.markdown(f"<h1 style='color:{VERT_FONCE}'>🌴 Suivi du Rendement - VACPA</h1>", unsafe_allow_html=True)

# 🔔 Alertes en cours
if st.session_state.alertes:
    with st.expander(f"🔴 Alertes en cours ({len(st.session_state.alertes)})", expanded=True):
        for alerte in st.session_state.alertes:
            st.warning(alerte)
        
        if st.button("Effacer les alertes"):
            st.session_state.alertes = []
            st.rerun()

# 🌟 Tableau de bord des KPI
st.subheader("📊 Tableau de bord des indicateurs")

if not df_rendement.empty:
    # Score global
    col_score = st.columns([1, 3, 1])
    with col_score[1]:
        score_color = get_color(kpis["score_global"], 80, 50, inverse=True)
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border-radius: 10px; background-color: {score_color}; color: white;">
            <h2>Score global de l'atelier</h2>
            <h1>{kpis["score_global"]:.0f}/100</h1>
        </div>
        """, unsafe_allow_html=True)
    
    # KPI principaux
    cols = st.columns(4)
    
    with cols[0]:
        color_l1 = get_color(kpis["rendement_ligne1"], SEUILS["rendement"]["haut"], SEUILS["rendement"]["moyen"], inverse=True)
        st.metric("Rendement Ligne 1", f"{kpis['rendement_ligne1']:.1f}%", delta=None, 
                 help="Performance moyenne des opératrices de la ligne 1", 
                 label_visibility="visible")
        st.markdown(f"<div style='height: 5px; background-color: {color_l1};'></div>", unsafe_allow_html=True)
    
    with cols[1]:
        color_l2 = get_color(kpis["rendement_ligne2"], SEUILS["rendement"]["haut"], SEUILS["rendement"]["moyen"], inverse=True)
        st.metric("Rendement Ligne 2", f"{kpis['rendement_ligne2']:.1f}%", delta=None,
                 help="Performance moyenne des opératrices de la ligne 2",
                 label_visibility="visible")
        st.markdown(f"<div style='height: 5px; background-color: {color_l2};'></div>", unsafe_allow_html=True)
    
    with cols[2]:
        color_np = get_color(kpis["non_productivite"], SEUILS["non_productivite"], SEUILS["non_productivite"]*0.7)
        st.metric("Temps non-productif", f"{kpis['non_productivite']:.1f}%", delta=None,
                 help="% de temps sans production (problèmes, lenteurs)",
                 label_visibility="visible")
        st.markdown(f"<div style='height: 5px; background-color: {color_np};'></div>", unsafe_allow_html=True)
    
    with cols[3]:
        color_sp = get_color(kpis["sous_performance"], SEUILS["sous_performance"], SEUILS["sous_performance"]*0.7)
        st.metric("Opératrices sous-perf.", f"{kpis['sous_performance']:.1f}%", delta=None,
                 help="% d'opératrices en dessous du seuil de performance",
                 label_visibility="visible")
        st.markdown(f"<div style='height: 5px; background-color: {color_sp};'></div>", unsafe_allow_html=True)
    
    # Deuxième ligne de KPI
    cols2 = st.columns(4)
    
    with cols2[0]:
        color_var = get_color(kpis["variabilite"], SEUILS["variabilite"], SEUILS["variabilite"]*0.7)
        st.metric("Variabilité rendement", f"{kpis['variabilite']:.1f} kg/h", delta=None,
                 help="Écart-type des rendements individuels",
                 label_visibility="visible")
        st.markdown(f"<div style='height: 5px; background-color: {color_var};'></div>", unsafe_allow_html=True)
    
    with cols2[1]:
        color_pan = get_color(kpis["nb_pannes"], SEUILS["pannes"], SEUILS["pannes"]*0.7)
        st.metric("Pannes signalées", kpis["nb_pannes"], delta=None,
                 help="Nombre de pannes signalées aujourd'hui",
                 label_visibility="visible")
        st.markdown(f"<div style='height: 5px; background-color: {color_pan};'></div>", unsafe_allow_html=True)
    
    with cols2[2]:
        if "mtbf" in kpis:
            st.metric("MTBF", f"{kpis['mtbf']:.1f} min", delta=None,
                     help="Temps moyen entre pannes",
                     label_visibility="visible")
        else:
            st.metric("MTBF", "N/A", delta=None,
                     help="Temps moyen entre pannes (pas assez de données)",
                     label_visibility="visible")
    
    with cols2[3]:
        color_err = get_color(kpis["ratio_erreurs"], SEUILS["erreurs"], SEUILS["erreurs"]*0.7)
        st.metric("Taux d'erreurs", f"{kpis['ratio_erreurs']:.1f}%", delta=None,
                 help="% de plateaux avec erreurs détectées",
                 label_visibility="visible")
        st.markdown(f"<div style='height: 5px; background-color: {color_err};'></div>", unsafe_allow_html=True)

    # 📊 Visualisations
    st.subheader("📈 Analyses visuelles")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Rendements", "Heatmap", "Pannes/Erreurs", "Historique"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Courbe de rendement par ligne
            df_rendement['heure'] = df_rendement['date_heure'].dt.hour
            df_rend_heure = df_rendement.groupby(['heure', 'ligne'])['rendement'].mean().reset_index()
            
            fig_rendement = px.line(
                df_rend_heure,
                x='heure',
                y='rendement',
                color='ligne',
                title='Rendement moyen par heure',
                labels={'heure': 'Heure', 'rendement': 'Rendement (kg/h)'},
                markers=True
            )
            st.plotly_chart(fig_rendement, use_container_width=True)
        
        with col2:
            # Distribution des rendements
            fig_distrib = px.histogram(
                df_rendement,
                x='rendement',
                color='ligne',
                nbins=20,
                title='Distribution des rendements par ligne',
                labels={'rendement': 'Rendement (kg/h)'},
                barmode='overlay'
            )
            st.plotly_chart(fig_distrib, use_container_width=True)
    
    with tab2:
        # Heatmap des performances
        df_heatmap = df_rendement.pivot_table(
            index='operatrice_id',
            columns='ligne',
            values='rendement',
            aggfunc='mean'
        ).reset_index()
        
        fig_heatmap = px.imshow(
            df_heatmap.set_index('operatrice_id'),
            labels=dict(x="Ligne", y="Opératrice", color="Rendement"),
            title="Heatmap des performances par opératrice",
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with tab3:
        if not df_pannes.empty or not df_erreurs.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                if not df_pannes.empty:
                    # Graphique des pannes
                    df_pannes['heure'] = df_pannes['date_heure'].dt.hour
                    pannes_par_heure = df_pannes.groupby('heure').size().reset_index(name='count')
                    
                    fig_pannes = px.bar(
                        pannes_par_heure,
                        x='heure',
                        y='count',
                        title='Pannes par heure',
                        labels={'heure': 'Heure', 'count': 'Nombre de pannes'}
                    )
                    st.plotly_chart(fig_pannes, use_container_width=True)
            
            with col2:
                if not df_erreurs.empty:
                    # Graphique des erreurs
                    df_erreurs['heure'] = df_erreurs['date_heure'].dt.hour
                    erreurs_par_heure = df_erreurs.groupby('heure').size().reset_index(name='count')
                    
                    fig_erreurs = px.bar(
                        erreurs_par_heure,
                        x='heure',
                        y='count',
                        title='Erreurs par heure',
                        labels={'heure': 'Heure', 'count': 'Nombre d\'erreurs'}
                    )
                    st.plotly_chart(fig_erreurs, use_container_width=True)
        else:
            st.info("Aucune donnée de pannes ou d'erreurs disponible")
    
    with tab4:
        # Historique des alertes
        st.dataframe(pd.DataFrame(st.session_state.alertes, columns=["Alertes"]), height=300)

    # 📝 Formulaire de signalement
    if st.session_state.role in ["admin", "manager", "operateur"]:
        with st.expander("📝 Signaler un problème"):
            with st.form("probleme_form"):
                type_probleme = st.selectbox("Type de problème", ["Panne", "Erreur", "Autre"])
                ligne = st.selectbox("Ligne concernée", [1, 2])
                description = st.text_area("Description")
                
                if st.form_submit_button("Envoyer"):
                    table = TABLE_PANNES if type_probleme == "Panne" else TABLE_ERREURS
                    data = {
                        "type": type_probleme,
                        "ligne": ligne,
                        "description": description,
                        "date_heure": datetime.now().isoformat() + "Z",
                        "operateur": st.session_state.username
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

    # ℹ️ Aide et légende
    with st.expander("ℹ️ Aide et légende"):
        st.markdown("""
        **Légende des couleurs :**
        - 🟢 Vert : Bonne performance (au-dessus du seuil haut)
        - 🟠 Orange : Performance moyenne (entre les seuils)
        - 🔴 Rouge : Performance faible (en dessous du seuil bas)
        
        **Seuils par défaut :**
        - Rendement : >85% 🟢 | 70-85% 🟠 | <70% 🔴
        - Non-productivité : >20% 🔴
        - Sous-performance : >25% 🔴
        - Variabilité : >5 kg/h 🔴
        - Pannes : >3 🔴
        - Erreurs : >10% 🔴
        
        **Modifier les seuils** dans le menu latéral (admin/manager uniquement)
        """)

else:
    st.info("Aucune donnée de rendement disponible à afficher.")
