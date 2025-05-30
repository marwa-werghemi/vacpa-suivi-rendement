import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    "manager": {"password": "manager123456789", "role": "manager"},
    "operateur": {"password": "operateur456789", "role": "operateur"},
    "marwa": {"password": "vacpa2025", "role": "operateur"}
}

# Seuils d'alerte
SEUILS = {
    "rendement": {"haut": 4.5, "moyen": 4.0},  # kg/h
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
            SEUILS["rendement"]["haut"] = st.number_input("Seuil haut rendement (kg/h)", value=4.5, step=0.1)
            SEUILS["rendement"]["moyen"] = st.number_input("Seuil moyen rendement (kg/h)", value=4.0, step=0.1)
            SEUILS["non_productivite"] = st.number_input("Seuil non-productivité (%)", value=20)
            SEUILS["sous_performance"] = st.number_input("Seuil sous-performance (%)", value=25)
            SEUILS["variabilite"] = st.number_input("Seuil variabilité (kg/h)", value=5.0, step=0.1)
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
        # Convertir les colonnes nécessaires
        df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="coerce").fillna(0)
        df["heure_travail"] = pd.to_numeric(df["heure_travail"], errors="coerce").fillna(5.0)
        df["rendement"] = df["poids_kg"] / df["heure_travail"]
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        dfs["rendement"] = df
    
    if r_pannes.status_code == 200:
        df_pannes = pd.DataFrame(r_pannes.json())
        if 'date_heure' in df_pannes.columns:
            df_pannes['date_heure'] = pd.to_datetime(df_pannes['date_heure'], errors='coerce')
        dfs["pannes"] = df_pannes
    
    if r_erreurs.status_code == 200:
        df_erreurs = pd.DataFrame(r_erreurs.json())
        if 'date_heure' in df_erreurs.columns:
            df_erreurs['date_heure'] = pd.to_datetime(df_erreurs['date_heure'], errors='coerce')
        dfs["erreurs"] = df_erreurs
    
    return dfs

def calculer_kpis(df_rendement, df_pannes, df_erreurs):
    kpis = {}
    
    if not df_rendement.empty:
        # Rendement moyen par ligne
        kpis["rendement_ligne1"] = df_rendement[df_rendement["ligne"] == 1]["rendement"].mean()
        kpis["rendement_ligne2"] = df_rendement[df_rendement["ligne"] == 2]["rendement"].mean()
        
        # Taux de non-productivité (basé sur le niveau de rendement)
        total_pesees = len(df_rendement)
        non_productives = len(df_rendement[df_rendement["niveau_rendement"].isin(["Faible", "Critique"])])
        kpis["non_productivite"] = (non_productives / total_pesees) * 100 if total_pesees > 0 else 0
        
        # % opératrices sous-performantes
        seuil_sous_perf = SEUILS["rendement"]["moyen"]
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
        alertes.append(f"⚠️ Rendement ligne 1 faible: {kpis['rendement_ligne1']:.1f} kg/h")
    
    if kpis.get("rendement_ligne2", 0) < SEUILS["rendement"]["moyen"]:
        alertes.append(f"⚠️ Rendement ligne 2 faible: {kpis['rendement_ligne2']:.1f} kg/h")
    
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

