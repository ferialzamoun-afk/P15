"""Page 1 — Synthèse décisionnelle."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_parquet

st.set_page_config(page_title="Page 1 — Synthèse décisionnelle", page_icon="🎯", layout="wide")

# ==============================================================================
# 1. TITRE & DESCRIPTION
# ==============================================================================
st.title("🎯 Page 1 — Synthèse décisionnelle")
st.markdown("""
**Question métier :** *Où se situe le volume d'offres Data & IA et quels signaux de tension ou limites de couverture méritent une analyse approfondie ?*
Cette page offre une vision exécutive consolidée confrontant les offres réelles collectées (France Travail), les besoins prévisionnels déclarés (Enquête BMO) et la qualité du mapping des certifications.
""")

# ==============================================================================
# 2. CHARGEMENT DES DONNÉES
# ==============================================================================
df_kpi_global = load_parquet("kpi_global.parquet")
df_kpi_rome = load_parquet("kpi_by_rome.parquet")
df_kpi_region = load_parquet("kpi_by_region.parquet")
df_tension = load_parquet("tension_data.parquet")
df_offres_bmo = load_parquet("offres_vs_bmo_region.parquet")
df_offres = load_parquet("fact_offres.parquet")

# ==============================================================================
# 3. BARRE LATÉRALE - FILTRES
# ==============================================================================
st.sidebar.markdown("### 🏛️ Sources de Données")
st.sidebar.markdown("""
* **France Travail** *(Offres d'emploi)*
* **Enquête BMO 2026** *(Besoins déclarés)*
* **France Compétences** *(Référentiel RNCP)*
""")
st.sidebar.divider()
st.sidebar.markdown("### 🔍 Filtres Synthèse")

regions_dispo = ["Toutes"] + sorted(df_offres["region"].dropna().unique().tolist()) if not df_offres.empty and "region" in df_offres.columns else ["Toutes"]
sel_region = st.sidebar.selectbox("Filtrer par Région", regions_dispo)

# Application filtre région si sélectionné
df_offres_plot = df_offres.copy() if not df_offres.empty else pd.DataFrame()
if sel_region != "Toutes" and not df_offres_plot.empty and "region" in df_offres_plot.columns:
    df_offres_plot = df_offres_plot[df_offres_plot["region"] == sel_region]

# ==============================================================================
# 4. INSIGHTS CLÉS & INDICATEURS STRATÉGIQUES
# ==============================================================================
st.subheader("💡 Insights clés & Indicateurs Stratégiques")

col1, col2, col3, col4 = st.columns(4)

nb_total_offres = len(df_offres_plot) if not df_offres_plot.empty else (int(df_kpi_global["nombre_offres"].iloc[0]) if not df_kpi_global.empty else 0)
taux_couverture = float(df_kpi_global["couverture_certifications_pct"].iloc[0]) if not df_kpi_global.empty and "couverture_certifications_pct" in df_kpi_global.columns else 36.9
nb_codes_rome = int(df_kpi_global["nombre_codes_rome"].iloc[0]) if not df_kpi_global.empty and "nombre_codes_rome" in df_kpi_global.columns else (df_offres["romeCode"].nunique() if not df_offres.empty else 0)
nb_regions = int(df_kpi_global["nombre_regions"].iloc[0]) if not df_kpi_global.empty and "nombre_regions" in df_kpi_global.columns else (df_offres["region"].nunique() if not df_offres.empty else 0)
nb_offres_global = int(df_kpi_global["nombre_offres"].iloc[0]) if not df_kpi_global.empty and "nombre_offres" in df_kpi_global.columns else 0
date_col = str(df_kpi_global["derniere_collecte"].iloc[0])[:10] if not df_kpi_global.empty and "derniere_collecte" in df_kpi_global.columns else "inconnue"
part_top_regions = 0.0
if not df_offres.empty and {"id", "region"}.issubset(df_offres.columns):
    nb_ids_global = df_offres["id"].nunique()
    if nb_ids_global:
        nb_ids_top_regions = df_offres.loc[
            df_offres["region"].isin(["Ile-de-France", "Auvergne-Rhône-Alpes"]), "id"
        ].nunique()
        part_top_regions = 100.0 * nb_ids_top_regions / nb_ids_global

col1.metric("Volume Total d'Offres", f"{nb_total_offres:,}")
col2.metric("Couverture Certifications", f"{taux_couverture:.1f} %", delta="Cible > 80 %")
col3.metric("Métiers ROME Détectés", f"{nb_codes_rome} codes distincts")
col4.metric("Régions avec Offres", f"{nb_regions}")

with st.container():
    st.info(f"""
    📌 **Constats majeurs :**
    * **Comparaison des extractions** : le snapshot du 2026-08-31 comptait **1,047 offres** et **36.9 %** de couverture RNCP. Au **{date_col}**, le mart courant compte **{nb_offres_global:,} offres** et **{taux_couverture:.1f} %** ({nb_offres_global - 1047:+,} offres ; {taux_couverture - 36.9:+.1f} points).
    * **Lecture prudente** : les dates et périmètres d'extraction diffèrent ; cet écart ne mesure pas à lui seul une croissance du marché.
    * **Concentration territoriale** : l'Île-de-France et Auvergne-Rhône-Alpes représentent **{part_top_regions:.1f} %** des offres du mart courant.
    * **Offres vs BMO** : les intentions BMO dépassent les offres publiées pour certains métiers ; les populations et temporalités diffèrent, ce qui ne suffit pas à conclure à un marché caché.
    * **Alerte Qualité** : Plusieurs offres intègrent des intitulés "Data Analyst" mais sont classées sous des ROME inattendus (ex. *G1302 - Yield Manager*, *G1211 - Performance sportive*).
    """)

# ==============================================================================
# 5. TABLEAU D'ONGLETS DE DÉTAILS
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Répartition par Métier ROME",
    "🗺️ Dynamique Territoriale & BMO",
    "⚖️ Quadrant Tension vs Offres",
    "📋 Tableau d'Audit & Qualité",
])

with tab1:
    st.markdown("#### Top 15 Métiers ROME par Volume d'Offres")
    if not df_kpi_rome.empty:
        # Filtrer sur les 15 premiers métiers pour une lisibilité optimale
        df_plot_rome = df_kpi_rome.sort_values("nombre_offres", ascending=True).tail(15)
        fig_rome = px.bar(
            df_plot_rome,
            x="nombre_offres",
            y="rome_libelle",
            orientation="h",
            color="couverture_certifications_pct",
            color_continuous_scale="Viridis",
            labels={
                "nombre_offres": "Nombre d'offres",
                "rome_libelle": "Métier ROME",
                "couverture_certifications_pct": "% Couverture Certifications"
            },
            title="Distribution des offres par métier et taux de certification",
            text="nombre_offres",
        )
        fig_rome.update_layout(height=480, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_rome, use_container_width=True)
    else:
        st.warning("Données ROME non disponibles.")

with tab2:
    st.markdown("#### Comparaison Offres réelles vs Projets BMO par Région")
    if not df_offres_bmo.empty:
        df_bmo_sorted = df_offres_bmo.sort_values("nombre_offres", ascending=False)
        fig_bmo = go.Figure()
        fig_bmo.add_trace(go.Bar(
            x=df_bmo_sorted["region"],
            y=df_bmo_sorted["nombre_offres"],
            name="Offres réelles observées",
            marker_color="#1f77b4"
        ))
        if "projets_recrutement" in df_bmo_sorted.columns:
            fig_bmo.add_trace(go.Bar(
                x=df_bmo_sorted["region"],
                y=df_bmo_sorted["projets_recrutement"],
                name="Projets de recrutement (BMO 2026)",
                marker_color="#ff7f0e"
            ))
        fig_bmo.update_layout(
            barmode="group",
            title="Confrontation de l'offre et du besoin projeté par Région",
            xaxis_tickangle=-45,
            height=480,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_bmo, use_container_width=True)
        st.caption("Note méthodologique : Les populations BMO et les offres publiées ne recouvrent pas exactement les mêmes temporalités.")
    else:
        st.warning("Données BMO régionales non disponibles.")

with tab3:
    st.markdown("#### Matrice de Tension Métier (Offres collectées vs Projets BMO)")
    if not df_tension.empty:
        fig_scatter = px.scatter(
            df_tension,
            x="offres_collectees",
            y="projets_recrutement",
            size="projets_difficiles",
            color="taux_difficulte_pct",
            hover_name="nom_metier_bmo",
            text="code_metier_bmo",
            color_continuous_scale="Reds",
            labels={
                "offres_collectees": "Offres France Travail publiées",
                "projets_recrutement": "Projets BMO déclarés",
                "taux_difficulte_pct": "% Recrutements Difficiles",
                "projets_difficiles": "Volume Difficile"
            },
            title="Matrice Quadrant : Métiers sous Tension vs Visibilité Marché",
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(height=480, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("Données de tension non disponibles.")

with tab4:
    st.markdown("#### Table d'Audit de la Couverture et des Mappings (Fiches Data & Tech)")
    if not df_kpi_rome.empty:
        # Exclusion des codes ROME non Data/Tech : D (Commerce), I (Maintenance/Artisanat), J (Santé/Social), K (Services)
        df_kpi_rome_clean = df_kpi_rome[~df_kpi_rome["rome_code"].astype(str).str.startswith(('D', 'I', 'J', 'K'))]
        st.caption(f"Filtre actif : exclusion des codes ROME hors périmètre Data/Tech commençant par **D**, **I**, **J**, **K** ({len(df_kpi_rome_clean)} métiers conservés)")
        st.dataframe(
            df_kpi_rome_clean,
            use_container_width=True,
            column_config={
                "couverture_certifications_pct": st.column_config.ProgressColumn(
                    "% Couverture Certifications",
                    min_value=0,
                    max_value=100,
                    format="%.1f %%"
                ),
                "nombre_offres": st.column_config.NumberColumn("Offres"),
                "offres_mappees_certification": st.column_config.NumberColumn("Mappées RNCP"),
                "offres_sans_mapping": st.column_config.NumberColumn("Sans RNCP"),
            }
        )

