from flask import Blueprint, request, jsonify, current_app
import pandas as pd  # may be needed for pd.isna

seasonality_bp = Blueprint("seasonality", __name__)

@seasonality_bp.route("/analysis/seasonality", methods=["GET"])
def seasonality_analysis():
    """
    GET /analysis/seasonality
    Optional query param ?store=<store_id>
    Returns monthly average (and std) of Total_Sales.
    """
    store_param = request.args.get("store", None)

    df = current_app.config["df"]
    if store_param:
        try:
            store_id = int(store_param)
        except ValueError:
            return jsonify({"error": "Invalid store ID"}), 400
        store_df = df[df["Store Number"] == store_id].copy()
        if store_df.empty:
            return jsonify({"error": f"Store {store_id} not found."}), 404
    else:
        store_df = df.copy()

    monthly_stats = (
        store_df.groupby("Month")["Total_Sales"]
        .agg(["mean", "std"])
        .reset_index()
        .sort_values("Month")
    )

    results = []
    for _, row in monthly_stats.iterrows():
        results.append({
            "month": int(row["Month"]),
            "avg_sales": float(row["mean"]),
            "std_sales": float(row["std"]) if not pd.isna(row["std"]) else 0.0
        })

    return jsonify({"seasonality": results})
