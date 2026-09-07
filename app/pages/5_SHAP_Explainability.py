import shap
import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title="Model Explainability", page_icon="🧠", layout="wide")

st.title("Model Explainability")
st.caption("Understand which factors influence delay predictions, both overall and for an individual prediction.")
st.info("**How to read this page:** SHAP values show how each feature changes the model's predicted delay. Positive values push the prediction higher, while negative values push it lower.")

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

with st.container(border=True):
    st.subheader("What influences the model most?")
    st.caption("These features have the largest average influence on predictions across the historical dataset.")

    importance_path = MODELS_DIR / "shap_importance_v1.csv"

    if importance_path.exists():
        importance = (pd.read_csv(importance_path).head(10).sort_values("mean_abs_shap", ascending=True))

        fig = px.bar(importance, x="mean_abs_shap", y="feature", orientation="h", labels={
            "mean_abs_shap": "Average SHAP Impact",
            "feature": "Feature"
        })

        fig.update_layout(height=300, margin=dict(l=5, r=10, t=5, b=5), xaxis_title="Average impact on predicted delay", yaxis_title=None, showlegend=False)

        fig.update_yaxes(tickfont=dict(size=10))
        fig.update_xaxes(tickfont=dict(size=9))

        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        st.caption("Longer bars indicate features that have a greater overall influence on the model's predictions.")

    else:
        st.warning("The SHAP importance file was not found. Please regenerate the saved SHAP results.")

    summary_png = MODELS_DIR / "shap_summary.png"

    if summary_png.exists():
        with st.expander("View technical SHAP summary"):
            st.caption("This technical view shows how feature values relate to their SHAP impact across the historical dataset.")
            img_col1, img_col2, img_col3 = st.columns([1,2,1])
            with img_col2:
                st.image(str(summary_png), width=600)

            st.caption("Each point represents a historical train-station-day record. The horizontal position shows whether a feature pushed the prediction lower or higher. Color represents the feature value.")
    else:
        st.info("The technical SHAP summary image is not available.")

with st.container(border=True):
    st.subheader("Why did this prediction happen?")
    if "last_prediction" not in st.session_state:
        st.info("No prediction is available yet. Go to **Delay Predictor**, generate a prediction, and return here to see the factors that influenced it.")
    else:
        pred = st.session_state["last_prediction"]
        st.caption("Explanation for the most recent prediction.")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Train", str(pred["train_no"]))
        col1.metric("Station", str(pred["station_code"]))
        col1.metric("Date", pred["date"])
        col1.metric("Predicted Delay", f"{pred['predicted_delay']:.0f} min")

        st.markdown(
            f"The model predicted approximately **{pred['predicted_delay']:.0f} minutes of delay** for **Train {pred['train_no']}** at **{pred['station_name']}**"
        )
        st.caption("The chart below shows which features moved the prediction away from the model's average starting point.")

        exp = pred["explanation"]

        ch1, ch2, ch3 = st.columns([1, 2, 1])

        with ch2:
            plt.figure(figsize=(5.5, 3.0), dpi=120)
            shap.plots.waterfall(exp, max_display=6, show=False)
            plt.tight_layout(pad=0.4)
            st.pyplot(plt.gcf(), clear_figure=True, width="stretch")

        st.caption("**Red:** increases the predicted delay • **Blue:** decreases the predicted delay • **Longer bars:** stronger influence")

        contrib = pd.DataFrame({
            "feature": exp.feature_names,
            "impact": exp.values
        })

        contrib["absolute_impact"] = (contrib["impact"].abs())

        top3 = contrib.sort_values("absolute_impact", ascending=False).head(3)

        st.markdown("### Biggest Influences")

        factor_cols = st.columns(3)

        for col, (_, row) in zip(factor_cols, top3.iterrows()):
            direction = ("increased" if row["impact"] > 0 else "decreased")

            with col:
                with st.container(border=True):
                    st.markdown(f"**{row['feature']}**")

                    st.metric(
                        "Impact",
                        f"{abs(row['impact']):.1f} min",
                        f"{'+' if row['impact'] > 0 else '-'}{direction.capitalize()}",
                        delta_color="normal"
                    )

        st.caption("These are the three features with the largest absolute SHAP values for this prediction. A larger value means a stronger contribution to the final prediction.")

        with st.expander("How the SHAP calculation works"):
            st.markdown("The model starts from it **avergae prediction** and then adds or subtracts the contribution of individual features. The combined contributions produce the final predicted delay")

            st.markdown("- **Positive SHAP value:** pushes the prediction higher.")
            st.markdown("- **Negative SHAP value:** pushes the prediction lower.")
            st.markdown("- **Largest absolute SHAP value:** stronger influence on this particular prediction.")