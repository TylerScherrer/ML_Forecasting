from flask import Blueprint, jsonify, current_app
from sklearn.metrics import mean_absolute_error, mean_squared_error
import math

metrics_bp = Blueprint("metrics", __name__)

@metrics_bp.route("/metrics", methods=["GET"])
def get_metrics():
    df = current_app.config["df"]
    model = current_app.config["model"]
    model_features = current_app.config["model_features"]

    test_data = df.tail(200).copy()
    X_test = test_data[model_features]
    y_test = test_data["Total_Sales"]

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = math.sqrt(mse)

    return jsonify({
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2)
    })