# 👷 Interface personnalisée pour les opérateurs
if st.session_state.role == "operateur":
    # Tableau de bord opérateur
    st.subheader(f"👋 Bienvenue {st.session_state.username}")
    
    # Statistiques personnelles
    if not df_rendement.empty:
        df_operateur = df_rendement[df_rendement['operatrice_id'] == st.session_state.username]
        
        if not df_operateur.empty:
            cols = st.columns(3)
            with cols[0]:
                st.metric("Votre rendement moyen", f"{df_operateur['rendement'].mean():.1f} kg/h")
            with cols[1]:
                st.metric("Total produit aujourd'hui", f"{df_operateur['poids_kg'].sum():.1f} kg")
            with cols[2]:
                st.metric("Nombre de pesées", len(df_operateur))
            
            # Graphique de performance personnelle
            if 'date' in df_operateur.columns:
                fig_perso = px.line(
                    df_operateur.sort_values('date'),
                    x='date',
                    y='rendement',
                    title='Votre performance au cours du temps',
                    markers=True
                )
                st.plotly_chart(fig_perso, use_container_width=True)
        else:
            st.info("Vous n'avez pas encore enregistré de pesée aujourd'hui.")
    
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
    
    with tab2:
        # Formulaire de signalement pour opérateurs
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
    
    with tab3:
        # Historique des actions de l'opérateur
        st.subheader("Vos dernières pesées")
        
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
        
        # Afficher aussi les problèmes signalés
        if not df_pannes.empty or not df_erreurs.empty:
            st.subheader("Vos signalements")
            
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

    st.stop()  # On arrête ici pour les opérateurs

# 🌟 Tableau de bord des KPI (pour admin/manager)
# 🌟 Tableau de bord simplifié
st.subheader("🏆 Classement des opératrices par rendement")

