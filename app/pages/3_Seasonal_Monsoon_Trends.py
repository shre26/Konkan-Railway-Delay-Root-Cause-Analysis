import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.db import run_query

st.set_page_config(page_title="Seasonal & Monsoon Trends", page_icon="🌧️", layout="wide")
st.title("🌧️ Seasonal & Monsoon Trends")
st.caption("Understanding how season, rainfall intensity, day of week, and station location influence delays on the Konkan corridor.")
st.info("Key finding: monsoon season alone has little impact on delays. The stronger patterns come from extreme rainfall, day of week, and specific station bottlenecks.")

WEEK2_STATS = {
    "monsoon_mean": 41.65,
    "non_monsoon_mean": 42.44,
    "mean_gap_min": -0.79,
    "t_stat": -3.077,
    "p-value": 0.002,
    "cohens_d": -0.016,
    "sample_size": 174988,
    "station_anova_f": 3.630,
    "station_anova_p": 0.0058,
    "dow_anova_f": 70.262,
    "dow_anova_p": 0.001,
    "rainfall_pearson_r": 0.070,
    "rainfall_spearman_r": 0.058,
    "rainfall_anova_f": 190.076,
    "rainfall_anova_p": 0.001,
    "very_heavy_rain_delay": 65.71,
    "very_heavy_rain_increase": 27.3,
}

BOTTLENECK_STATIONS = ["NIV", "ANO", "VRLI", "KKW", "KRMI"]

monsoon_split = run_query("""
    SELECT is_monsoon, AVG(delay_minutes) As avg_delay, COUNT(*) AS n
    FROM delays
    GROUP BY is_monsoon
""")

monsoon_avg = monsoon_split.loc[monsoon_split["is_monsoon"] == 1, "avg_delay"].iloc[0]

non_monsoon_avg = monsoon_split.loc[monsoon_split["is_monsoon"] == 0, "avg_delay"].iloc[0]

difference = monsoon_avg - non_monsoon_avg

col1, col2, col3 = st.columns(3)

col1.metric(
    "Monsoon Average Delay",
    f"{monsoon_avg:.1f} min"
)
col2.metric(
    "Non-Monsoon Average Delay",
    f"{non_monsoon_avg:.1f} min",
)
col3.metric(
    "Seasonal Difference",
    f"{abs(difference):.1f} min",
    "minimal difference",
    "orange"
)

st.divider()

with st.container(border=True):
    st.subheader("Does the monsoon season itself cause delays?")
    st.markdown(
        f"""
        **Not significantly in operational terms.** Trains average **{monsoon_avg:.1f} minutes** of delay during monsoon months compared with **{non_monsoon_avg:.1f} minutes** during the rest of the year.

        The difference is less than a minute, suggesting that normal monsoon conditions alone do not meaningfully increase delays.
        """
    )

    with st.expander("Statistical evidence"):
        st.markdown(
            f"""
            - Welch's t-test: **t = {WEEK2_STATS['t_stat']}**, **p = {WEEK2_STATS['p-value']}**
            - Cohen's d: **{WEEK2_STATS['cohens_d']}** - negligible effect
            - Sample size: **{WEEK2_STATS['sample_size']} records**

            Although the p-value indicates statistical significance, the effect size shows that the actual difference is operationally negligible. With a dataset of this size, even very small difference can become statistically significant.
            """
        )

trend = run_query("""
    SELECT 
        DATE_FORMAT(record_date, '%Y-%m') AS month,
        AVG(delay_minutes) As avg_delay,
        MAX(is_monsoon) AS is_monsoon
    FROM delays
    GROUP BY DATE_FORMAT(record_date, '%Y-%m')
    ORDER BY DATE_FORMAT(record_date, '%Y-%m')
""")

with st.container(border=True):
    st.subheader("Monthly Delay Trend")
    st.caption("Average delay by month. Shaded regions indicate monsoon months.")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trend['month'],
            y=trend['avg_delay'],
            mode="lines+markers",
            name="Average Delay",
            line=dict(width=3, color="#327BC8")
        )
    )

    monsoon_indices = trend.index[trend["is_monsoon"] == 1].tolist()

    if monsoon_indices:
        groups = []
        current = [monsoon_indices[0]]

        for i in range(1, len(monsoon_indices)):
            if monsoon_indices[i] == monsoon_indices[i-1] + 1:
                current.append(monsoon_indices[i])
            else:
                groups.append(current)
                current = [monsoon_indices[i]]
        groups.append(current)

        for group in groups:
            fig.add_vrect(
                x0=trend.loc[group[0], "month"],
                x1=trend.loc[group[-1], "month"],
                fillcolor="yellow",
                opacity=0.10,
                line_width=0,
            )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Average Delau (minutes)",
        height=400,
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, width='stretch')

