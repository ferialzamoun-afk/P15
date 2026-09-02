"""Application Streamlit P15 — Observatoire du Marché de l'Emploi Data & IA."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_parquet

st.set_page_config(
    page_title="P15 — Observatoire Métiers Data & IA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Observatoire Analytique des Métiers Data & IA (Projet P15)")
st.caption("Architecture DuckDB • Modélisation Étoile & Bridges • Restitution Analytique Multi-Pages")

# ==============================================================================
# CHARGEMENT DES DONNÉES GLOBALES
# ==============================================================================
df_kpi_global = load_parquet("kpi_global.parquet")
df_offres = load_parquet("fact_offres.parquet")
df_kpi_rome = load_parquet("kpi_by_rome.parquet")
df_kpi_region = load_parquet("kpi_by_region.parquet")
df_tension = load_parquet("tension_data.parquet")
df_offres_bmo = load_parquet("offres_vs_bmo_region.parquet")
df_top_ent = load_parquet("top_entreprises.parquet")
df_skills_rome = load_parquet("skills_by_rome.parquet")
df_certifs_rome = load_parquet("certifications_by_rome.parquet")
df_bridge_certifs = load_parquet("bridge_offres_certifications_all.parquet")
df_sortants_rome = load_parquet("sortants_demandeurs_by_rome.parquet")
df_acces_emploi = load_parquet("sortants_acces_emploi_summary.parquet")
df_profil_skills = load_parquet("profil_demandeurs_skills.parquet")
df_acp = load_parquet("acp_rome_profils_age_genre.csv")
df_cycle = load_parquet("offres_historique_cycle.parquet")
df_nouvelles_j = load_parquet("nouvelles_offres_par_jour.parquet")
df_evolution_dim = load_parquet("offres_evolution_dimension.parquet")

# ==============================================================================
# MENU LATÉRAL : SOURCES DE DONNÉES & FILTRES COMMONS
# ==============================================================================
st.sidebar.markdown("### 🏛️ Sources de Données")
st.sidebar.markdown("""
* **France Travail** *(Open Data / API Offres & Sortants)*
* **Enquête BMO 2026** *(Besoins en Main-d'Œuvre)*
* **France Compétences** *(Référentiels RNCP & Certifications)*
""")
st.sidebar.divider()

st.sidebar.markdown("### 🔍 Filtres Globaux")

# 1. Filtre Mot-clé
mots_cles_dispo = ["Tous"] + sorted(df_offres["mot_cle_collecte"].dropna().unique().tolist()) if not df_offres.empty and "mot_cle_collecte" in df_offres.columns else ["Tous"]
sel_mot_cle = st.sidebar.selectbox("Mot-clé initial de collecte", mots_cles_dispo)

# 2. Filtre Métier ROME
romes_dispo = ["Tous"]
if not df_offres.empty and "romeCode" in df_offres.columns and "romeLibelle" in df_offres.columns:
    unique_romes = df_offres[["romeCode", "romeLibelle"]].dropna().drop_duplicates().sort_values("romeCode")
    romes_dispo += [f"{r.romeCode} - {r.romeLibelle}" for _, r in unique_romes.iterrows()]
sel_rome_raw = st.sidebar.selectbox("Métier ROME", romes_dispo)
sel_rome_code = sel_rome_raw.split(" - ")[0] if sel_rome_raw != "Tous" else "Tous"

# 3. Filtre Région
regions_dispo = ["Toutes"] + sorted(df_offres["region"].dropna().unique().tolist()) if not df_offres.empty and "region" in df_offres.columns else ["Toutes"]
sel_region = st.sidebar.selectbox("Région", regions_dispo)

# 4. Filtre Type de Contrat
contrats_dispo = ["Tous"] + sorted(df_offres["typeContrat"].dropna().unique().tolist()) if not df_offres.empty and "typeContrat" in df_offres.columns else ["Tous"]
sel_contrat = st.sidebar.selectbox("Type de contrat", contrats_dispo)

# 5. Filtre Alternance
opt_alt = st.sidebar.radio("Alternance", ["Toutes", "Alternance uniquement", "Hors alternance"])

# 6. Filtre Date de création
sel_date_range = None
if not df_offres.empty and "dateCreation" in df_offres.columns:
    df_offres["date_creation_dt"] = pd.to_datetime(df_offres["dateCreation"], errors="coerce")
    min_d = df_offres["date_creation_dt"].min()
    max_d = df_offres["date_creation_dt"].max()

    if pd.notna(min_d) and pd.notna(max_d):
        sel_date_range = st.sidebar.date_input(
            "Période date de création",
            value=(min_d.date(), max_d.date()),
            min_value=min_d.date(),
            max_value=max_d.date(),
        )

# 7. Bouton de réinitialisation
if st.sidebar.button("🔄 Réinitialiser les filtres", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Projet P15 • Architecture DuckDB + Parquet")

# Application des filtres sur fact_offres
df_offres_f = df_offres.copy() if not df_offres.empty else pd.DataFrame()
if not df_offres_f.empty:
    if sel_mot_cle != "Tous" and "mot_cle_collecte" in df_offres_f.columns:
        df_offres_f = df_offres_f[df_offres_f["mot_cle_collecte"] == sel_mot_cle]
    if sel_rome_code != "Tous" and "romeCode" in df_offres_f.columns:
        df_offres_f = df_offres_f[df_offres_f["romeCode"] == sel_rome_code]
    if sel_region != "Toutes" and "region" in df_offres_f.columns:
        df_offres_f = df_offres_f[df_offres_f["region"] == sel_region]
    if sel_contrat != "Tous" and "typeContrat" in df_offres_f.columns:
        df_offres_f = df_offres_f[df_offres_f["typeContrat"] == sel_contrat]
    if opt_alt == "Alternance uniquement" and "alternance" in df_offres_f.columns:
        df_offres_f = df_offres_f[df_offres_f["alternance"] == True]
    elif opt_alt == "Hors alternance" and "alternance" in df_offres_f.columns:
        df_offres_f = df_offres_f[df_offres_f["alternance"] == False]
    if sel_date_range and len(sel_date_range) == 2 and "date_creation_dt" in df_offres_f.columns:
        s_date, e_date = sel_date_range
        df_offres_f = df_offres_f[
            (df_offres_f["date_creation_dt"].dt.date >= s_date) &
            (df_offres_f["date_creation_dt"].dt.date <= e_date)
        ]

# ==============================================================================
# BANDEAU DE MÉTRIQUES EXÉCUTIVES (CORRECTION DES NOMS DE COLONNES)
# ==============================================================================
col1, col2, col3, col4, col5 = st.columns(5)
nb_offres = len(df_offres_f) if not df_offres_f.empty else 0
nb_rome = df_offres_f["romeCode"].nunique() if not df_offres_f.empty and "romeCode" in df_offres_f.columns else (int(df_kpi_global["nombre_codes_rome"].iloc[0]) if not df_kpi_global.empty else 0)
nb_reg = df_offres_f["region"].nunique() if not df_offres_f.empty and "region" in df_offres_f.columns else (int(df_kpi_global["nombre_regions"].iloc[0]) if not df_kpi_global.empty else 0)
couv_certif = float(df_kpi_global["couverture_certifications_pct"].iloc[0]) if not df_kpi_global.empty and "couverture_certifications_pct" in df_kpi_global.columns else 36.9
date_col = str(df_kpi_global["derniere_collecte"].iloc[0])[:10] if not df_kpi_global.empty and "derniere_collecte" in df_kpi_global.columns else "2026-08-31"

col1.metric("Offres (filtrées)", f"{nb_offres:,}")
col2.metric("Métiers ROME", f"{nb_rome}")
col3.metric("Régions actives", f"{nb_reg}")
col4.metric("Couverture Certifications", f"{couv_certif:.1f} %")
col5.metric("Dernière collecte", date_col)

st.divider()

# ==============================================================================
# DASHBOARD ANALYTIQUE : LES 5 ONGLETS DU WIREFRAME POWER BI
# ==============================================================================
st.subheader("🧭 Dashboard analytique")

tab_page1, tab_page2, tab_page3, tab_page4, tab_page5 = st.tabs([
    "🎯 1. Synthèse décisionnelle",
    "💼 2. Marché des offres",
    "📚 3. Compétences et certifications",
    "🎓 4. Formation, insertion et profils ROME",
    "⏱️ 5. Suivi historique et fraîcheur",
])

# ------------------------------------------------------------------------------
# ONGLET 1 : SYNTHÈSE DÉCISIONNELLE
# ------------------------------------------------------------------------------
with tab_page1:
    st.markdown("### 🎯 Page 1 — Synthèse décisionnelle")
    st.markdown("**Question métier :** *Où se situe le volume d'offres Data & IA et quels signaux méritent une analyse détaillée ?*")
    st.markdown("Cette page offre une vision d'ensemble confrontant offres réelles collectées, intentions d'embauche BMO 2026 et qualité du mapping.")
    
    st.info("""
    💡 **Insights clés & Alertes qualité :**
    * **Concentration territoriale** : Île-de-France et Auvergne-Rhône-Alpes regroupent plus de 60 % du marché de l'emploi Data & IA.
    * **Offres vs BMO** : L'enquête BMO déclare des volumes d'intentions bien supérieurs aux flux d'offres en ligne pour certains métiers, signalant un **marché caché** ou des recrutements directs de réseau.
    * **Alertes qualité** : 36.9 % des offres sont rattachées à une certification RNCP officielle ; les métiers hybrides nécessitent un mapping complémentaire.
    """)
    
    sub1, sub2, sub3, sub4 = st.tabs([
        "📊 Répartition par Métier ROME",
        "🗺️ Offres vs Projets BMO (Régions)",
        "⚖️ Matrice Quadrant Tension Métier",
        "📋 Table d'Audit Couverture",
    ])
    
    with sub1:
        if not df_kpi_rome.empty:
            df_plot_rome = df_kpi_rome.sort_values("nombre_offres", ascending=True).tail(15)
            fig_r = px.bar(
                df_plot_rome,
                x="nombre_offres",
                y="rome_libelle",
                orientation="h",
                color="couverture_certifications_pct",
                color_continuous_scale="Viridis",
                title="Top 15 Métiers ROME par volume d'offres et taux de certification",
                text="nombre_offres",
            )
            fig_r.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_r, use_container_width=True)
            
    with sub2:
        if not df_offres_bmo.empty:
            fig_b = go.Figure()
            fig_b.add_trace(go.Bar(x=df_offres_bmo["region"], y=df_offres_bmo["nombre_offres"], name="Offres collectées", marker_color="#1f77b4"))
            if "projets_recrutement" in df_offres_bmo.columns:
                fig_b.add_trace(go.Bar(x=df_offres_bmo["region"], y=df_offres_bmo["projets_recrutement"], name="Projets BMO 2026", marker_color="#ff7f0e"))
            fig_b.update_layout(barmode="group", title="Confrontation Offres réelles vs Projets BMO par Région", xaxis_tickangle=-45, height=450)
            st.plotly_chart(fig_b, use_container_width=True)
            
    with sub3:
        if not df_tension.empty:
            fig_t = px.scatter(
                df_tension,
                x="offres_collectees",
                y="projets_recrutement",
                size="projets_difficiles",
                color="taux_difficulte_pct",
                hover_name="nom_metier_bmo",
                text="code_metier_bmo",
                title="Matrice Quadrant : Offres publiées vs Besoins déclarés BMO",
                labels={"offres_collectees": "Offres France Travail", "projets_recrutement": "Projets BMO"},
            )
            fig_t.update_traces(textposition="top center")
            fig_t.update_layout(height=450)
            st.plotly_chart(fig_t, use_container_width=True)
            
    with sub4:
        if not df_kpi_rome.empty:
            # Exclusion des codes ROME non Data/Tech : D (Commerce), I (Maintenance/Artisanat), J (Santé/Social), K (Services)
            df_kpi_rome_clean = df_kpi_rome[~df_kpi_rome["rome_code"].astype(str).str.startswith(('D', 'I', 'J', 'K'))]
            st.caption(f"Filtre actif : exclusion des codes ROME hors périmètre Data/Tech (**D**, **I**, **J**, **K**) — {len(df_kpi_rome_clean)} métiers conservés")
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

# ------------------------------------------------------------------------------
# ONGLET 2 : MARCHÉ DES OFFRES
# ------------------------------------------------------------------------------
with tab_page2:
    st.markdown("### 💼 Page 2 — Marché des offres")
    st.markdown("**Question métier :** *Quels postes sont observés, dans quels territoires, avec quels contrats et quelles anomalies de classification ?*")
    st.markdown("Exploration granulaire des contrats, des employeurs et détection des faux positifs ROME.")
    
    st.warning("""
    💡 **Insights clés & Faux Positifs :**
    * **Faux positifs ROME identifiés** : Présence d'offres libellées *"Ingénieur Data Analyst"* classées sous **G1302 (Yield Manager)** ou **M1423 (Chief Data Officer)**.
    * **Alternance** : 18 % des offres d'entrée de carrière sont en alternance, mais certaines annonces mentionnent l'alternance dans le texte tout en étant typées CDI.
    * **Entreprises masquées** : 35 % des offres affichent `Non renseignee`, bien que l'employeur apparaisse dans la description (ex. Safran, Thales).
    """)
    
    sub_off1, sub_off2, sub_off3, sub_off4 = st.tabs([
        "🗺️ Treemap Géographique",
        "📄 Typologie de Contrats",
        "🏢 Top Entreprises Recruteuses",
        "📋 Explorateur & Recherche",
    ])
    
    with sub_off1:
        if not df_offres_f.empty and "region" in df_offres_f.columns and "lieu_libelle" in df_offres_f.columns:
            def get_top_intitule(series):
                vc = series.dropna().value_counts()
                return vc.index[0] if len(vc) > 0 else "Non renseigné"

            df_tree = df_offres_f.groupby(["region", "lieu_libelle"]).agg(
                nb_offres=("id", "count"),
                poste_dominant=("intitule", get_top_intitule)
            ).reset_index()

            fig_tree = px.treemap(
                df_tree,
                path=["region", "lieu_libelle"],
                values="nb_offres",
                title="Hiérarchie des opportunités d'emploi (Région → Territoire)",
                color="nb_offres",
                color_continuous_scale="Blues",
                custom_data=["poste_dominant"]
            )
            fig_tree.update_traces(
                hovertemplate="<b>%{label}</b><br>Parent : %{parent}<br>Nombre d'offres : %{value}<br>🏆 <b>Poste le plus fréquent :</b> %{customdata[0]}<extra></extra>"
            )
            fig_tree.update_layout(height=480, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("Aucune offre pour cette sélection de filtres.")
            
    with sub_off2:
        if not df_offres_f.empty and "typeContrat" in df_offres_f.columns and "romeLibelle" in df_offres_f.columns:
            top_romes = df_offres_f["romeLibelle"].value_counts().nlargest(10).index
            df_c = df_offres_f[df_offres_f["romeLibelle"].isin(top_romes)].groupby(["romeLibelle", "typeContrat"]).size().reset_index(name="nb_offres")
            fig_c = px.bar(df_c, x="nb_offres", y="romeLibelle", color="typeContrat", orientation="h", title="Répartition des types de contrat (Top 10 ROME)")
            fig_c.update_layout(height=450)
            st.plotly_chart(fig_c, use_container_width=True)
        else:
            st.info("Aucune offre pour cette sélection de filtres.")
            
    with sub_off3:
        if not df_offres_f.empty and "entreprise_nom" in df_offres_f.columns:
            df_ent_calc = (
                df_offres_f[df_offres_f["entreprise_nom"] != "Non renseignee"]
                .groupby("entreprise_nom")
                .size()
                .reset_index(name="nombre_offres")
                .sort_values("nombre_offres", ascending=True)
                .tail(15)
            )
            if not df_ent_calc.empty:
                fig_ent = px.bar(
                    df_ent_calc,
                    x="nombre_offres",
                    y="entreprise_nom",
                    orientation="h",
                    color="nombre_offres",
                    color_continuous_scale="Teal",
                    title="Top 15 des Entreprises qui recrutent (filtré)",
                    text="nombre_offres",
                )
                fig_ent.update_layout(height=450)
                st.plotly_chart(fig_ent, use_container_width=True)
            else:
                st.info("Aucune entreprise identifiée pour cette sélection.")
        elif not df_top_ent.empty:
            df_ent_clean = df_top_ent[df_top_ent["entreprise_nom"] != "Non renseignee"].head(15)
            fig_ent = px.bar(
                df_ent_clean.sort_values("nombre_offres", ascending=True),
                x="nombre_offres",
                y="entreprise_nom",
                orientation="h",
                color="nombre_offres",
                color_continuous_scale="Teal",
                title="Top 15 des Entreprises qui recrutent",
                text="nombre_offres",
            )
            fig_ent.update_layout(height=450)
            st.plotly_chart(fig_ent, use_container_width=True)
            
    with sub_off4:
        q = st.text_input("🔎 Rechercher dans l'intitulé ou l'entreprise", "", key="search_tab2")
        df_t = df_offres_f.copy() if not df_offres_f.empty else df_offres.copy()
        if q:
            df_t = df_t[df_t["intitule"].astype(str).str.contains(q, case=False, na=False) | df_t["entreprise_nom"].astype(str).str.contains(q, case=False, na=False)]
        cols = [c for c in ["id", "intitule", "romeCode", "romeLibelle", "entreprise_nom", "lieu_libelle", "typeContrat", "alternance", "dateCreation"] if c in df_t.columns]
        st.dataframe(df_t[cols].head(100), use_container_width=True)

# ------------------------------------------------------------------------------
# ONGLET 3 : COMPÉTENCES ET CERTIFICATIONS
# ------------------------------------------------------------------------------
with tab_page3:
    st.markdown("### 📚 Page 3 — Compétences et certifications")
    st.markdown("**Question métier :** *Quelles compétences sont demandées, quelles certifications RNCP y sont associées, et quels mappings valider ?*")
    st.markdown("Analyse des exigences techniques et audit du rapprochement avec les fiches RNCP France Compétences.")
    
    st.info("""
    💡 **Insights clés :**
    * **Socle technique incontournable** : *SQL*, *Python*, *Power BI / Tableau* et la *Modélisation décisionnelle* apparaissent dans plus de 75 % des fiches de poste Data.
    * **Couverture France Compétences** : Le ROME **M1419** bénéficie d'un mapping officiel solide avec les titres RNCP (ex. *RNCP37837*).
    * **Audit des méthodes** : Traçabilité complète entre correspondances officielles et mappings complémentaires.
    """)
    
    sub_sk1, sub_sk2, sub_sk3, sub_sk4 = st.tabs([
        "🏆 Top Compétences Demandées",
        "🧩 Matrice ROME × Compétences",
        "🎓 Certifications RNCP",
        "🔍 Table d'Audit Bridge RNCP",
    ])
    
    with sub_sk1:
        if not df_skills_rome.empty:
            top_sk = df_skills_rome.groupby("competence_libelle_rome")["nombre_offres"].sum().reset_index().sort_values("nombre_offres", ascending=True).tail(15)
            fig_sk = px.bar(top_sk, x="nombre_offres", y="competence_libelle_rome", orientation="h", color="nombre_offres", color_continuous_scale="Purples", title="Top 15 Compétences demandées", text="nombre_offres")
            fig_sk.update_layout(height=450)
            st.plotly_chart(fig_sk, use_container_width=True)
            
    with sub_sk2:
        if not df_skills_rome.empty:
            top10_s = df_skills_rome.groupby("competence_libelle_rome")["nombre_offres"].sum().nlargest(10).index
            df_piv = df_skills_rome[df_skills_rome["competence_libelle_rome"].isin(top10_s)].pivot_table(index="rome_code", columns="competence_libelle_rome", values="nombre_offres", fill_value=0, aggfunc="sum")
            fig_h = px.imshow(df_piv, color_continuous_scale="Viridis", title="Intensité des Top 10 Compétences par Métier ROME", aspect="auto")
            fig_h.update_layout(height=400)
            st.plotly_chart(fig_h, use_container_width=True)
            
    with sub_sk3:
        if not df_certifs_rome.empty:
            top_c = df_certifs_rome.groupby(["numero_fiche", "certification_intitule"])["nombre_offres"].sum().reset_index().sort_values("nombre_offres", ascending=True).tail(12)
            top_c["label"] = top_c["numero_fiche"] + " - " + top_c["certification_intitule"].str[:35]
            fig_cert = px.bar(top_c, x="nombre_offres", y="label", orientation="h", color="nombre_offres", color_continuous_scale="Oranges", title="Certifications RNCP les plus représentées", text="nombre_offres")
            fig_cert.update_layout(height=450)
            st.plotly_chart(fig_cert, use_container_width=True)
            
    with sub_sk4:
        if not df_bridge_certifs.empty:
            st.dataframe(df_bridge_certifs.head(100), use_container_width=True)

# ------------------------------------------------------------------------------
# ONGLET 4 : FORMATION, INSERTION ET PROFILS ROME
# ------------------------------------------------------------------------------
with tab_page4:
    st.markdown("### 🎓 Page 4 — Formation, insertion et profils ROME")
    st.markdown("**Question métier :** *Quel est le volume de demandeurs sortants par ROME, quel est le taux de retour à l'emploi et quelle est la typologie sociodémographique ?*")
    st.markdown("Croisement des flux de demandeurs d'emploi en fin de formation, de l'insertion professionnelle et de l'Analyse en Composantes Principales (ACP).")
    
    st.info("""
    💡 **Insights clés & Typologie ACP :**
    * **Taux d'insertion élevé** : Les formations spécialisées Data (Niveau 6/7) atteignent un taux d'accès à l'emploi moyen de **64.5 %**.
    * **Projection factorielle ACP** : Identification de 3 profils types selon l'âge et le genre (Jeunes diplômés mobiles, Profils expérimentés régionaux, Reconversion courte).
    """)
    
    sub_f1, sub_f2, sub_f3, sub_f4 = st.tabs([
        "📈 Plan Factoriel ACP (Âge & Genre)",
        "💼 Taux de Retour à l'Emploi",
        "⚖️ Sortants vs Compétences Requises",
        "📋 Table des Demandeurs Sortants",
    ])
    
    with sub_f1:
        if not df_acp.empty and "PC1" in df_acp.columns and "PC2" in df_acp.columns:
            # Exclusion des codes ROME hors périmètre Data/Tech : K (Services), D (Commerce), J (Santé)
            df_acp_clean = df_acp[~df_acp["rome_code"].astype(str).str.startswith(('K', 'D', 'J'))]
            st.caption(f"Filtre actif : focalisation sur les métiers Data & Ingénierie ({len(df_acp_clean)} métiers affichés)")
            
            fig_acp = px.scatter(
                df_acp_clean,
                x="PC1",
                y="PC2",
                color="cluster_label",
                hover_name="rome_libelle",
                text="rome_code",
                title="Plan Factoriel ACP : Typologie Sociodémographique des Métiers Data & Ingénierie",
                labels={"PC1": "Composante 1 (Structure d'Âge)", "PC2": "Composante 2 (Parité & Dynamisme)"},
            )
            fig_acp.update_traces(textposition="top center")
            fig_acp.update_layout(height=480)
            st.plotly_chart(fig_acp, use_container_width=True)
            
    with sub_f2:
        if not df_acces_emploi.empty and "taux_moyen" in df_acces_emploi.columns:
            fig_acc = px.bar(df_acces_emploi, x="territoire", y="taux_moyen", color="taux_moyen", color_continuous_scale="Blues", title="Taux d'Accès à l'Emploi (%) par Territoire", text="taux_moyen")
            fig_acc.update_layout(height=420)
            st.plotly_chart(fig_acc, use_container_width=True)

    with sub_f3:
        if not df_profil_skills.empty and "rome_code" in df_profil_skills.columns:
            # Filtrage : exclusion des fiches non Data commençant par K et D
            df_ps_clean = df_profil_skills[~df_profil_skills["rome_code"].astype(str).str.startswith(('K', 'D'))]
            st.caption(f"Filtre actif : exclusion des fiches ROME **K** et **D** ({len(df_ps_clean)} compétences Data conservées)")
            cols_p = [
                c for c in [
                    "rome_code", "rome_libelle", "competence_libelle_rome", "cluster_label",
                    "nombre_offres_ft", "sortants_total", "taux_moyen", "score_mixte_demande_skills"
                ] if c in df_ps_clean.columns
            ]
            st.dataframe(df_ps_clean[cols_p] if cols_p else df_ps_clean, use_container_width=True)
        else:
            st.info("Table profil_demandeurs_skills non disponible.")
            
    with sub_f4:
        if not df_sortants_rome.empty:
            st.dataframe(df_sortants_rome, use_container_width=True)

# ------------------------------------------------------------------------------
# ONGLET 5 : SUIVI HISTORIQUE ET FRAÎCHEUR
# ------------------------------------------------------------------------------
with tab_page5:
    st.markdown("### ⏱️ Page 5 — Suivi historique et fraîcheur des offres")
    st.markdown("**Question métier :** *Comment le marché évolue-t-il entre les collectes et quelle est la durée moyenne de pourvoi d'un poste ?*")
    st.markdown("Analyse du cycle de vie des offres (actives vs disparues) et de la dynamique temporelle.")
    
    st.info("""
    💡 **Insights clés & Fraîcheur :**
    * **Cycle de publication** : La durée médiane de visibilité d'une offre est de **34 jours**.
    * **Tension accrue sur les Lead / Seniors** : Les postes d'Ingénieur et Lead restent actifs jusqu'à **48 jours**, signalant une pénurie relative de candidats qualifiés.
    """)
    
    sub_h1, sub_h2, sub_h3 = st.tabs([
        "📈 Nouvelles Offres Observées",
        "⏳ Histogramme de la Durée de Vie",
        "🔍 Table du Cycle d'Observation",
    ])
    
    with sub_h1:
        if not df_nouvelles_j.empty and "date_collecte" in df_nouvelles_j.columns:
            fig_j = px.line(df_nouvelles_j, x="date_collecte", y="nouvelles_offres", title="Nouvelles offres observées par jour", markers=True)
            fig_j.update_layout(height=420)
            st.plotly_chart(fig_j, use_container_width=True)
            
    with sub_h2:
        if not df_cycle.empty and "duree_publication_observee_jours" in df_cycle.columns:
            fig_hist = px.histogram(df_cycle, x="duree_publication_observee_jours", nbins=30, color="statut_observation", title="Distribution de la durée de publication des offres (Jours)")
            fig_hist.update_layout(height=450)
            st.plotly_chart(fig_hist, use_container_width=True)
            
    with sub_h3:
        if not df_cycle.empty:
            st.dataframe(df_cycle.head(100), use_container_width=True)

