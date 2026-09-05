import pandas as pd
import streamlit as st
import plotly.express as px
from utils.db import run_query, run_query_params

st.set_page_config(page_title="Route & Station Explorer", page_icon="🔍", layout="wide")
st.title("🔍 Route & Station Explorer")
st.caption("Explore train and station delay patterns across the Konkan Railway corridor.")
st.info("Select a train or station to view delay statistics, monthly trends, " "and route-level performance.")

def summary_cards(stats: pd.DataFrame):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Average Delay",
        f"{stats['avg_delay'].iloc[0]:.1f} min"
    )
    col2.metric(
        "Median Delay",
        f"{stats['median_delay'].iloc[0]:.1f} min"
    )
    col3.metric(
        "Maximum Delay",
        f"{stats['max_delay'].iloc[0]:.0f} min"
    )
    col4.metric(
        "Observations",
        f"{int(stats['n'].iloc[0]):,}"
    )

tab_train, tab_station = st.tabs(["🚆 Explore by Train", "📍 Explore by Station"])

with tab_train:
    trains_df = run_query("""
        SELECT train_no, train_name, coverage_tier
        FROM trains
        ORDER BY train_no
    """)
    trains_df["label"] = (trains_df["train_no"].astype(str) + " - " + trains_df['train_name'])

    with st.container(border=True):
        st.subheader("Select Train")
        selected_label = st.selectbox("Train", trains_df["label"], key="train_select", label_visibility="collapsed")
    row = trains_df.loc[trains_df["label"] == selected_label].iloc[0]
    selected_train = int(row["train_no"])
    selected_train_name = row["train_name"]

    if row["coverage_tier"] == "Low":
        st.warning("⚠️ Limited data coverage for this train (<150 days). "
                   "Trend results should be treated as indicative.")

    stats = run_query_params("""
        SELECT
            AVG(delay_minutes) AS avg_delay,
            MAX(delay_minutes) AS max_delay,
            COUNT(*) AS n
        FROM delays
        WHERE train_no = :train_no
    """, {"train_no": selected_train})

    raw = run_query_params("""
        SELECT delay_minutes
        FROM delays
        WHERE train_no = :train_no
    """, {"train_no": selected_train})

    stats["median_delay"] = raw["delay_minutes"].median()

    st.subheader(f"{selected_train_name}")
    st.caption(f"Train {selected_train}")

    summary_cards(stats)

    st.write("")

    trend = run_query_params("""
        SELECT
            DATE_FORMAT(record_date, '%Y-%m') AS month,
            AVG(delay_minutes) AS avg_delay
        FROM delays
        WHERE train_no = :train_no
        GROUP BY DATE_FORMAT(record_date, '%Y-%m')
        ORDER BY DATE_FORMAT(record_date, '%Y-%m')
    """, {"train_no": selected_train})

    with st.container(border=True):
        st.subheader("📈 Monthly Delay Trend")
        st.caption("Average dealy recorded for each month.")
        st.line_chart(trend.set_index("month")["avg_delay"], width='stretch')

    station_breakdown = run_query_params("""
        SELECT 
            d.station_code,
            s.station_full_name,
            AVG(d.delay_minutes) AS avg_delay,
            MIN(d.station_no) AS route_order
        FROM delays d
        JOIN stations s ON d.station_code = s.station_code
        WHERE d.train_no = :train_no
        GROUP BY d.station_code, s.station_full_name
        ORDER BY route_order
    """, {"train_no": selected_train})

    station_order = station_breakdown.sort_values("route_order")

    with st.container(border=True):
        st.subheader("📍 Delay Across Route Stops")
        st.caption("Average delay at each station following the train's route order.")
        fig = px.bar(
            station_breakdown,
            x="station_full_name",
            y="avg_delay",
            labels={
                "station_full_name": "Station",
                "avg_delay": "Average Delay (minutes)"
            }
        )
        fig.update_layout(
            xaxis={
                "categoryorder": "array",
                "categoryarray": station_order,
                "tickangle": -45
            },
            yaxis_title="Average Delay (minutes)",
            xaxis_title="Station",
            height=500
        )
        st.plotly_chart(fig, width='stretch')

with tab_station:
    stations_df = run_query("""
        SELECT DISTINCT d.station_code, s.station_full_name
        FROM delays d
        JOIN stations s ON d.station_code = s.station_code
        ORDER BY s.station_full_name
    """)

    stations_df["label"] = (stations_df["station_full_name"] + " (" + stations_df["station_code"] + ")")

    with st.container(border=True):
        st.subheader("📍 Select Station")

        selected_label = st.selectbox(
            "Station",
            stations_df["label"],
            key="station_select",
            label_visibility="collapsed"
        )

    selected_station = stations_df.loc[stations_df["label"] == selected_label, "station_code"].iloc[0]

    selected_station_name = stations_df.loc[stations_df["label"] == selected_label, "station_full_name"].iloc[0]

    stats = run_query_params("""
        SELECT 
            AVG(delay_minutes) AS avg_delay,
            MAX(delay_minutes) AS max_delay,
            COUNT(*) AS n
        FROM delays
        WHERE station_code = :station_code
    """, {"station_code": selected_station})

    raw = run_query_params("""
        SELECT delay_minutes
        FROM delays
        WHERE station_code = :station_code
    """, {"station_code": selected_station})

    stats["median_delay"] = raw["delay_minutes"].median()

    st.subheader(selected_station_name)
    st.caption(f"Station code: {selected_station}")

    summary_cards(stats)

    st.write("")

    trend = run_query_params("""
        SELECT
            DATE_FORMAT(record_date, '%Y-%m') AS month,
            AVG(delay_minutes) AS avg_delay
        FROM delays
        WHERE station_code = :station_code
        GROUP BY DATE_FORMAT(record_date, '%Y-%m')
        ORDER BY DATE_FORMAT(record_date, '%Y-%m')
    """, {"station_code": selected_station})

    with st.container(border=True):
        st.subheader("📈 Monthly Delay Trend")
        st.caption("Average station delay recorded for each month.")
        st.line_chart(trend.set_index("month")["avg_delay"], width='stretch')

    train_breakdown = run_query_params("""
        SELECT
            d.train_no,
            t.train_name,
            AVG(d.delay_minutes) AS avg_delay
        FROM delays d
        JOIN trains t ON d.train_no = t.train_no
        WHERE d.station_code = :station_code
        GROUP BY d.train_no, t.train_name
        HAVING COUNT(*) > 30
        ORDER BY avg_delay DESC
        LIMIT 10
    """, {"station_code": selected_station})

    train_breakdown["label"] = (train_breakdown["train_no"].astype(str) + " - " + train_breakdown["train_name"])

    with st.container(border=True):
        st.subheader("🚆 Most Delayed Trains at This Station")
        st.caption("Top 10 trains ranked by their average delay at this station.")
        st.bar_chart(train_breakdown.set_index("label")["avg_delay"], width='stretch')