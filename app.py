import os
import logging
import urllib.request
import pickle
import pandas as pd
import numpy as np
from flask import Flask
from flask_cors import CORS

# === Azure Blob SAS URLs ===
MODEL_URL = "https://mlstoragegroup.blob.core.windows.net/ml-artifacts/model.pkl?sp=r&st=2025-04-16T00:54:37Z&se=2026-01-16T09:54:37Z&spr=https&sv=2024-11-04&sr=b&sig=9ui%2F6DONK0mcGhTwME0WFps93%2FytZnO%2BPsDIEIozxzQ%3D"
FEATURES_URL = "https://mlstoragegroup.blob.core.windows.net/ml-artifacts/features.csv?sp=r&st=2025-04-16T00:54:11Z&se=2025-12-01T09:54:11Z&spr=https&sv=2024-11-04&sr=b&sig=pMhMY2AmblthZe9UxP7AEPOU5A0DsFu2VF8kcubGxoU%3D"

# === Local Paths ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "features.csv")

# === Download Files if Missing ===
if not os.path.exists(MODEL_PATH):
    print("📦 Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

if not os.path.exists(FEATURES_PATH):
    print("📊 Downloading features...")
    urllib.request.urlretrieve(FEATURES_URL, FEATURES_PATH)

# === Load Model & Data ===
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

df = pd.read_csv(FEATURES_PATH)

# === Feature Engineering ===
if 'Profit_Margin' not in df.columns:
    if 'State Bottle Retail' in df.columns and 'State Bottle Cost' in df.columns:
        df['Profit_Margin'] = (df['State Bottle Retail'] - df['State Bottle Cost']) / df['State Bottle Retail']
    else:
        df['Profit_Margin'] = np.nan

if 'Is_Promotion_Month' not in df.columns:
    if 'Month' not in df.columns and 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.month
    df['Is_Promotion_Month'] = df['Month'].isin([11, 12]).astype(int)

if 'Average_Price' not in df.columns:
    if 'Sale (Dollars)' in df.columns and 'Bottles Sold' in df.columns:
        df['Average_Price'] = df['Sale (Dollars)'] / df['Bottles Sold'].replace(0, np.nan)
        df['Average_Price'] = df['Average_Price'].fillna(0)
    else:
        df['Average_Price'] = np.nan

# === Constants ===
AVG_MAE = 5000
model_features = [
    'Lag_1', 'Lag_2', 'Lag_3', 'Lag_12',
    'Month_sin', 'Month_cos',
    'store_mean_sales', 'store_std_sales',
    'rolling_mean_3', 'rolling_std_3',
    'rolling_mean_6', 'rolling_trend', 'sales_to_avg_ratio',
    'Profit_Margin', 'Is_Promotion_Month', 'Average_Price'
]

# === Create Flask App ===
app = Flask(__name__)
CORS(app)

# === App Configuration ===
app.config["df"] = df
app.config["model"] = model
app.config["AVG_MAE"] = AVG_MAE
app.config["model_features"] = model_features

# === Health Check ===
@app.route("/")
def index():
    return "🚀 ML Forecast API is live and working!"

# === Register Blueprints ===
from routes.stores import stores_bp
from routes.metrics import metrics_bp
from routes.compare import compare_bp
from routes.predict import predict_bp
from routes.seasonality import seasonality_bp
from routes.feature_importance import feature_importance_bp
from routes.ai_summary import ai_summary_bp

app.register_blueprint(stores_bp)
app.register_blueprint(metrics_bp)
app.register_blueprint(compare_bp)
app.register_blueprint(predict_bp)
app.register_blueprint(seasonality_bp)
app.register_blueprint(feature_importance_bp)
app.register_blueprint(ai_summary_bp)

# === For Azure Compatibility ===
application = app

# === Start Server Locally ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s: %(message)s')
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
