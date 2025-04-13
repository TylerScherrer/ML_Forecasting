import pandas as pd
import numpy as np
import pickle
from flask import Flask
from flask_cors import CORS
import urllib.request
import os
import logging

# === Azure Blob SAS URLs ===
MODEL_URL = "https://mlstoragegroup.blob.core.windows.net/ml-artifacts/model.pkl?sp=r&st=2025-04-13T22:51:19Z&se=2025-04-14T06:51:19Z&spr=https&sv=2024-11-04&sr=b&sig=bKcxNJuEQimzDfxAScUIzYu5tqUK4oMd7Z79y57868o%3D"
FEATURES_URL = "https://mlstoragegroup.blob.core.windows.net/ml-artifacts/features.csv?sp=r&st=2025-04-13T22:51:55Z&se=2025-04-14T06:51:55Z&spr=https&sv=2024-11-04&sr=b&sig=gUVLQw6SeFjeCXxOfQWcenlIntM8NuVUhwpNNjYaIDM%3D"

# === Local Cache Paths ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "features.csv")

# === Download if not present ===
if not os.path.exists(MODEL_PATH):
    print("📦 Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

if not os.path.exists(FEATURES_PATH):
    print("📊 Downloading features...")
    urllib.request.urlretrieve(FEATURES_URL, FEATURES_PATH)

# === Load model & data ===
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

df = pd.read_csv(FEATURES_PATH)

# --- Ensure Actionable Features Exist ---
if 'Profit_Margin' not in df.columns:
    if 'State Bottle Retail' in df.columns and 'State Bottle Cost' in df.columns:
        df['Profit_Margin'] = (df['State Bottle Retail'] - df['State Bottle Cost']) / df['State Bottle Retail']
    else:
        df['Profit_Margin'] = np.nan

if 'Is_Promotion_Month' not in df.columns:
    if 'Month' not in df.columns:
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

# === Import Blueprints ===
from routes.stores import stores_bp
from routes.metrics import metrics_bp
from routes.compare import compare_bp
from routes.predict import predict_bp
from routes.seasonality import seasonality_bp
from routes.feature_importance import feature_importance_bp
from routes.ai_summary import ai_summary_bp

def create_app():
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    app = Flask(__name__)
    CORS(app)

    print("[DEBUG] Setting up app config with model, df, etc.")

    app.config["df"] = df
    app.config["model"] = model
    app.config["AVG_MAE"] = AVG_MAE
    app.config["model_features"] = model_features

    # Register routes
    app.register_blueprint(ai_summary_bp)
    app.register_blueprint(stores_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(compare_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(seasonality_bp)
    app.register_blueprint(feature_importance_bp)

    print("[DEBUG] Flask app created and Blueprints registered.")
    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
