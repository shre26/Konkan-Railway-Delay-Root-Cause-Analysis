import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.db import run_query

st.set_page_config(page_title="Overview", page_icon="📋", layout="wide")

st.title("Dataset Overview")
st.caption("Understand the scale of the dataset, typical delay behaviour, and where delays are most concentrated.")

with st.container(border=True):
    st.subheader("About this analysis")
    st.markdown("""
        This project analyzes real per-station delay data for **48 Konkan Railway trains**, covering the corridor from Mumbai (CSMT / Panvel / Bandra Terminus) to Madgaon, Goa.

        The analysis examines whether delays are associated with **season, rainfall, day of week, or individual stations**, and uses these historical patterns to support delay prediction.
    """)

    st.caption("Dataset period: 8 February 2025 - 7 February 2026")

scale = run_query("""
    SELECT 
        COUNT(*) AS total_records,
        COUNT(DISTINCT train_no) AS n_trains,
        COUNT(DISTINCT station_code) AS n_stations,
        MIN(record_date) AS start_date,
        MAX(record_date) AS end_date
    FROM delays
""").iloc[0]

st.subheader("Dataset at a glance")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Records", f"{scale['total_records']:,}")
col2.metric("Trains", f"{scale['n_trains']:,}")
col3.metric("Stations", f"{scale['n_stations']:,}")
col4.metric(
    "Coverage",
    "1 year",
    f"{scale['start_date']} → {scale['end_date']}"
)

st.write("")

with st.container(border=True):
    st.subheader("What does a typical delay look like?")
    st.caption("Distribution of recorded delays across all trains and stations.")

    delay_raw = run_query("""
        SELECT delay_minutes FROM delays
    """)["delay_minutes"].dropna()

    mean_d = delay_raw.mean()
    median_d = delay_raw.median()
    std_d = delay_raw.std()
    max_d = delay_raw.max()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Median Delay", f"{median_d:.0f} min")
    col2.metric("Average Delay", f"{mean_d:.0f} min")
    col3.metric("Standard Deviation", f"{std_d:.0f} min")
    col4.metric("Longest Recorded", f"{max_d:.0f} min")

    st.markdown(f"The median delay is **{median_d:.0f} minutes**, while the average is **{mean_d:.0f} minutes**. The higher average suggests that a smaller number of severe delays pull the overall mean upward.")

    histogram_data = delay_raw[delay_raw <= 180]
    fig = px.histogram(x=histogram_data, nbins=32, labels={
        "x": "Delay (minutes)",
        "count": "Number of records"
    })

    fig.update_traces(marker_line_width=0.5, opacity=0.85, hovertemplate=(
        "<b>Delay range</b>: %{x}<br>"
        "<b>Records</b>: %{y:,}"
        "<extra></extra>"
    ))

    fig.add_vline(x=median_d, line_dash="dash", line_width=2, annotation_text=f"Median: {median_d:.0f}", annotation_position="top")

    fig.update_layout(
         height=330, margin=dict(l=10, r=10, t=35, b=10), bargap=0.04, showlegend=False, hoverlabel=dict(font_size=12)
    )

    fig.update_xaxes(title="Delay (minutes)", showgrid=False)
    fig.update_yaxes(title="Number of records", gridcolor="rgba(128,128,128,0.15)")

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    
    st.caption("Dashed line = median delay • Dotted line = average delay. The visualization is limited to 180 minutes so extreme values do not compress the main distribution.")

st.write("")

st.subheader("Where are delays concentrated?")
st.caption("Compare the trains and stations with the highest average recorded delays.")

left, right = st.columns(2)

with left:
    with st.container(border=True):
        st.subheader("Most Delayed Trains")
        st.caption("Top 10 trains by average delay, using only trains with more than 20 observations.")

        top_trains = run_query("""
            SELECT d.train_no, t.train_name, t.coverage_tier, AVG(d.delay_minutes) AS avg_delay, COUNT(*) AS n
            FROM delays d
            JOIN trains t ON d.train_no = t.train_no
            GROUP BY d.train_no, t.train_name, t.coverage_tier
            HAVING COUNT(*) > 30
            ORDER BY avg_delay DESC LIMIT 10
        """)

        if not top_trains.empty:
            top_trains["label"] = (
                top_trains["train_no"].astype(str)
                + " - " + top_trains["train_name"]
            )

            top_trains["coverage_label"] = (
                top_trains["coverage_tier"]
                .fillna("Unknown")
                .astype(str)
            )

            top_trains = top_trains.sort_values("avg_delay", ascending=True)

            fig_t = go.Figure()

            fig_t.add_trace(go.Bar(
                x=top_trains["avg_delay"],
                y=top_trains["label"],
                orientation="h",
                text=[f"{value:.1f} min" for value in top_trains["avg_delay"]],
                textposition="outside",
                customdata=np.stack((top_trains["coverage_label"], top_trains["n"]), axis=-1),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Average delay: %{x:.1f} min<br>"
                    "Coverage: %{customdata[0]}<br>"
                    "Records: %{customdata[1]:,}"
                    "<extra></extra>"
                )
            ))

            fig_t.update_layout(height=340, margin=dict(l=5, r=65, t=5, b=10), showlegend=False)

            fig_t.update_xaxes(
                title="Average delay (minutes)",
                showgrid=True,
                gridcolor="rgba(128,128,128,0.15)",
                zeroline=False
            )

            fig_t.update_yaxes(title=None, tickfont=dict(size=10))

            st.plotly_chart(fig_t, width="stretch", config={"displayModeBar":False})

            worst_train = top_trains.iloc[-1]

            st.info(f"**Train {worst_train['train_no']} - {worst_train['train_name']}** has the highest average delay in this ranking at approximately **{worst_train['avg_delay']:.1f} minutes**.")

            if(top_trains["coverage_tier"].eq("Low").any()):
                st.caption("Some trains in this ranking have Low historical coverage. Hover over a bar to vire its coverage level and number of observations.")
        else:
            st.info("No train ranking data is currently available.")

