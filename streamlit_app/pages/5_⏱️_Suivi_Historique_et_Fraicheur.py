"""Page 5 — Suivi historique et fraîcheur des offres."""

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_parquet

st.set_page_config(page_title="Page 5 — Suivi Historique", page_icon="⏱️", layout="wide")

# ==============================================================================
# 1. TITRE & DESCRIPTION
# ==============================================================================
st.title("⏱️ Page 5 — Suivi historique et fraîcheur des offres")
st.markdown("""
**Question métier :** *Quelles offres sont observées au fil des collectes et quelle est la durée de leur suivi dans l'historique ?*
Cette page décrit les premières et dernières observations des annonces. La présence dans une collecte ne prouve pas qu'une offre est encore en ligne ni qu'elle a été pourvue.
""")

# ==============================================================================
# 2. CHARGEMENT DES DONNÉES
# ==============================================================================
df_cycle = load_parquet("offres_historique_cycle.parquet")
df_nouvelles_j = load_parquet("nouvelles_offres_par_jour.parquet")
df_nouvelles_s = load_parquet("nouvelles_offres_par_semaine.parquet")
df_evolution_dim = load_parquet("offres_evolution_dimension.parquet")
df_fraicheur = load_parquet("fraicheur_offres.parquet")

# ==============================================================================
# 3. INSIGHTS CLÉS & FRAÎCHEUR
# ==============================================================================
st.subheader("💡 Insights clés & Cycle de Vie des Annonces")

c1, c2, c3, c4 = st.columns(4)
nb_total_snap = df_cycle["id"].nunique() if not df_cycle.empty and "id" in df_cycle.columns else 0
date_derniere_observation = pd.to_datetime(df_cycle["date_derniere_observation"], errors="coerce") if not df_cycle.empty and "date_derniere_observation" in df_cycle.columns else pd.Series(dtype="datetime64[ns]")
date_reference = date_derniere_observation.max() if not date_derniere_observation.empty else pd.NaT
jour_reference = date_reference.date() if pd.notna(date_reference) else None
nb_vues_dernier_jour = int(date_derniere_observation.dt.date.eq(jour_reference).sum()) if jour_reference is not None else 0
nb_nouvelles_dernier_jour = 0
if jour_reference is not None and not df_nouvelles_j.empty and "date_collecte" in df_nouvelles_j.columns:
    nouvelles_dates = pd.to_datetime(df_nouvelles_j["date_collecte"], errors="coerce").dt.date
    nouvelles_du_jour = df_nouvelles_j.loc[nouvelles_dates.eq(jour_reference), "nouvelles_offres"]
    nb_nouvelles_dernier_jour = int(nouvelles_du_jour.sum()) if not nouvelles_du_jour.empty else 0
duree_observation_mediane = df_cycle["duree_observation_jours"].median() if not df_cycle.empty and "duree_observation_jours" in df_cycle.columns else None
nb_dernier_lot = int(df_cycle["statut_observation"].eq("Active").sum()) if not df_cycle.empty and "statut_observation" in df_cycle.columns else 0
date_premiere_collecte = pd.to_datetime(df_fraicheur["premiere_collecte"].iloc[0], errors="coerce") if not df_fraicheur.empty and "premiere_collecte" in df_fraicheur.columns else pd.NaT
nombre_collectes = int(df_fraicheur["nombre_collectes"].iloc[0]) if not df_fraicheur.empty and "nombre_collectes" in df_fraicheur.columns else 0
nombre_snapshots = int(df_fraicheur["snapshots_collectes"].iloc[0]) if not df_fraicheur.empty and "snapshots_collectes" in df_fraicheur.columns else 0

if not df_cycle.empty and "statut_observation" in df_cycle.columns:
    df_cycle["statut_observation"] = df_cycle["statut_observation"].replace({"Active": "Présente au dernier lot", "Disparue": "Non revue au dernier lot"})