with st.container(border=True):
    st.subheader("Rainfall matters mainly when it becomes severe")
    st.markdown(
        f"""
        **Extreme rainfall is different from ordinary rainy weather.**
        Typical rainy days show little change in delay, while very heavy rainfall is associated with a sharp increase.

        Very-heavy-rain days average **{WEEK2_STATS['very_heavy_rain_delay']:.1f} minutes** of delay - approximately **{WEEK2_STATS['very_heavy_rain_increase']:.1f} minutes higher** than normal conditions.
        """
    )

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Typical Rainy Day",
        "~38-40 min",
        "similar to dry days"
    )
    col2.metric(
        "Very Heavy Rain",
        f"{WEEK2_STATS['very_heavy_rain_delay']:.1f} min",
        f"+{WEEK2_STATS['very_heavy_rain_increase']:.0f} min"
    )
    col3.metric(
        "Relationship",
        "Threshold effect",
        "not gradual",
        "red"
    )

    st.warning("Very heavy rainfall is associated with a sharp increase in delays, while light-to heavy rainfall levels remain comparatively stable")

    with st.expander("Statistical evidence"):
        st.markdown(
            f"""
            - Pearson correlation: **r = {WEEK2_STATS['rainfall_pearson_r']:.3f}**
            - Spearman correlation: **r = {WEEK2_STATS['rainfall_spearman_r']:.3f}**
            - Rainfall-category ANOVA: **F = {WEEK2_STATS['rainfall_anova_f']:.1f}**
            - ANOVA significance: **p < 0.001**

            The weak correlation coefficients and strong category-level significance are consistent with a threshold effect: delays remain relatively stable until rainfall becomes extreme, after which they increase sharply.
            """
        )

dow = run_query("""
    SELECT day_of_week, AVG(delay_minutes) AS avg_delay
    FROM delays
    GROUP BY day_of_week
""")

dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

dow["day_of_week"] = pd.Categorical(dow["day_of_week"], categories=dow_order, ordered=True)

dow = dow.sort_values("day_of_week")

highest_day = dow.loc[dow["avg_delay"].idxmax()]
lowest_day = dow.loc[dow["avg_delay"].idxmin()]

with st.container(border=True):
    st.subheader("Day of Week Has a Stronger Pattern")
    st.markdown(
        f"""
        The day on which a train operates shows a clearer difference in average delay than the broad monsoon/ non-monsoon split.

        **{highest_day['day_of_week']}** has the highest average delay at
        **{highest_day['avg_delay']} minutes**, while
        **{lowest_day['day_of_week']}** has the lowest at
        **{lowest_day['avg_delay']} minutes**.
        """
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Highest Average Delay",
        str(highest_day["day_of_week"]),
        f"{highest_day['avg_delay']:.1f} min"
    )
    col2.metric(
        "Lowest Average Delay",
        str(lowest_day["day_of_week"]),
        f"{lowest_day['avg_delay']:.1f} min"
    )

    st.bar_chart(dow.set_index("day_of_week")["avg_delay"], width='stretch')

    with st.expander("Statistical evidence"):
        st.markdown(
            f"""
            One-way ANOVA across all seven days:

            **F = {WEEK2_STATS['dow_anova_f']:.1f}, p < 0.001**

            This indicates a statistically significant difference in average delay across days of the week.
            """
        )

with st.container(border=True):
    st.subheader("Station-Level Bottlenecks")
    st.markdown(
        """
        Delay patterns also vary significantly by station. A small group of stations consistently records substantially higher delays than the corridor average, suggesting localized operational or infrastructure bottlenecks.
        """
    )

    st.markdown(
        "**Flagged bottleneck stations:** " + " • ".join(f"`{station}`" for station in BOTTLENECK_STATIONS)
    )

    with st.expander("Statistical evidence"):
        st.markdown(
            f"""
            - Statistical AVOVA: **F = {WEEK2_STATS['station_anova_f']:.3f}**
            - Significance: **p = {WEEK2_STATS['station_anova_p']:.4f}**
            - Bottleneck stations: approximately **60-67 min average delay**

            These results indicate meaningful variation between stations rather then a uniform corridor-wide delay pattern.
            """
        )

st.divider()

with st.container(border=True):
    st.subheader("Overall Takeaway")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            **What matters less**

            - Monsoon season by itself
            - Ordinary rainfall
            - A broad seasonal classification
        """)

    with col2:
        st.markdown("""
            **What matters more**

            - Extreme rainfall
            - Day of week
            - Specific station locations
        """)

    st.success("Delays are better explained by specific operating conditions and locations than by simply classifying a day as monsoon or non-monsoon.")