if not df_rendement.empty and 'operatrice_id' in df_rendement.columns:
    # Calcul du rendement moyen par opératrice
    perf_operatrices = df_rendement.groupby('operatrice_id')['rendement'].mean().reset_index()
    perf_operatrices = perf_operatrices.sort_values('rendement', ascending=False)
    
    # Prendre les top 10
    top10 = perf_operatrices.head(10)
    
    # Création du graphique simple
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=top10['operatrice_id'],
        x=top10['rendement'],
        orientation='h',
        marker_color=VERT_FONCE,
        text=top10['rendement'].round(2),
        textposition='auto'
    ))
    
    fig.update_layout(
        height=500,
        xaxis_title="Rendement moyen (kg/h)",
        yaxis_title="ID Opératrice",
        yaxis={'categoryorder':'total ascending'},
        margin=dict(l=100, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Affichage tableau simple
    st.write("### Détails des performances")
    st.dataframe(
        top10.rename(columns={
            'operatrice_id': 'Opératrice',
            'rendement': 'Rendement (kg/h)'
        }),
        hide_index=True,
        use_container_width=True
    )
else:
    st.warning("Aucune donnée disponible pour le classement")
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
        st.metric("Rendement Ligne 1", f"{kpis['rendement_ligne1']:.1f} kg/h", delta=None, 
                 help="Performance moyenne des opératrices de la ligne 1", 
                 label_visibility="visible")
        st.markdown(f"<div style='height: 5px; background-color: {color_l1};'></div>", unsafe_allow_html=True)
    
    with cols[1]:
        color_l2 = get_color(kpis["rendement_ligne2"], SEUILS["rendement"]["haut"], SEUILS["rendement"]["moyen"], inverse=True)
        st.metric("Rendement Ligne 2", f"{kpis['rendement_ligne2']:.1f} kg/h", delta=None,
                 help="Performance moyenne des opératrices de la ligne 2",
                 label_visibility="visible")
        st.markdown(f"<div style='height: 5px; background-color: {color_l2};'></div>", unsafe_allow_html=True)
    
    with cols[2]:
        color_np = get_color(kpis["non_productivite"], SEUILS["non_productivite"], SEUILS["non_productivite"]*0.7)
        st.metric("Temps non-productif", f"{kpis['non_productivite']:.1f}%", delta=None,
                 help="% de pesées avec rendement faible ou critique",
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

    # 🌟 Statistiques globales (visible par tous)
    st.subheader("📊 Statistiques globales")
    if not df_rendement.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total KG", f"{df_rendement['poids_kg'].sum():.2f} kg")
        
        # Nombre max de pesées
        max_pesee = df_rendement['numero_pesee'].max()
        col2.metric("Nombre max de pesées", f"{max_pesee}")
        
        col3.metric("Rendement Moyen", f"{df_rendement['rendement'].mean():.2f} kg/h")
        col4.metric("Max Rendement", f"{df_rendement['rendement'].max():.2f} kg/h")
    else:
        st.warning("Aucune donnée disponible.")

    # 📊 Visualisations
    st.subheader("📈 Analyses visuelles")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Rendements", "Heatmap", "Pannes/Erreurs", "Historique"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Courbe de rendement par ligne
            if 'date' in df_rendement.columns:
                df_rendement['jour'] = df_rendement['date'].dt.date
                df_rend_jour = df_rendement.groupby(['jour', 'ligne'])['rendement'].mean().reset_index()
                
                fig_rendement = px.line(
                    df_rend_jour,
                    x='jour',
                    y='rendement',
                    color='ligne',
                    title='Rendement moyen par jour',
                    labels={'jour': 'Date', 'rendement': 'Rendement (kg/h)'},
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
                if not df_pannes.empty and 'date_heure' in df_pannes.columns:
                    # Graphique des pannes
                    df_pannes['jour'] = df_pannes['date_heure'].dt.date
                    pannes_par_jour = df_pannes.groupby('jour').size().reset_index(name='count')
                    
                    fig_pannes = px.bar(
                        pannes_par_jour,
                        x='jour',
                        y='count',
                        title='Pannes par jour',
                        labels={'jour': 'Date', 'count': 'Nombre de pannes'}
                    )
                    st.plotly_chart(fig_pannes, use_container_width=True)
            
            with col2:
                if not df_erreurs.empty and 'date_heure' in df_erreurs.columns:
                    # Graphique des erreurs
                    df_erreurs['jour'] = df_erreurs['date_heure'].dt.date
                    erreurs_par_jour = df_erreurs.groupby('jour').size().reset_index(name='count')
                    
                    fig_erreurs = px.bar(
                        erreurs_par_jour,
                        x='jour',
                        y='count',
                        title='Erreurs par jour',
                        labels={'jour': 'Date', 'count': 'Nombre d\'erreurs'}
                    )
                    st.plotly_chart(fig_erreurs, use_container_width=True)
        else:
            st.info("Aucune donnée de pannes ou d'erreurs disponible")
    
    with tab4:
        # Historique des alertes
        st.dataframe(pd.DataFrame(st.session_state.alertes, columns=["Alertes"]), height=300)

    # 📝 Formulaire de signalement
    if st.session_state.role in ["admin", "manager"]:
        with st.expander("📝 Signaler un problème"):
            with st.form("probleme_form"):
                type_probleme = st.selectbox("Type de problème", ["Panne", "Erreur", "Autre"])
                ligne = st.selectbox("Ligne concernée", [1, 2])
                description = st.text_area("Description")
                
                if st.form_submit_button("Envoyer"):
                    table = TABLE_PANNES if type_probleme == "Panne" else TABLE_ERREURS
                    data = {
                        "ligne": ligne,
                        "description": description,
                        "date_heure": datetime.now().isoformat() + "Z",
                        "operatrice_id": st.session_state.username,
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

    # ℹ️ Aide et légende
    with st.expander("ℹ️ Aide et légende"):
        st.markdown("""
        **Légende des couleurs :**
        - 🟢 Vert : Bonne performance (au-dessus du seuil haut)
        - 🟠 Orange : Performance moyenne (entre les seuils)
        - 🔴 Rouge : Performance faible (en dessous du seuil bas)
        
        **Seuils par défaut :**
        - Rendement : >4.5 kg/h 🟢 | 4.0-4.5 kg/h 🟠 | <4.0 kg/h 🔴
        - Non-productivité : >20% 🔴
        - Sous-performance : >25% 🔴
        - Variabilité : >5 kg/h 🔴
        - Pannes : >3 🔴
        - Erreurs : >10% 🔴
        
        **Modifier les seuils** dans le menu latéral (admin/manager uniquement)
        """)

else:
    st.info("Aucune donnée de rendement disponible à afficher.")

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
                    "rendement": rendement,
                    "niveau_rendement": niveau_rendement
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
