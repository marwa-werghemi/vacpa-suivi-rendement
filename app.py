import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from datetime import datetime, timedelta

# 🌿 Design & configuration de page
st.set_page_config(page_title="Suivi de rendement VACPA", layout="wide", page_icon="🌴")

# 🌿 Couleurs
VERT_FONCE = "#1b4332"
VERT_CLAIR = "#d8f3dc"
VERT_MOYEN = "#52b788"
ORANGE = "#f4a261"
ROUGE = "#e76f51"

# 🔐 Authentification simple
MOT_DE_PASSE = "vacpa2025"
if "connecte" not in st.session_state:
    st.session_state.connecte = False
if not st.session_state.connecte:
    st.markdown(f"<h2 style='color:{VERT_FONCE}'>🔐 Accès sécurisé</h2>", unsafe_allow_html=True)
    mdp = st.text_input("Entrez le mot de passe", type="password")
    if mdp == MOT_DE_PASSE:
        st.session_state.connecte = True
        st.success("✅ Accès autorisé")
    elif mdp:
        st.error("❌ Mot de passe incorrect")
    st.stop()

# 🔗 Supabase - Configuration
SUPABASE_URL = "https://pavndhlnvfwoygmatqys.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdm5kaGxudmZ3b3lnbWF0cXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYzMDYyNzIsImV4cCI6MjA2MTg4MjI3Mn0.xUMJfDZdjZkTzYdz0MgZ040IdT_cmeJSWIDZ74NGt1k"
TABLE = "rendements"
TABLE_PANNES = "pannes"  # Table pour signaler les pannes (à créer côté Supabase)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

@st.cache_data(ttl=60)
def charger_donnees():
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*", headers=headers)
    return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()

@st.cache_data(ttl=60)
def charger_pannes():
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_PANNES}?select=*", headers=headers)
    return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()

if st.button("🔄 Recharger les données"):
    st.cache_data.clear()

df = charger_donnees()
df_pannes = charger_pannes()

# 🏷️ Titre
st.markdown(f"<h1 style='color:{VERT_FONCE}'>🌴 Suivi du Rendement - VACPA</h1>", unsafe_allow_html=True)

if df.empty:
    st.warning("Aucune donnée disponible.")
    st.stop()

# Nettoyage & calculs
df["temps_min"] = pd.to_numeric(df["temps_min"], errors="coerce").fillna(0)
df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="coerce").fillna(0)
df["rendement"] = df["poids_kg"] / (df["temps_min"] / 60).replace(0, 1)
df["created_at"] = pd.to_datetime(df.get("created_at", pd.NaT), errors="coerce")

# 📅 Filtre par date
with st.expander("📅 Filtrer par date"):
    date_min = df["created_at"].min().date()
    date_max = df["created_at"].max().date()
    start_date, end_date = st.date_input("Plage de dates", [date_min, date_max])
    df = df[(df["created_at"].dt.date >= start_date) & (df["created_at"].dt.date <= end_date)]

# 🔑 Indicateurs Clés

# Simuler la séparation en 2 lignes (44 opératrices chacune)
# Suppose operatrice_id "op-1" à "op-44" ligne 1, "op-45" à "op-88" ligne 2
def ligne_operatrice(op_id):
    try:
        num = int(op_id.split('-')[1])
        return 1 if num <= 44 else 2
    except:
        return None

df["ligne"] = df["operatrice_id"].apply(ligne_operatrice)

# Rendement moyen par ligne
rendement_ligne = df.groupby("ligne")["rendement"].mean()

def couleur_rendement(val):
    if val > 85:
        return VERT_MOYEN
    elif val > 70:
        return ORANGE
    else:
        return ROUGE

# Taux de non-productivité par heure (1 - rendement réel / théorique)
# Hypothèse: rendement théorique = 100 kg/h (ajustable)
REND_THEORIQUE = 100
taux_non_prod = {}
for ligne in [1, 2]:
    r = rendement_ligne.get(ligne, 0)
    taux_non_prod[ligne] = max(0, 1 - (r / REND_THEORIQUE))

# % opératrices sous-performantes
SEUIL_RENDEMENT_MIN = 70  # kg/h seuil minimum
total_ops = df["operatrice_id"].nunique()
ops_sous_perf = df[df["rendement"] < SEUIL_RENDEMENT_MIN]["operatrice_id"].nunique()
pourcentage_sous_perf = 100 * ops_sous_perf / total_ops if total_ops > 0 else 0

# Variabilité rendement (écart-type) par ligne (sur la période filtrée)
ecart_type_ligne = df.groupby("ligne")["rendement"].std()

# Nombre de pannes signalées par ligne
if not df_pannes.empty:
    df_pannes["ligne"] = df_pannes["operatrice_id"].apply(ligne_operatrice)
    nb_pannes_par_ligne = df_pannes.groupby("ligne").size().to_dict()
else:
    nb_pannes_par_ligne = {1:0, 2:0}

# Temps moyen entre pannes (MTBF) par ligne
mtbf_ligne = {}
for ligne in [1, 2]:
    pannes_ligne = df_pannes[df_pannes["ligne"] == ligne].sort_values("date_heure")
    if len(pannes_ligne) > 1:
        deltas = pannes_ligne["date_heure"].diff().dropna()
        mtbf_ligne[ligne] = deltas.mean()
    else:
        mtbf_ligne[ligne] = None

