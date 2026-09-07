import pandas as pd
import streamlit as st
from datetime import date
from utils.db import run_query, run_query_params
from utils.model import load_model, load_feature_columns, build_feature_vector, explain_prediction
from utils.model import load_shap_explainer

st.set_page_config(page_title="Delay Predictor", page_icon="🔮", layout="wide")
st.title("🔮 Delay Predictor")
st.caption("Predict expected delay for a train at a station, based on the trained model.")
st.info("This is a statistical estimate from the historical patterns - not a live running-status feed. Actual delays on the day can differ.")

try:
    model = load_model()
    feature_columns = load_feature_columns()
except Exception as e:
    st.error("Unable to load the prediction model. Please contact the administrator.")
    st.stop()

trains_df = run_query("SELECT train_no, train_name, coverage_tier FROM trains ORDER BY train_no")
if trains_df.empty:
    st.error("No train data is currently available.")
    st.stop()
trains_df["label"] = trains_df["train_no"].astype(str) + " - " + trains_df["train_name"]

# select the train
with st.container(border=True):
    st.subheader("Select Train")
    train_label = st.selectbox("Train", trains_df["label"], label_visibility="collapsed")
    selected_train = int(trains_df.loc[trains_df["label"] == train_label, "train_no"].iloc[0])

    coverage = trains_df.loc[trains_df["train_no"] == selected_train, "coverage_tier"].iloc[0]
    if coverage == "Low":
        st.warning("⚠️ This train has limited historical data (<150 days) - treat the prediction as a rough estimate.")

# select the station of selected train's route
route_df = run_query_params("""
    SELECT sch.station_no, sch.station_code, st.station_full_name, st.station_zone
    FROM schedule sch
    JOIN stations st ON sch.station_code = st.station_code
    WHERE sch.train_no = :train_no
    ORDER BY sch.distance_from_origin
""", {"train_no": selected_train})

if route_df.empty:
    st.error("No route data found for this train. Try a different train.")
    st.stop()

route_df["station_full_name"] = route_df["station_full_name"].fillna(
    route_df["station_code"]
)

route_df["label"] = route_df["station_full_name"].astype(str) + " (" + route_df["station_code"].astype(str) + ")"

with st.container(border=True):
    st.subheader("Select Station")
    st.caption("Only stations on this train's actual route are shown.")
    station_label = st.selectbox("Station", route_df["label"], label_visibility="collapsed")
    station_row = route_df.loc[route_df["label"] == station_label].iloc[0]

# pick the date of travel
with st.container(border=True):
    st.subheader("Select Date")
    selected_date = st.date_input("Travel Date", value=date.today(), label_visibility="collapsed")

    month = selected_date.month
    day_of_week = selected_date.strftime("%A")
    is_monsoon = 1 if month in (6, 7, 8, 9) else 0

    st.caption(f"Day: **{day_of_week}** • Month: **{selected_date.strftime('%B')}** • Monsoon period: **{'Yes' if is_monsoon else 'No'}**" )

# select level of expected rainfall
with st.container(border=True):
    st.subheader("Expected Rainfall")
    st.caption("No live forecast integration yet - pick the closest expected condition.")
    rain_category = st.select_slider("Rainfall", options=["No rain", "Light", "Moderate", "Heavy", "Very heavy"], value="No rain", label_visibility="collapsed")
    if rain_category == "Very heavy":
        st.warning("⚠️ Very heavy rainfall historically causes a sharp jump in delays - see Seasonal Trends page.")

st.write("")

with st.container(border=True):
    st.markdown("### Selected Journey")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Train", str(selected_train))
    col2.metric("Station", str(station_row["station_code"]))
    col3.metric("Date", selected_date.strftime("%d %b %Y"))
    col4.metric("Rainfall", rain_category)


st.write("")

# predict the delay
if st.button("🔮 Predict Delay", type="primary", width="stretch"):
    X_input = build_feature_vector(feature_columns, station_no=int(station_row["station_no"]), month=month, is_monsoon=is_monsoon, station_code=station_row["station_code"], train_no=selected_train, day_of_week=day_of_week, rain_category=rain_category, station_zone=station_row["station_zone"])

    predicted_delay = float(model.predict(X_input)[0])
    predicted_delay = max(predicted_delay, 0)

    explainer = load_shap_explainer()
    explanation = explain_prediction(explainer, X_input)

    st.session_state["last_prediction"] = {
        "explanation": explanation,
        "predicted_delay": predicted_delay,
        "train_no": selected_train,
        "station_name": station_row["station_full_name"],
        "station_code": station_row["station_code"],
        "date": selected_date.strftime("%d %b %Y"),
        "rain_category": rain_category,
    }

    st.write("")
    with st.container(border=True):
        st.metric("Predicted delay", f"{predicted_delay:.0f} min")
        if predicted_delay < 15:
            st.success(f"Train {selected_train} is expected to be approximately on time at {station_row['station_full_name']}.")
        elif predicted_delay < 60:
            st.warning(f"Train {selected_train} is predicted to be about {predicted_delay:.0f} minutes late at {station_row['station_full_name']}.")
        else:
            st.error(f"Train {selected_train} is predicted to be about {predicted_delay:.0f} minutes late at {station_row['station_full_name']}.")

        st.caption("Model: XGBoost - based on historical patterns for this train, station, day, season, and rainfall condition. Not a live prediction.")