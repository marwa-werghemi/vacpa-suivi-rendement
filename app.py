import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from datetime import datetime

# 🌿 Design & configuration de page
st.set_page_config(page_title="Suivi de rendement VACPA", layout="wide", page_icon="🌴🌴🌴")

# 🌿 Couleurs
VERT_FONCE = "#1b4332"
VERT_CLAIR = "#d8f3dc"
VERT_MOYEN = "#52b788"

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

if st.button("🔄 Recharger les données"):
    st.cache_data.clear()

df = charger_donnees()

# 🏷️ Titre
st.markdown(f"<h1 style='color:{VERT_FONCE}'>🌴 Suivi du Rendement - VACPA</h1>", unsafe_allow_html=True)

# 🌟 Statistiques globales
st.subheader("📊 Statistiques globales")
if not df.empty:
    df["temps_min"] = pd.to_numeric(df["temps_min"], errors="coerce").fillna(0)
    df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="coerce").fillna(0)
    df["rendement"] = df["poids_kg"] / (df["temps_min"] / 60).replace(0, 1)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total KG", f"{df['poids_kg'].sum():.2f} kg")
    col2.metric("Durée Totale", f"{df['temps_min'].sum():.0f} min")
    col3.metric("Rendement Moyen", f"{df['rendement'].mean():.2f} kg/h")
    col4.metric("Max Rendement", f"{df['rendement'].max():.2f} kg/h")
else:
    st.warning("Aucune donnée disponible.")

# 📅 Filtre par date
if "created_at" in df.columns:
    with st.expander("📅 Filtrer par date"):
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        date_min = df["created_at"].min().date()
        date_max = df["created_at"].max().date()
        start_date, end_date = st.date_input("Plage de dates", [date_min, date_max])
        df = df[(df["created_at"].dt.date >= start_date) & (df["created_at"].dt.date <= end_date)]

# ➕ Formulaire d'ajout
st.markdown(f"<h3 style='color:{VERT_MOYEN}'>🧺 Ajouter une Pesée</h3>", unsafe_allow_html=True)
with st.form("ajout_rendement", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        operatrice_id = st.text_input("ID opératrice", placeholder="op-1", key="operatrice_id")
    with col2:
        poids_kg = st.number_input("Poids (kg)", min_value=0.1, step=0.1, value=1.0)
    with col3:
        heures = st.number_input("Heures", min_value=0, value=0)
        minutes = st.number_input("Minutes", min_value=0, max_value=59, value=30)

    if st.form_submit_button("✅ Enregistrer"):
        if not operatrice_id or not operatrice_id.startswith('op-'):
            st.error("L'ID opératrice doit commencer par 'op-'")
        elif poids_kg <= 0:
            st.error("Le poids doit être supérieur à 0")
        elif heures == 0 and minutes == 0:
            st.error("La durée ne peut pas être 0")
        else:
            temps_total = heures * 60 + minutes
            nouveau = {
                "operatrice_id": operatrice_id.strip(),
                "poids_kg": float(poids_kg),
                "temps_min": int(temps_total),
                "date_heure": datetime.now().isoformat() + "Z"
            }
            try:
                r = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE}", headers=headers, json=nouveau)
                if r.status_code == 201:
                    st.success("✅ Enregistré avec succès!")
                    st.balloons()
                    st.cache_data.clear()
                else:
                    st.error(f"Erreur {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Erreur de connexion: {str(e)}")

# 📄 Données enregistrées
st.markdown(f"<h3 style='color:{VERT_MOYEN}'>📄 Données enregistrées</h3>", unsafe_allow_html=True)
if not df.empty:
    cols_to_show = ["operatrice_id", "date_heure", "poids_kg", "temps_min", "rendement", "created_at"]
    cols_to_show = [col for col in cols_to_show if col in df.columns]
    st.dataframe(df[cols_to_show])

    def exporter_excel(df_export):
        df_export = df_export.copy()
        for col in df_export.columns:
            if pd.api.types.is_datetime64_any_dtype(df_export[col]):
                df_export[col] = df_export[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                df_export[col] = df_export[col].astype(str)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Rendements')
        return buffer.getvalue()

    st.download_button(
        "⬇️ Télécharger en Excel",
        data=exporter_excel(df[cols_to_show].fillna('')),
        file_name="rendements.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 📊 Histogramme
    st.markdown(f"<h3 style='color:{VERT_MOYEN}'>📊 Répartition des performances par opératrice</h3>", unsafe_allow_html=True)
    fig_hist = px.histogram(
        df,
        x="operatrice_id",
        y="poids_kg",
        color="operatrice_id",
        title="Répartition du poids total par opératrice",
        labels={"operatrice_id": "Opératrice", "poids_kg": "Poids total (kg)"},
        height=500
    )
    fig_hist.update_layout(
        bargap=0.2,
        xaxis_title="Opératrice",
        yaxis_title="Poids total (kg)",
        showlegend=False
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # 🏆 Top 10
    st.markdown(f"<h3 style='color:{VERT_MOYEN}'>🏆 Top 10 des opératrices</h3>", unsafe_allow_html=True)
    top = df.groupby("operatrice_id").agg(
        poids_total=("poids_kg", "sum"),
        rendement_moyen=("rendement", "mean")
    ).sort_values("poids_total", ascending=False).head(10).reset_index()

    fig_top = px.bar(
        top,
        x="operatrice_id",
        y="poids_total",
        color="operatrice_id",
        text="poids_total",
        labels={"operatrice_id": "Opératrice", "poids_total": "Poids total (kg)"},
        title="Top 10 des opératrices par poids total"
    )
    fig_top.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_top.update_layout(showlegend=False, xaxis_title="Opératrice", yaxis_title="Poids total (kg)")
    st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info("Aucune donnée disponible à afficher.")
# ➖ Bouton de déconnexion
if st.button("🚪 Quitter l'application"):
    st.session_state.connecte = False
    st.rerun()
