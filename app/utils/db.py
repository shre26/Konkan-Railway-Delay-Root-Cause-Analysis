import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

@st.cache_resource
def get_engine():
    return create_engine(f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
                         f"@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}")

@st.cache_data(ttl=3600)
def run_query(query: str) -> pd.DataFrame:
    return pd.read_sql(query, get_engine())