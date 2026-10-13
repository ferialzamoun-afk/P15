"""Page 4 — Formation, insertion et profils ROME."""

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_parquet

st.set_page_config(page_title="Page 4 — Formation & Profils ROME", page_icon="🎓", layout="wide")

# ==============================================================================
# 1. TITRE & DESCRIPTION
# ==============================================================================
st.title("🎓 Page 4 — Formation, insertion et profils ROME")
st.markdown("""
**Question métier :** *Quel est le volume de demandeurs sortants par ROME, comment se positionne le retour à l'emploi post-formation, et quels profils sociodémographiques (âge, genre) se dégagent ?*
Cette page croise les données de flux de demandeurs d'emploi sortant de formation, les taux d'insertion professionnelle et l'analyse en composantes principales (ACP) des profils métiers.
""")

# ==============================================================================
# 2. CHARGEMENT DES DONNÉES
# ==============================================================================
df_sortants_rome = load_parquet("sortants_demandeurs_by_rome.parquet")
df_acces_emploi = load_parquet("sortants_acces_emploi_summary.parquet")
df_profil_skills = load_parquet("profil_demandeurs_skills.parquet")

# Chargement du fichier ACP (CSV ou Parquet)
df_acp = pd.DataFrame()
try:
    df_acp = load_parquet("acp_rome_profils_age_genre.parquet")
    if df_acp.empty:
        df_acp = pd.read_csv("data/processed/marts/acp_rome_profils_age_genre.csv")
except Exception:
    pass

# ==============================================================================
# 3. INSIGHTS CLÉS & INSERTION
# ==============================================================================
st.subheader("💡 Insights clés & Profils de Demandeurs")

c1, c2, c3, c4 = st.columns(4)
total_sortants = df_sortants_rome["sortants_total"].sum() if not df_sortants_rome.empty and "sortants_total" in df_sortants_rome.columns else 0
date_sortants = pd.to_datetime(df_sortants_rome["derniere_mise_a_jour"], errors="coerce").max() if not df_sortants_rome.empty and "derniere_mise_a_jour" in df_sortants_rome.columns else pd.NaT
acces_unique = df_acces_emploi.iloc[0] if len(df_acces_emploi) == 1 and "taux_moyen" in df_acces_emploi.columns else None
df_acp_clean = df_acp[~df_acp["rome_code"].astype(str).str.startswith(("K", "D", "J"))] if not df_acp.empty and "rome_code" in df_acp.columns else pd.DataFrame()
nb_clusters_acp = df_acp_clean["cluster_label"].nunique() if not df_acp_clean.empty and "cluster_label" in df_acp_clean.columns else 0
cluster_counts = df_acp_clean["cluster_label"].value_counts().to_dict() if nb_clusters_acp else {}
cluster_summary = "; ".join(f"{str(label).replace('_', ' ')} : {count}" for label, count in cluster_counts.items()) or "non disponible"
variance_pc1 = float(df_acp_clean["var_expliquee_pc1_pct"].iloc[0]) if not df_acp_clean.empty and "var_expliquee_pc1_pct" in df_acp_clean.columns else None
variance_pc2 = float(df_acp_clean["var_expliquee_pc2_pct"].iloc[0]) if not df_acp_clean.empty and "var_expliquee_pc2_pct" in df_acp_clean.columns else None

c1.metric("Somme des volumes sortants", f"{int(total_sortants):,}" if total_sortants else "N/D", f"{len(df_sortants_rome)} codes ROME")
c2.metric("Accès à l'emploi (périmètre affiché)", f"{float(acces_unique.taux_moyen):.1f} %" if acces_unique is not None else "N/D")
c3.metric("Groupes ACP affichés", f"{nb_clusters_acp}" if nb_clusters_acp else "N/D")
c4.metric("Métiers dans l'ACP", f"{len(df_acp_clean)}" if not df_acp_clean.empty else "N/D")

