import pandas as pd
import numpy as np
import pickle
from flask import Flask
from flask_cors import CORS

# === Load model & data once here ===
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

df = pd.read_csv("features.csv")

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

# Just a constant for confidence intervals, from your training logs
AVG_MAE = 5000

# The columns your model uses
model_features = [
    'Lag_1', 'Lag_2', 'Lag_3', 'Lag_12',
    'Month_sin', 'Month_cos',
    'store_mean_sales', 'store_std_sales',
    'rolling_mean_3', 'rolling_std_3',
    'rolling_mean_6', 'rolling_trend', 'sales_to_avg_ratio',
    'Profit_Margin', 'Is_Promotion_Month', 'Average_Price'
]

# Import your Blueprints
# (Make sure you created these files inside routes/)
from routes.stores import stores_bp
from routes.metrics import metrics_bp
from routes.compare import compare_bp
from routes.predict import predict_bp
from routes.seasonality import seasonality_bp
from routes.feature_importance import feature_importance_bp
from routes.ai_summary import ai_summary_bp

import logging
import os

def create_app():
    # Example: set up a basic logger
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

    app = Flask(__name__)
    CORS(app)

    # Debug: let’s see which keys we are setting
    print("[DEBUG] Setting up app config with model, df, etc.")

    # Attach model/data to app config
    app.config["df"] = df
    app.config["model"] = model
    app.config["AVG_MAE"] = AVG_MAE
    app.config["model_features"] = model_features

    # Register Blueprints
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