c1.metric("Offres distinctes observées", f"{nb_total_snap:,}")
c2.metric("Vues le dernier jour", f"{nb_vues_dernier_jour:,}", jour_reference.strftime("%d/%m/%Y") if jour_reference else "Date N/D")
c3.metric("Premières observations ce jour", f"{nb_nouvelles_dernier_jour:,}")
c4.metric("Médiane entre observations", f"{int(duree_observation_mediane)} jours" if duree_observation_mediane is not None else "N/D")
st.caption(f"Historique : {date_premiere_collecte.strftime('%d/%m/%Y') if pd.notna(date_premiere_collecte) else 'date inconnue'} au {date_reference.strftime('%d/%m/%Y') if pd.notna(date_reference) else 'date inconnue'} ; {nombre_collectes:,} horodatages de collecte, {nombre_snapshots:,} snapshots. {nb_dernier_lot:,} offres sont présentes dans le dernier lot exact : cela ne prouve pas qu'elles sont encore en ligne.")

with st.container():
    st.info(f"""
    📌 **Indicateurs de Fraîcheur & Tendance :**
    * **Dernier jour documenté** : **{nb_vues_dernier_jour:,} offres distinctes** ont été observées le {jour_reference.strftime('%d/%m/%Y') if jour_reference else 'dernier jour disponible'}, dont **{nb_nouvelles_dernier_jour:,} premières observations**.
    * **Durée de suivi** : la médiane entre première et dernière observation est de **{int(duree_observation_mediane)} jours** ; elle décrit la fenêtre de collecte, pas la durée réelle de publication ni un délai de pourvoi.
    * Le statut historique « présente au dernier lot » repose sur un horodatage précis. Les collectes de la même journée comportent plusieurs lots ; ne pas l'interpréter comme un état exhaustif de toutes les annonces en ligne.
    """)

# ==============================================================================
# 4. ONGLETS DE DÉTAILS
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Nouvelles Offres observées",
    "⏳ Fenêtre d'observation",
    "📊 Évolution par Dimension",
    "🔍 Table du Cycle de Vie des Offres",
])

with tab1:
    st.markdown("#### Dynamique d'apparition des nouvelles opportunités")
    if not df_nouvelles_j.empty and "date_collecte" in df_nouvelles_j.columns:
        fig_j = px.line(
            df_nouvelles_j,
            x="date_collecte",
            y="nouvelles_offres",
            title="Volume de nouvelles offres par jour de collecte",
            markers=True,
            line_shape="spline",
        )
        fig_j.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_j, use_container_width=True)
    elif not df_nouvelles_s.empty:
        fig_s = px.bar(df_nouvelles_s, x=df_nouvelles_s.columns[0], y=df_nouvelles_s.columns[1], title="Nouvelles offres par semaine")
        st.plotly_chart(fig_s, use_container_width=True)
    else:
        st.info("Données temporelles non disponibles.")

with tab2:
    st.markdown("#### Durée entre première et dernière observation (en jours)")
    if not df_cycle.empty and "duree_observation_jours" in df_cycle.columns:
        fig_hist = px.histogram(
            df_cycle,
            x="duree_observation_jours",
            nbins=30,
            color="statut_observation" if "statut_observation" in df_cycle.columns else None,
            title="Durée observée dans les collectes successives",
            labels={"duree_observation_jours": "Jours entre première et dernière observation"},
        )
        fig_hist.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_hist, use_container_width=True)

with tab3:
    st.markdown("#### Évolution selon les Dimensions (Contrats, Régions, Compétences)")
    if not df_evolution_dim.empty:
        st.dataframe(df_evolution_dim.head(100), use_container_width=True)
    else:
        st.info("Mart d'évolution par dimension non disponible.")

with tab4:
    st.markdown("#### Détail du cycle de vie des offres")
    if not df_cycle.empty:
        st.dataframe(df_cycle.head(100), use_container_width=True)