with st.container():
        st.info(f"""
    📌 **Synthèse Socio-Démographique & Insertion :**
        * **Volumes sortants** : la somme des agrégats atteint **{int(total_sortants):,}** sur **{len(df_sortants_rome)} codes ROME** ; dernière mise à jour **{date_sortants.strftime('%d/%m/%Y') if pd.notna(date_sortants) else 'inconnue'}**. Ce cumul n'est pas un décompte de personnes distinctes.
        * **Accès à l'emploi** : {f"{float(acces_unique.taux_moyen):.1f} % pour {acces_unique.territoire} / {acces_unique.formation}, sur {int(acces_unique.periodes)} périodes ({int(acces_unique.observations)} observations)" if acces_unique is not None else f"{len(df_acces_emploi)} combinaisons territoire/formation disponibles ; aucun taux national moyen n'est calculé"}. Le périmètre affiché ne permet pas une comparaison nationale.
        * **ACP** : **{len(df_acp_clean)} métiers** dans le périmètre affiché, répartis en **{nb_clusters_acp} groupes** ({cluster_summary}). PC1 explique {f'{variance_pc1:.1f} %' if variance_pc1 is not None else 'N/D'} et PC2 {f'{variance_pc2:.1f} %' if variance_pc2 is not None else 'N/D'} de la variance ; les axes ne suffisent pas à déduire des profils d'âge ou de mobilité.
    """)

# ==============================================================================
# 4. ONGLETS DE DÉTAILS
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Analyse Factorielle des Profils (ACP)",
    "💼 Taux d'Accès à l'Emploi par Territoire",
    "⚖️ Sortants vs Compétences Requises",
    "📋 Données de Synthèse par Métier",
])

with tab1:
    st.markdown("#### Projection ACP des Métiers ROME Data & Tech (Âge & Genre)")
    if not df_acp.empty and "PC1" in df_acp.columns and "PC2" in df_acp.columns:
        st.caption(f"Filtre actif : focalisation sur les métiers Data & Ingénierie ({len(df_acp_clean)} métiers affichés)")
        
        fig_acp = px.scatter(
            df_acp_clean,
            x="PC1",
            y="PC2",
            color="cluster_label" if "cluster_label" in df_acp_clean.columns else None,
            hover_name="rome_libelle" if "rome_libelle" in df_acp_clean.columns else "rome_code",
            text="rome_code" if "rome_code" in df_acp_clean.columns else None,
            title="Plan Factoriel ACP : Typologie Sociodémographique des Métiers Data & Ingénierie",
            labels={"PC1": "Composante 1 (Structure d'Âge)", "PC2": "Composante 2 (Parité / Dynamisme)"},
        )
        fig_acp.update_traces(textposition="top center")
        fig_acp.update_layout(height=500)
        st.plotly_chart(fig_acp, use_container_width=True)
    else:
        st.info("Données factorielles ACP en cours d'actualisation.")

with tab2:
    st.markdown("#### Taux Moyen de Retour à l'Emploi par Région/Territoire")
    if not df_acces_emploi.empty and "taux_moyen" in df_acces_emploi.columns:
        fig_acc = px.bar(
            df_acces_emploi.sort_values("taux_moyen", ascending=True),
            x="taux_moyen",
            y="territoire" if "territoire" in df_acces_emploi.columns else ("code_territoire" if "code_territoire" in df_acces_emploi.columns else df_acces_emploi.index),
            orientation="h",
            color="taux_moyen",
            color_continuous_scale="Blues",
            title="Taux d'accès à l'emploi (%) par Territoire",
            text="taux_moyen",
        )
        fig_acc.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_acc, use_container_width=True)

with tab3:
    st.markdown("#### Croisement Profils Demandeurs × Compétences Prioritaires (Fiches Data uniquement)")
    if not df_profil_skills.empty and "rome_code" in df_profil_skills.columns:
        # Filtrage : exclusion des codes ROME commençant par K (services à la personne/collectivité) et D (commerce/vente)
        df_skills_clean = df_profil_skills[~df_profil_skills["rome_code"].astype(str).str.startswith(('K', 'D'))]
        
        st.caption(f"Filtre actif : exclusion des fiches ROME commençant par **K** et **D** ({len(df_skills_clean)} lignes de compétences Data conservées)")
        
        cols_profil = [
            c for c in [
                "rome_code", "rome_libelle", "competence_libelle_rome", "cluster_label",
                "nombre_offres_ft", "sortants_total", "taux_moyen", "score_mixte_demande_skills"
            ] if c in df_skills_clean.columns
        ]
        st.dataframe(df_skills_clean[cols_profil] if cols_profil else df_skills_clean, use_container_width=True)
    else:
        st.info("Table profil_demandeurs_skills non disponible.")

with tab4:
    st.markdown("#### Table détaillée des Sortants par ROME")
    if not df_sortants_rome.empty:
        st.dataframe(df_sortants_rome, use_container_width=True)
