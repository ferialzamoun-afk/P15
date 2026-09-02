"""Module de chargement optimisé des données DuckDB et Parquet pour l'application Streamlit P15."""

from pathlib import Path
import duckdb
import pandas as pd
import streamlit as st

# Résolution ultra-robuste des chemins
POSSIBLE_MARTS_DIRS = [
    Path(__file__).resolve().parents[2] / "data" / "processed" / "marts",
    Path("C:/Users/feria/Documents/P15/data/processed/marts"),
    Path("data/processed/marts"),
    Path("../data/processed/marts"),
]

MARTS_DIR = next((d for d in POSSIBLE_MARTS_DIRS if d.exists()), POSSIBLE_MARTS_DIRS[0])


@st.cache_data(ttl=3600)
def load_parquet(file_name: str) -> pd.DataFrame:
    """Charge un fichier Parquet ou CSV depuis le dossier marts avec mise en cache."""
    stem = file_name.replace(".parquet", "").replace(".csv", "")
    
    for d in POSSIBLE_MARTS_DIRS:
        if not d.exists():
            continue
        p_file = d / f"{stem}.parquet"
        if p_file.exists():
            try:
                return pd.read_parquet(p_file)
            except Exception:
                try:
                    con = duckdb.connect()
                    df = con.execute(f"SELECT * FROM '{p_file.as_posix()}'").df()
                    con.close()
                    return df
                except Exception:
                    pass
        c_file = d / f"{stem}.csv"
        if c_file.exists():
            try:
                return pd.read_csv(c_file)
            except Exception:
                pass
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def execute_query(query: str) -> pd.DataFrame:
    """Exécute une requête SQL DuckDB sur les marts Parquet enregistrés comme tables."""
    try:
        con = duckdb.connect()
        for d in POSSIBLE_MARTS_DIRS:
            if d.exists():
                for p in d.glob("*.parquet"):
                    con.execute(f"CREATE OR REPLACE VIEW {p.stem} AS SELECT * FROM '{p.as_posix()}'")
                for c in d.glob("*.csv"):
                    con.execute(f"CREATE OR REPLACE VIEW {c.stem} AS SELECT * FROM '{c.as_posix()}'")
                break
        df = con.execute(query).df()
        con.close()
        return df
    except Exception as e:
        st.warning(f"Avertissement SQL : {e}")
        return pd.DataFrame()


def get_available_marts() -> list[str]:
    """Liste tous les fichiers Parquet disponibles."""
    if MARTS_DIR.exists():
        return sorted([f.name for f in MARTS_DIR.glob("*.parquet")])
    return []
