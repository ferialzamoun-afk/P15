"""Page 2 — Marché des offres."""

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_parquet

st.set_page_config(page_title="Page 2 — Marché des offres", page_icon="💼", layout="wide")

# ==============================================================================
# 1. TITRE & DESCRIPTION
# ==============================================================================
st.title("💼 Page 2 — Marché des offres")
st.markdown("""
**Question métier :** *Quels postes sont observés, dans quels territoires, avec quels contrats et quelles anomalies de classification ou faux positifs ROME ?*
Cette page permet d'explorer la structure fine des opportunités d'emploi, les types d'engagements (CDI, CDD, Alternance) et les employeurs les plus actifs.
""")

# ==============================================================================
# 2. CHARGEMENT & PRÉPARATION
# ==============================================================================
df_offres = load_parquet("fact_offres.parquet")
df_top_ent = load_parquet("top_entreprises.parquet")
df_offers_dep = load_parquet("offers_by_departement.parquet")

if df_offres.empty:
    st.error("Aucune offre chargée.")
    st.stop()

# Barre latérale - Filtres
st.sidebar.markdown("### 🏛️ Sources de Données")
st.sidebar.markdown("""
* **France Travail** *(Offres d'emploi)*
* **Enquête BMO 2026** *(Besoins déclarés)*
* **France Compétences** *(Référentiel RNCP)*
""")
st.sidebar.divider()
st.sidebar.header("🔍 Filtres Marché des Offres")

# 1. Filtre Région
regions_dispo = ["Toutes"] + sorted(df_offres["region"].dropna().unique().tolist()) if "region" in df_offres.columns else ["Toutes"]
sel_region = st.sidebar.selectbox("Région", regions_dispo)

# 2. Filtre Mot-clé
mots_cles = ["Tous"] + sorted(df_offres["mot_cle_collecte"].dropna().unique().tolist()) if "mot_cle_collecte" in df_offres.columns else ["Tous"]
sel_mot_cle = st.sidebar.selectbox("Mot-clé initial", mots_cles)

# 3. Filtre Type de contrat
types_contrat = ["Tous"] + sorted(df_offres["typeContrat"].dropna().unique().tolist()) if "typeContrat" in df_offres.columns else ["Tous"]
sel_contrat = st.sidebar.selectbox("Type de contrat", types_contrat)

# 4. Filtre Alternance
opt_alt = st.sidebar.radio("Alternance", ["Toutes", "Uniquement Alternance", "Hors Alternance"])

# 5. Filtre Date de création
df_offres["date_creation_dt"] = pd.to_datetime(df_offres["dateCreation"], errors="coerce")
min_date_val = df_offres["date_creation_dt"].min()
max_date_val = df_offres["date_creation_dt"].max()

if pd.notna(min_date_val) and pd.notna(max_date_val):
    sel_date_range = st.sidebar.date_input(
        "Période de date de création",
        value=(min_date_val.date(), max_date_val.date()),
        min_value=min_date_val.date(),
        max_value=max_date_val.date(),
    )
else:
    sel_date_range = None

# Bouton réinitialiser
if st.sidebar.button("🔄 Réinitialiser les filtres", use_container_width=True):
    st.rerun()

# Application des filtres
df_filtered = df_offres.copy()
if sel_region != "Toutes":
    df_filtered = df_filtered[df_filtered["region"] == sel_region]
if sel_mot_cle != "Tous":
    df_filtered = df_filtered[df_filtered["mot_cle_collecte"] == sel_mot_cle]
if sel_contrat != "Tous":
    df_filtered = df_filtered[df_filtered["typeContrat"] == sel_contrat]
if opt_alt == "Uniquement Alternance":
    df_filtered = df_filtered[df_filtered["alternance"] == True]
elif opt_alt == "Hors Alternance":
    df_filtered = df_filtered[df_filtered["alternance"] == False]

if sel_date_range and len(sel_date_range) == 2:
    start_d, end_d = sel_date_range
    df_filtered = df_filtered[
        (df_filtered["date_creation_dt"].dt.date >= start_d) &
        (df_filtered["date_creation_dt"].dt.date <= end_d)
    ]

