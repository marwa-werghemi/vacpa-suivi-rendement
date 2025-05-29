import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# 🌿 Design & configuration de page
st.set_page_config(page_title="Suivi de rendement VACPA", layout="wide", page_icon="🌴🌴🌴")

# 🌿 Couleurs
VERT_FONCE = "#1b4332"
VERT_CLAIR = "#d8f3dc"
VERT_MOYEN = "#52b788"

# 🔐 Authentification améliorée avec username + password et rôles
CREDENTIALS = {
    "admin": {"password": "vacpa2025", "role": "admin"},
    "manager": {"password": "manager123", "role": "manager"},
    "operateur": {"password": "operateur456", "role": "operateur"},
    "marwa": {"password": "vacpa2025", "role": "operateur"}
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None

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
    if st.button("🚪 Déconnexion"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

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
        if 'ligne' not in df.columns:
            df['ligne'] = 1
        if 'numero_pesee' not in df.columns:
            df['numero_pesee'] = 1
        
        df["temps_min"] = pd.to_numeric(df["temps_min"], errors="coerce").fillna(0)
        df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="coerce").fillna(0)
        df["rendement"] = df["poids_kg"] / (df["temps_min"] / 60).replace(0, 1)
        
        df['date_heure'] = pd.to_datetime(df['date_heure'], errors='coerce')
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        return df
    return pd.DataFrame()

if st.button("🔄 Recharger les données"):
    st.cache_data.clear()

df = charger_donnees()

# 🏷️ Titre
st.markdown(f"<h1 style='color:{VERT_FONCE}'>🌴 Suivi du Rendement - VACPA</h1>", unsafe_allow_html=True)

# 🌟 Statistiques globales (visible par tous)
st.subheader("📊 Statistiques globales")
if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total KG", f"{df['poids_kg'].sum():.2f} kg")
    
    # Remplacement du temps total par le nombre max de pesées
    max_pesee = df['numero_pesee'].max()
    col2.metric("Nombre max de pesées", f"{max_pesee}")
    
    col3.metric("Rendement Moyen", f"{df['rendement'].mean():.2f} kg/h")
    col4.metric("Max Rendement", f"{df['rendement'].max():.2f} kg/h")
else:
    st.warning("Aucune donnée disponible.")

# 📅 Filtres (uniquement pour admin/manager)
if st.session_state.role in ["admin", "manager"]:
    with st.expander("🔍 Filtres"):
        if "created_at" in df.columns:
            date_min = df["created_at"].min().date() if not df.empty else datetime.today().date()
            date_max = df["created_at"].max().date() if not df.empty else datetime.today().date()
            start_date, end_date = st.date_input("Plage de dates", [date_min, date_max])
            df = df[(df["created_at"].dt.date >= start_date) & (df["created_at"].dt.date <= end_date)]
        
        if 'ligne' in df.columns:
            lignes = sorted(df['ligne'].unique())
            selected_lignes = st.multiselect("Lignes de production", options=lignes, default=lignes)
            df = df[df['ligne'].isin(selected_lignes)] if selected_lignes else df

# ➕ Formulaire d'ajout simplifié
with st.form("ajout_form", clear_on_submit=True):
    cols = st.columns([1,1,1,1])
    with cols[0]:
        ligne = st.number_input("Ligne", min_value=1, value=1)
        operatrice = st.text_input("ID Opératrice", "op-")
    with cols[1]:
        poids = st.number_input("Poids (kg)", min_value=0.1, value=1.0, step=0.1)
        numero_pesee = st.number_input("N° Pesée", min_value=1, value=1)
    with cols[2]:
        # Champ pour l'heure de la pesée
        heure_pesee = st.time_input("Heure de pesée", datetime.now().time())
    
    if st.form_submit_button("💾 Enregistrer"):
        # Création de la date complète avec l'heure de pesée
        date_pesee = datetime.combine(datetime.now().date(), heure_pesee)
        
        data = {
            "operatrice_id": operatrice,
            "poids_kg": poids,
            "temps_min": 0,  # On met 0 car ce champ n'est plus utilisé
            "ligne": ligne,
            "numero_pesee": numero_pesee,
            "date_heure": date_pesee.isoformat() + "Z"
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

# 📊 Visualisations selon le rôle
if not df.empty:
    if st.session_state.role == "operateur":
        st.markdown(f"<h3 style='color:{VERT_MOYEN}'>📋 Tableau des données</h3>", unsafe_allow_html=True)
        
        cols_to_show = ["ligne", "numero_pesee", "operatrice_id", "poids_kg", "date_heure", "rendement"]
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
        
        st.info("ℹ️ Vous avez un accès limité (opérateur). Seul l'affichage des données et le formulaire sont disponibles.")
    
    else:
        st.markdown(f"<h3 style='color:{VERT_MOYEN}'>📊 Analyses Visuelles</h3>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Tableau", "📈 Courbes", "📊 Histogrammes", "🏆 Top Performances"])
        
        with tab1:
            cols_to_show = ["ligne", "numero_pesee", "operatrice_id", "poids_kg", "date_heure", "rendement", "created_at"]
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
        
        with tab2:
            st.subheader("Évolution temporelle")
            df_clean = df.dropna(subset=['date_heure'])
            
            if not df_clean.empty:
                df_clean['date'] = df_clean['date_heure'].dt.date
                
                if all(col in df_clean.columns for col in ['date', 'operatrice_id', 'poids_kg']):
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
                        
                        if not df_filtered.empty:
                            fig_poids = px.line(
                                df_filtered,
                                x='date',
                                y='poids_kg',
                                color='operatrice_id',
                                title='Poids total par jour (kg)',
                                labels={'poids_kg': 'Poids (kg)', 'date': 'Date'},
                                markers=True
                            )
                            st.plotly_chart(fig_poids, use_container_width=True)
                            
                            fig_rendement = px.line(
                                df_filtered,
                                x='date',
                                y='rendement',
                                color='operatrice_id',
                                title='Rendement moyen par jour (kg/h)',
                                labels={'rendement': 'Rendement (kg/h)', 'date': 'Date'},
                                markers=True
                            )
                            st.plotly_chart(fig_rendement, use_container_width=True)
        
        with tab3:
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
                fig_heure = px.histogram(
                    df,
                    x=df['date_heure'].dt.hour,
                    nbins=24,
                    title="Distribution par heure de la journée",
                    labels={"date_heure": "Heure", "count": "Nombre de pesées"}
                )
                st.plotly_chart(fig_heure, use_container_width=True)
                
                fig_rendement = px.histogram(
                    df,
                    x="rendement",
                    nbins=20,
                    title="Distribution des rendements (kg/h)",
                    labels={"rendement": "Rendement (kg/h)", "count": "Fréquence"}
                )
                st.plotly_chart(fig_rendement, use_container_width=True)
        
        with tab4:
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
