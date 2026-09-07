from pathlib import Path
import shap
import joblib
import pandas as pd
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

# builds a single-row DataFrame matching the model's training schema
def build_feature_vector(feature_columns, *, station_no, month, is_monsoon, station_code, train_no, day_of_week, rain_category, station_zone):
    row = {col: 0 for col in feature_columns}

    for name, value in [("station_no", station_no), ("month", month), ("is_monsoon", is_monsoon)]:
        if name in row:
            row[name] = value

    categorical_inputs = {
        "station_code": station_code,
        "train_no": train_no,
        "day_of_week": day_of_week,
        "rain_category": rain_category,
        "station_zone": station_zone,
    }

    for prefix, value in categorical_inputs.items():
        dummy_col = f"{prefix}_{value}"
        if dummy_col in row:
            row[dummy_col] = 1

    return pd.DataFrame([row])[feature_columns]

def explain_prediction(explainer, X_input):
    shap_values = explainer.shap_values(X_input)
    return shap.Explanation(
        values=shap_values[0],
        base_values=explainer.expected_value,
        data=X_input.iloc[0],
        feature_names=X_input.columns.tolist(),
    )