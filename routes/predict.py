from flask import Blueprint, request, jsonify, current_app
import numpy as np

predict_bp = Blueprint("predict", __name__)

@predict_bp.route("/predict", methods=["POST"])
def predict_route():
    """
    POST /predict
    Expects JSON: {"store": <store_id>, "weeks": <int>}
    Returns forecast for next 'weeks' periods for the specified store.
    """
    data = request.get_json()
    store = int(data["store"])
    weeks = int(data.get("weeks", 4))

    # Access config variables set in create_app()
    df = current_app.config["df"]
    model = current_app.config["model"]
    model_features = current_app.config["model_features"]
    AVG_MAE = current_app.config["AVG_MAE"]

    # Sort the store’s data
    store_df = df[df["Store Number"] == store].sort_values(by=["Year", "Month"])
    if store_df.empty:
        return jsonify({"error": f"Store {store} not found."}), 404

    current_row = store_df.iloc[-1].copy()
    predictions = []
    current_month = int(current_row["Month"])

    for _ in range(weeks):
        X_feat = current_row[model_features].values.reshape(1, -1)
        pred_sales = float(model.predict(X_feat)[0])

        upper = pred_sales + AVG_MAE
        lower = max(pred_sales - AVG_MAE, 0)  # floor at zero

        predictions.append({
            "predicted": pred_sales,
            "upper": upper,
            "lower": lower
        })

        # Update dynamic row for next iteration
        current_row["Lag_3"] = current_row["Lag_2"]
        current_row["Lag_2"] = current_row["Lag_1"]
        current_row["Lag_1"] = pred_sales

        current_month += 1
        if current_month > 12:
            current_month = 1
            current_row["Year"] += 1

        current_row["Month"] = float(current_month)
        current_row["Month_sin"] = np.sin(2 * np.pi * current_month / 12)
        current_row["Month_cos"] = np.cos(2 * np.pi * current_month / 12)

        lags = [current_row["Lag_1"], current_row["Lag_2"], current_row["Lag_3"]]
        current_row["rolling_mean_3"] = np.mean(lags)
        current_row["rolling_std_3"] = np.std(lags)
        current_row["rolling_mean_6"] = np.mean(lags + [current_row["rolling_mean_3"]] * 3)
        current_row["rolling_trend"] = current_row["rolling_mean_3"] - current_row["rolling_mean_6"]
        current_row["sales_to_avg_ratio"] = pred_sales / (current_row["rolling_mean_3"] + 1e-6)

    return jsonify({
        "prediction": [
            {
                "predicted": round(p["predicted"], 2),
                "upper": round(p["upper"], 2),
                "lower": round(p["lower"], 2)
            }
            for p in predictions
        ],
        "total": round(sum(p["predicted"] for p in predictions), 2)
    })
