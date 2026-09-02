import warnings
import joblib
import pandas as pd

# Suppress serialization warning for clean output
warnings.filterwarnings("ignore")

# Load model and feature column names
model = joblib.load("models/delay_model_v1.pkl")
feature_columns = joblib.load("models/feature_columns_v1.pkl")

# Create a sample input matching the training schema exactly
sample = pd.DataFrame([{col: 0 for col in feature_columns}])

# Set example feature values
if "station_no" in sample.columns:
    sample["station_no"] = 5
if "is_monsoon" in sample.columns:
    sample["is_monsoon"] = 1

# Predict delay
pred = model.predict(sample)
print(f"Predicted delay: {pred[0]:.1f} min")
