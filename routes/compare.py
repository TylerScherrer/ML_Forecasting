from flask import Blueprint, request, jsonify, current_app
import numpy as np

compare_bp = Blueprint("compare", __name__)

@compare_bp.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    store = int(data["store"])
    num_points = int(data.get("num_points", 6))

    df = current_app.config["df"]
    model = current_app.config["model"]
    model_features = current_app.config["model_features"]

    store_df = df[df["Store Number"] == store].sort_values(by=["Year", "Month"])
    if store_df.empty:
        return jsonify({"error": f"Store {store} not found."}), 404

    hist_period = store_df.tail(num_points)
    results = []
    for _, row in hist_period.iterrows():
        actual_sales = row["Total_Sales"]
        X_feat = row[model_features].values.reshape(1, -1)
        predicted_sales = float(model.predict(X_feat)[0])
        results.append({
            "year": float(row["Year"]),
            "month": float(row["Month"]),
            "actual": actual_sales,
            "predicted": predicted_sales
        })

    return jsonify({"data": results})
