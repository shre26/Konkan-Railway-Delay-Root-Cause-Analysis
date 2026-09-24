import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

def _get_credential(key: str) -> str:
    if key in st.secrets:
        return st.secrets[key]
    return os.getenv(key)

@st.cache_resource
def get_engine():
    ssl_ca_path = PROJECT_ROOT / "db" / "aiven-ca.pem"
    return create_engine(
        f"mysql+mysqlconnector://{_get_credential('DB_USER')}:{_get_credential('DB_PASSWORD')}"
        f"@{_get_credential('DB_HOST')}:{_get_credential('DB_PORT')}/{_get_credential('DB_NAME')}"
        f"?ssl_ca={ssl_ca_path}"
    )

@st.cache_data(ttl=3600)
def run_query(query: str) -> pd.DataFrame:
    return pd.read_sql(query, get_engine())

@st.cache_data(ttl=3600)
def run_query_params(query: str, params: dict) -> pd.DataFrame:
    return pd.read_sql(text(query), get_engine(), params=params)