# ==============================================================================
# 3. INSIGHTS CLÉS & ANOMALIES DÉTECTÉES
# ==============================================================================
st.subheader("💡 Insights clés & Analyse du Marché")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
nb_cdi = (df_filtered["typeContrat"] == "CDI").sum() if "typeContrat" in df_filtered.columns else 0
part_cdi = (nb_cdi / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
nb_alt = (df_filtered["alternance"] == True).sum() if "alternance" in df_filtered.columns else 0

kpi1.metric("Offres sélectionnées", f"{len(df_filtered):,}")
kpi2.metric("Part de CDI", f"{part_cdi:.1f} %", f"{nb_cdi} postes")
kpi3.metric("Postes en Alternance", f"{nb_alt}", f"{nb_alt/len(df_filtered)*100:.1f} %")
kpi4.metric("Entreprises distinctes", f"{df_filtered['entreprise_nom'].nunique() if 'entreprise_nom' in df_filtered.columns else 0}")

with st.container():
    st.warning("""
    ⚠️ **Audit des Faux Positifs & Incohérences de Classification :**
    * **Faux positifs ROME** : Plusieurs offres avec intitulé *"Ingénieur Data Analyst"* sont classées en **G1302 (Yield Manager)** ou **M1423 (Chief Data Officer)** par l'algorithme de France Travail.
    * **Incohérence Alternance / Contrat** : Des offres mentionnent *"alternance"* ou *"apprentissage"* dans l'intitulé tout en étant libellées en CDI ou avec l'attribut `alternance=False`.
    * **Entreprises masquées** : 35 % des offres ont un employeur `Non renseignée` dans le champ structuré, bien que le nom apparaisse dans le corps du texte (ex. Safran, Thales).
    """)

# ==============================================================================
# 4. ONGLETS DE DÉTAILS
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Treemap Géographique (Région → Dép.)",
    "📄 Contrats & Alternance",
    "🏢 Top Entreprises Recruteuses",
    "📋 Explorateur & Recherche d'Offres",
])

with tab1:
    st.markdown("#### Poids relatif des Territoires (sans biais de surface)")
    if "region" in df_filtered.columns and "lieu_libelle" in df_filtered.columns:
        def get_top_intitule(series):
            vc = series.dropna().value_counts()
            return vc.index[0] if len(vc) > 0 else "Non renseigné"

        df_tree = df_filtered.groupby(["region", "lieu_libelle"]).agg(
            nb_offres=("id", "count"),
            poste_dominant=("intitule", get_top_intitule)
        ).reset_index()

        fig_tree = px.treemap(
            df_tree,
            path=["region", "lieu_libelle"],
            values="nb_offres",
            title="Hiérarchie des Opportunités d'Emploi par Région et Territoire",
            color="nb_offres",
            color_continuous_scale="Blues",
            custom_data=["poste_dominant"]
        )
        fig_tree.update_traces(
            hovertemplate="<b>%{label}</b><br>Parent : %{parent}<br>Nombre d'offres : %{value}<br>🏆 <b>Poste le plus fréquent :</b> %{customdata[0]}<extra></extra>"
        )
        fig_tree.update_layout(height=520, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.info("Données de localisation indisponibles.")

with tab2:
    st.markdown("#### Répartition des Contrats par Métier ROME")
    if "romeLibelle" in df_filtered.columns and "typeContrat" in df_filtered.columns:
        df_contrat = df_filtered.groupby(["romeLibelle", "typeContrat"]).size().reset_index(name="nb_offres")
        fig_c = px.bar(
            df_contrat,
            x="nb_offres",
            y="romeLibelle",
            color="typeContrat",
            orientation="h",
            title="Typologie de contrat par intitulé métier",
            barmode="stack",
        )
        fig_c.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_c, use_container_width=True)

with tab3:
    st.markdown("#### Top Entreprises qui recrutent (Hors 'Non renseignée')")
    if not df_top_ent.empty and "entreprise_nom" in df_top_ent.columns:
        df_ent_clean = df_top_ent[df_top_ent["entreprise_nom"] != "Non renseignee"].head(15)
        fig_ent = px.bar(
            df_ent_clean.sort_values("nombre_offres", ascending=True),
            x="nombre_offres",
            y="entreprise_nom",
            orientation="h",
            title="Top 15 Entreprises identifiées",
            color="nombre_offres",
            color_continuous_scale="Teal",
            text="nombre_offres",
        )
        fig_ent.update_layout(height=480, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_ent, use_container_width=True)

with tab4:
    st.markdown("#### Recherche textuelle et table détaillée")
    search_query = st.text_input("🔎 Rechercher dans l'intitulé ou la description", "")
    df_table = df_filtered.copy()
    if search_query:
        mask = (
            df_table["intitule"].astype(str).str.contains(search_query, case=False, na=False) |
            df_table["description"].astype(str).str.contains(search_query, case=False, na=False)
        )
        df_table = df_table[mask]

    cols_view = [c for c in ["id", "intitule", "romeCode", "romeLibelle", "entreprise_nom", "lieu_libelle", "typeContrat", "alternance", "dateCreation"] if c in df_table.columns]
    st.dataframe(df_table[cols_view], use_container_width=True)
