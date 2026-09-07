"""Module de chargement optimisé des données DuckDB et Parquet pour l'application Streamlit P15."""

from pathlib import Path
import duckdb
import pandas as pd
import streamlit as st

EXCLUDED_DISPLAY_ROME_CODES = {"K2205", "D1106", "J1102", "H2605", "I1620"}
ROME_CODE_COLUMNS = ("romeCode", "rome_code")


def exclude_display_rome_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Retire de l'affichage les codes ROME hors périmètre métier Data & IA."""
    if df.empty:
        return df

    filtered_df = df
    for column in ROME_CODE_COLUMNS:
        if column in filtered_df.columns:
            filtered_df = filtered_df[
                ~filtered_df[column].astype(str).isin(EXCLUDED_DISPLAY_ROME_CODES)
            ]
    return filtered_df

def get_marts_dir() -> Path:
    """Trouve dynamiquement le dossier des marts contenant les fichiers parquet."""
    current_file = Path(__file__).resolve()
    candidates = [
        current_file.parent.parent / "data" / "processed" / "marts",  # streamlit_app/data/processed/marts
        current_file.parent.parent.parent / "data" / "processed" / "marts",  # repo_root/data/processed/marts
        Path.cwd() / "streamlit_app" / "data" / "processed" / "marts",
        Path.cwd() / "data" / "processed" / "marts",
        Path("C:/Users/feria/Documents/P15/streamlit_app/data/processed/marts"),
        Path("C:/Users/feria/Documents/P15/data/processed/marts"),
    ]
    for c in candidates:
        if c.exists() and any(c.glob("*.parquet")):
            return c
    return candidates[0]


@st.cache_data(ttl=3600)
def load_parquet(file_name: str) -> pd.DataFrame:
    """Charge un fichier Parquet ou CSV depuis le dossier marts avec mise en cache."""
    stem = file_name.replace(".parquet", "").replace(".csv", "")
    marts = get_marts_dir()
    
    # 1. Essai Parquet direct
    p_file = marts / f"{stem}.parquet"
    if p_file.exists():
        try:
            return exclude_display_rome_codes(pd.read_parquet(p_file))
        except Exception:
            try:
                con = duckdb.connect()
                df = con.execute(f"SELECT * FROM '{p_file.as_posix()}'").df()
                con.close()
                return exclude_display_rome_codes(df)
            except Exception:
                pass
                
    # 2. Essai CSV
    c_file = marts / f"{stem}.csv"
    if c_file.exists():
        try:
            return exclude_display_rome_codes(pd.read_csv(c_file))
        except Exception:
            pass
            
    # 3. Parcours complet des candidats de secours
    current_file = Path(__file__).resolve()
    candidates = [
        current_file.parent.parent / "data" / "processed" / "marts",
        current_file.parent.parent.parent / "data" / "processed" / "marts",
        Path.cwd() / "streamlit_app" / "data" / "processed" / "marts",
        Path.cwd() / "data" / "processed" / "marts",
    ]
    for d in candidates:
        pf = d / f"{stem}.parquet"
        if pf.exists():
            try:
                return exclude_display_rome_codes(pd.read_parquet(pf))
            except Exception:
                pass
        cf = d / f"{stem}.csv"
        if cf.exists():
            try:
                return exclude_display_rome_codes(pd.read_csv(cf))
            except Exception:
                pass

    return pd.DataFrame()


@st.cache_data(ttl=3600)
def execute_query(query: str) -> pd.DataFrame:
    """Exécute une requête SQL DuckDB sur les marts Parquet enregistrés comme tables."""
    try:
        con = duckdb.connect()
        marts = get_marts_dir()
        if marts.exists():
            for p in marts.glob("*.parquet"):
                con.execute(f"CREATE OR REPLACE VIEW {p.stem} AS SELECT * FROM '{p.as_posix()}'")
            for c in marts.glob("*.csv"):
                con.execute(f"CREATE OR REPLACE VIEW {c.stem} AS SELECT * FROM '{c.as_posix()}'")
        df = con.execute(query).df()
        con.close()
        return df
    except Exception as e:
        st.warning(f"Avertissement SQL : {e}")
        return pd.DataFrame()


def get_available_marts() -> list[str]:
    """Liste tous les fichiers Parquet disponibles."""
    marts = get_marts_dir()
    if marts.exists():
        return sorted([f.name for f in marts.glob("*.parquet")])
    return []
