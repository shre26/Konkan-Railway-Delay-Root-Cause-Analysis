import pandas as pd
import streamlit as st
from utils.db import run_query

st.set_page_config(page_title="Konkan Railway Delay Analysis", layout="wide")
st.title("🚆 Konkan Railway Delay Analysis")
st.caption("Root-cause analysis of delays on the Konkan corridor - Feb 2025 to Feb 2026")
st.info("Explore delay patterns across trains, stations and seasonal conditions ""on the Konkan Railway corridor.")

avg_delay = run_query("SELECT AVG(delay_minutes) AS avg_delay FROM delays")["avg_delay"].iloc[0]

worst_train = run_query("""
    SELECT d.train_no, t.train_name, AVG(d.delay_minutes) AS avg_delay, COUNT(*) AS n
    FROM delays d JOIN trains t ON d.train_no = t.train_no
    GROUP BY d.train_no, t.train_name
    HAVING COUNT(*) > 30
    ORDER BY avg_delay DESC LIMIT 1
""")

worst_station = run_query("""
    SELECT d.station_code, s.station_full_name, AVG(d.delay_minutes) AS avg_delay
    FROM delays d JOIN stations s ON d.station_code = s.station_code
    GROUP BY d.station_code, s.station_full_name
    ORDER BY avg_delay DESC LIMIT 1
""")

monsoon_split = run_query("""
    SELECT is_monsoon, AVG(delay_minutes) AS avg_delay
    FROM delays GROUP BY is_monsoon
""")
monsoon_avg = monsoon_split.loc[monsoon_split["is_monsoon"] == 1, "avg_delay"].iloc[0]
non_monsoon_avg = monsoon_split.loc[monsoon_split["is_monsoon"] == 0, "avg_delay"].iloc[0]

# cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Overall Avg Delay", f"{avg_delay:.1f} min")
col2.metric(
    "Most Delayed Train",
    str(worst_train["train_name"].iloc[0]),
    f"Train {worst_train["train_no"].iloc[0]} • {worst_train['avg_delay'].iloc[0]:.1f} min avg",
)
col3.metric(
    "Most Delayed Station",
    str(worst_station["station_full_name"].iloc[0]),
    f"{worst_station['avg_delay'].iloc[0]:.1f} min avg",
)
col4.metric(
    "Monsoon Avg Delay",
    f"{monsoon_avg:.1f} min",
    f"{monsoon_avg - non_monsoon_avg:+.1f} min vs non-monsoon",
)

dist_data = run_query("""
    SELECT
        CASE
            WHEN delay_minutes < 0 THEN 'Early'
            WHEN delay_minutes < 15 THEN 'On time (0-15)'
            WHEN delay_minutes < 30 THEN '15-30 min'
            WHEN delay_minutes < 60 THEN '30-60 min'
            WHEN delay_minutes < 120 THEN '1-2 hr'
            WHEN delay_minutes < 300 THEN '2-5 hr'
            ELSE '5+ hr'
        END AS delay_bucket,
        COUNT(*) AS n
    FROM delays
    GROUP BY delay_bucket
""")
order = ["Early", "On time (0-15)", "15-30 min", "30-60 min", "1-2 hr", "2-5 hr", "5+ hr"]
dist_data["delay_bucket"] = dist_data["delay_bucket"].astype(pd.CategoricalDtype(categories=order, ordered=True))
dist_data = dist_data.sort_values("delay_bucket")

left, right = st.columns([3, 2])

with left:
    with st.container(border=True):
        st.subheader("Delay Distribution")
        st.bar_chart(dist_data.set_index("delay_bucket")["n"], width='stretch')

with right:
    with st.container(border=True):
        st.subheader("Seasonal Impact")
        season_df = pd.DataFrame({
            "Season": ["Monsoon", "Non-Monsoon"],
            "Average Delay": [monsoon_avg, non_monsoon_avg]
        })
        st.bar_chart(season_df.set_index("Season"), width='stretch')