# Ratio contrôleuse / opératrices (simulation erreur)
# Simulation simple : nombre d'erreurs (à ajouter dans df_pannes), nombre de plateaux contrôlés (à définir)
nombre_erreurs = len(df_pannes)  # supposition erreurs = pannes signalées
nombre_plateaux_controles = len(df)  # supposition 1 plateau par ligne
ratio_erreurs = nombre_erreurs / nombre_plateaux_controles if nombre_plateaux_controles > 0 else 0

# 🎨 Affichage des KPIs
st.subheader("🔑 Indicateurs clés recommandés")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Rendement moyen par ligne (kg/h)")
    for ligne, val in rendement_ligne.items():
        couleur = couleur_rendement(val*100)  # converti en %
        st.markdown(f"Ligne {ligne}: <span style='color:{couleur};font-weight:bold'>{val:.2f}</span>", unsafe_allow_html=True)

with col2:
    st.markdown("### Taux de non-productivité par heure")
    for ligne, val in taux_non_prod.items():
        couleur = ROUGE if val > 0.2 else VERT_MOYEN
        st.markdown(f"Ligne {ligne}: <span style='color:{couleur};font-weight:bold'>{val*100:.1f}%</span>", unsafe_allow_html=True)

col3, col4 = st.columns(2)
with col3:
    couleur_perf = ROUGE if pourcentage_sous_perf > 25 else (ORANGE if pourcentage_sous_perf > 10 else VERT_MOYEN)
    st.markdown(f"### % opératrices sous-performantes < {SEUIL_RENDEMENT_MIN} kg/h")
    st.markdown(f"<span style='color:{couleur_perf};font-weight:bold'>{pourcentage_sous_perf:.1f}%</span>", unsafe_allow_html=True)

with col4:
    st.markdown("### Variabilité du rendement (écart-type)")
    for ligne, val in ecart_type_ligne.items():
        couleur = ORANGE if val and val > 10 else VERT_MOYEN
        st.markdown(f"Ligne {ligne}: <span style='color:{couleur};font-weight:bold'>{val:.2f}</span>", unsafe_allow_html=True)

st.markdown("---")

st.subheader("⚠️ Alertes et suivi des pannes")

colp1, colp2 = st.columns(2)
with colp1:
    st.markdown("### Nombre de pannes signalées")
    for ligne, val in nb_pannes_par_ligne.items():
        couleur = ROUGE if val > 5 else VERT_MOYEN
        st.markdown(f"Ligne {ligne}: <span style='color:{couleur};font-weight:bold'>{val}</span>", unsafe_allow_html=True)

with colp2:
    st.markdown("### Temps moyen entre pannes (MTBF)")
    for ligne, val in mtbf_ligne.items():
        mtbf_text = f"{val}" if val is not None else "N/A"
        couleur = VERT_MOYEN if val and val > timedelta(hours=2) else ORANGE
        st.markdown(f"Ligne {ligne}: <span style='color:{couleur};font-weight:bold'>{mtbf_text}</span>", unsafe_allow_html=True)

st.markdown("---")

st.markdown("### Ratio erreurs / plateaux contrôlés")
couleur_ratio = ORANGE if ratio_erreurs > 0.05 else VERT_MOYEN
st.markdown(f"<span style='color:{couleur_ratio};font-weight:bold'>{ratio_erreurs:.2%}</span>", unsafe_allow_html=True)

# 📊 Graphiques

st.subheader("📊 Analyse graphique")

fig_rendement_ligne = px.box(df, x="ligne", y="rendement", color="ligne",
                             labels={"ligne":"Ligne", "rendement":"Rendement (kg/h)"},
                             title="Distribution du rendement par ligne")
st.plotly_chart(fig_rendement_ligne, use_container_width=True)

fig_pannes_timeline = None
if not df_pannes.empty:
    df_pannes["date_heure"] = pd.to_datetime(df_pannes.get("date_heure", pd.NaT))
    fig_pannes_timeline = px.histogram(df_pannes, x="date_heure", color="ligne",
                                       nbins=20, title="Historique des pannes")
    st.plotly_chart(fig_pannes_timeline, use_container_width=True)

# Formulaire simple pour ajout rendement (optionnel)
st.subheader("➕ Ajouter un nouveau rendement")

with st.form("form_ajout_rendement", clear_on_submit=True):
    operatrice_id = st.text_input("ID opératrice (ex: op-10)")
    temps_min = st.number_input("Temps en minutes", min_value=1)
    poids_kg = st.number_input("Poids (kg)", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Ajouter")

    if submitted:
        if operatrice_id and temps_min > 0 and poids_kg > 0:
            nouvelle_ligne = {
                "operatrice_id": operatrice_id,
                "temps_min": temps_min,
                "poids_kg": poids_kg,
                "created_at": datetime.now().isoformat()
            }
            response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE}",
                                     headers=headers,
                                     json=nouvelle_ligne)
            if response.status_code in [200, 201]:
                st.success("Rendement ajouté avec succès !")
                st.experimental_rerun()
            else:
                st.error(f"Erreur ajout données : {response.text}")
        else:
            st.error("Veuillez remplir tous les champs correctement.")


# ➖ Bouton de déconnexion
if st.button("🚪 Quitter l'application"):
    st.session_state.connecte = False
    st.rerun()