with right:
    with st.container(border=True):
        st.subheader("Most Delayed Stations")
        st.caption("Top 10 stations by average delay across trains passing through the station.")

        top_stations = run_query("""
            SELECT s.station_code, s.station_full_name, AVG(d.delay_minutes) AS avg_delay, COUNT(*) AS n
            FROM delays d
            JOIN stations s ON d.station_code = s.station_code
            GROUP BY s.station_code, s.station_full_name
            HAVING COUNT(*) > 30
            ORDER BY avg_delay DESC LIMIT 10
        """)

        if not top_stations.empty:
            top_stations = top_stations.sort_values("avg_delay", ascending=True)

            fig_s = go.Figure()

            for _, row in top_stations.iterrows():
                fig_s.add_trace(go.Scatter(
                    x=[0, row["avg_delay"]],
                    y=[row["station_full_name"], row["station_full_name"]],
                    mode="lines",
                    line=dict(width=3),
                    hoverinfo="skip",
                    showlegend=False
                ))

            fig_s.add_trace(go.Scatter(
                x=top_stations["avg_delay"],
                y=top_stations["station_full_name"],
                mode="markers+text",
                marker=dict(size=12),
                text=[f"{value:.1f}" for value in top_stations["avg_delay"]],
                textposition="middle right",
                customdata=np.stack((top_stations["station_code"], top_stations["n"]), axis=-1),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Station code: %{customdata[0]}<br>"
                    "Records: %{customdata[1]:,}"
                    "<extra></extra>"
                ),
                showlegend=False
            ))

            fig_s.update_layout(height=340, margin=dict(l=5, r=55, t=5, b=10), showlegend=False)

            fig_s.update_xaxes(
                title="Average delay (minutes)",
                gridcolor="rgba(128,128,128,0.15)",
                zeroline=False
            )

            fig_s.update_yaxes(title=None, tickfont=dict(size=10))

            st.plotly_chart(fig_s, width="stretch", config={"displayModeBar": False})

            worst_station = top_stations.iloc[-1]

            st.info(f"**{worst_station['station_full_name']} ({worst_station['station_code']})** has the highest average delay in this ranking at approximately **{worst_station['avg_delay']:.1f} minutes**.")

            st.caption("The line shows the magnitude of the average delay and the endpoint marks the station's value. Hover over a point for station code and observation count.")

        else:
            st.info("No station ranking data is currently available.")

st.write("")

with st.container(border=True):
    st.subheader("Data quality and preparation")
    st.caption("Key decisions made before performing the statistical analysis and training the prediction model.")

    left_quality, right_quality = st.columns(2)

    with left_quality:
        st.markdown("#### Excluded or removed")
        st.markdown("""
            **5 stations excluded**

            KDV, KARD, NVRD, KCVLA and BDMJ had severe missing-data problems and were excluded from the analysis.

            **Remaining missing records removed**

            Missing delay observations were dropped rather than replaced with artificially estimated values.
        """)

    with right_quality:
        st.markdown("#### Retained and monitored")
        st.markdown("""
            **Extreme delays retained**

            Delays above 1000 minutes remain in the dataset because they may represent genuine disruption events.

            **Train coverage monitored**

            High, Medium and Low coverage tiers indicate how much historical information is available for each train.
        """)

    with st.expander("View detailed data-cleaning methodology"):
        st.markdown("""
            ### Excluded stations

            Five stations were removed because approximately **93-99%** of their delay observations were missing. This pattern was treated as a systematic data-collection problem rather than ordinary random missingness.

            ### Remaining missing values

            Approximately **2%** of the remaining records contained missing values. These observations were dropped rather than imputed because estimated delay values could introduce artificial relationships into the root-cause analysis.

            ### Coverage tiers

            Trains are classified as **High, Medium, or Low coverage** according to the amount of historical data available.

            Rankings involving low-coverage trains should therefore be interpreted more cautiously than those based on trains with substantially more observations.
        """)

        st.warning("Lower data coverage does not automatically mean a train is more or less delayed. It means the estimated average is based on fewer oobservations and may therefore be less stable.")