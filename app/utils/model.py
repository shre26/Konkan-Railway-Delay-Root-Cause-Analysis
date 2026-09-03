from pathlib import Path
import joblib
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"

@st.cache_resource
def load_model():
    return joblib.load(MODELS_DIR / "delay_model_v1.pkl")

@st.cache_resource
def load_feature_columns():
    return joblib.load(MODELS_DIR / "feature_columns_v1.pkl")

@st.cache_resource
def load_shap_explainer():
    return joblib.load(MODELS_DIR / "shap_explainer_v1.pkl")