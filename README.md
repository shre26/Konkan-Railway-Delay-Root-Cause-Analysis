# Konkan Railway Delay Root-Cause Analysis

Statistical analysis of station-wise train delays on the Konkan Railway corridor (Mumbai to Mangalore), covering one year of data from February 2025 to February 2026. Includes exploratory analysis, hypothesis testing, an XGBoost prediction model with SHAP explainability, and a multi-page Streamlit dashboard backed by a MySQL database.

**Live app:** https://konkan-railway-delay-root-cause-analysis.streamlit.app/

## Project Structure

```
.
├── app/
│   ├── Home.py                          # Streamlit entry point
│   ├── pages/
│   │   ├── 1_Overview.py                # Dataset overview and delay distribution
│   │   ├── 2_Route_Station_Explorer.py
│   │   ├── 3_Seasonal_Monsoon_Trends.py
│   │   ├── 4_Delay_Predictor.py         # XGBoost delay predictor
│   │   └── 5_SHAP_Explainability.py
│   └── utils/
│       ├── db.py                        # SQLAlchemy connection + cached queries
│       └── model.py                     # Model and SHAP loader helpers
├── data/
│   ├── raw/                             # Original CSVs from Kaggle (gitignored)
│   ├── cleaned/                         # Output of clean_data.py (gitignored)
│   └── reference/                       # Static reference lists (train/station)
├── db/
│   ├── schema.sql                       # MySQL table definitions
│   ├── indexes.sql                      # Performance indexes
│   └── full_dump.sql                    # Full database dump
├── models/
│   ├── delay_model_v1.pkl               # Trained XGBoost model
│   ├── feature_columns_v1.pkl
│   ├── shap_explainer_v1.pkl
│   └── shap_values_sample_v1.pkl
├── notebooks/
│   ├── 01_data_quality_analysis.ipynb
│   ├── 02_eda_overall_and_segments.ipynb
│   ├── 03_eda_time_and_season.ipynb
│   ├── 04_hypothesis_testing.ipynb
│   ├── 05_feature_engineering.ipynb
│   └── 06_model_training.ipynb
├── src/
│   ├── clean_data.py                    # Data cleaning pipeline
│   ├── fetch_weather.py                 # Meteostat rainfall fetch
│   ├── load_to_mysql.py                 # Load cleaned data into MySQL
│   └── test_predict.py
└── requirements.txt
```

## Dataset

Source: [Indian Railways Delay Dataset](https://www.kaggle.com/datasets/rxydenxd/indian-railways-delay-dataset) on Kaggle.

Download and place the following files in `data/raw/`:

- `combined_delay.csv`
- `combined_schedule.csv`
- `train_details.csv`
- `station_full_names.csv`

> `data/raw/` and `data/cleaned/` are gitignored. You must download the raw data separately.

## Prerequisites

- Python 3.10+
- A MySQL database (local or cloud-hosted). The project was developed against [Aiven MySQL](https://aiven.io/).

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/shre26/Konkan-Railway-Delay-Root-Cause-Analysis.git
cd Konkan-Railway-Delay-Root-Cause-Analysis
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DB_HOST=your-mysql-host
DB_PORT=3306
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=konkan_railway
```

If your MySQL instance uses SSL (e.g. Aiven), place the CA certificate at `db/aiven-ca.pem`. The `db.py` utility picks it up automatically.

### 5. Set up the database

**Option A — restore from the included dump (recommended):**

```bash
mysql -h <host> -P <port> -u <user> -p konkan_railway < db/full_dump.sql
```

**Option B — apply schema and load from raw data:**

```bash
mysql -h <host> -P <port> -u <user> -p konkan_railway < db/schema.sql
mysql -h <host> -P <port> -u <user> -p konkan_railway < db/indexes.sql
```

Then run the data pipeline (see next section).

## Data Pipeline

Skip this if you restored from `full_dump.sql`.

```bash
# 1. Clean raw data and produce data/cleaned/cleaned_v1.csv
python src/clean_data.py

# 2. (Optional) Fetch weather/rainfall data used in notebooks
python src/fetch_weather.py

# 3. Load cleaned data into MySQL
python src/load_to_mysql.py
```

## Running the Dashboard

```bash
streamlit run app/Home.py
```

Credentials are loaded from the `.env` file at startup.

**Streamlit Cloud deployment:** add the same variables under **Settings > Secrets**:

```toml
DB_HOST = "..."
DB_PORT = "..."
DB_USER = "..."
DB_PASSWORD = "..."
DB_NAME = "konkan_railway"
```

## Dashboard Pages

| Page | Description |
|------|-------------|
| Home | Summary metrics: overall avg delay, worst train, worst station, monsoon impact |
| Overview | Delay distribution, top 10 trains and stations by avg delay, data quality notes |
| Route & Station Explorer | Per-train route with station-level delay breakdown |
| Seasonal & Monsoon Trends | Month-by-month and monsoon vs. non-monsoon comparisons |
| Delay Predictor | Predict delay for a given train, station, date, and rainfall level (XGBoost) |
| SHAP Explainability | Feature importance and SHAP summary from the trained model |

## Notebooks

Run in order. Each notebook reads from `data/cleaned/cleaned_v1.csv` or the MySQL database.

| Notebook | Purpose |
|----------|---------|
| 01 | Data quality audit |
| 02 | EDA — overall patterns and segment-level analysis |
| 03 | EDA — time-of-year and monsoon seasonality |
| 04 | Hypothesis testing (monsoon vs. non-monsoon, day-of-week effects) |
| 05 | Feature engineering |
| 06 | XGBoost model training and SHAP analysis |

## Key Findings

- Delays are significantly higher during monsoon months (June–September)
- A small number of trains and stations account for a disproportionate share of severe delays
- Station position along the route and rainfall category are the strongest predictors of delay
- Extreme delays (> 1000 minutes) are retained in the dataset as they represent genuine disruption events

## Tech Stack

| Component | Library |
|-----------|---------|
| Dashboard | Streamlit 1.63 |
| ML model | XGBoost 3.4, scikit-learn 1.9 |
| Explainability | SHAP 0.52 |
| Database | MySQL, SQLAlchemy 2.0 |
| Data processing | pandas 3.0, numpy 2.5 |
| Visualizations | Plotly 7.0 |
| Weather data | Meteostat 2.1 |
