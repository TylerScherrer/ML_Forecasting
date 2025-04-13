from flask import Blueprint, jsonify, current_app
import pandas as pd

feature_importance_bp = Blueprint("feature_importance", __name__)

@feature_importance_bp.route("/feature_importance", methods=["GET"])
def get_feature_importance():
    """
    GET /feature_importance
    Returns feature importances from the loaded model,
    split into actionable vs. conceptual factors.
    """
    model = current_app.config["model"]
    model_features = current_app.config["model_features"]

    if not hasattr(model, "feature_importances_"):
        return jsonify({"error": "Model does not provide feature_importances_"}), 400

    importances = model.feature_importances_
    if len(importances) != len(model_features):
        return jsonify({"error": "Mismatch between model_features and feature_importances_ length"}), 500

    df_imp = pd.DataFrame({
        "feature": model_features,
        "importance": importances
    }).sort_values(by="importance", ascending=False)

    # Manager-controllable features
    actionable_features = {"Profit_Margin", "Is_Promotion_Month", "Average_Price"}
    df_actionable = df_imp[df_imp["feature"].isin(actionable_features)]
    df_conceptual = df_imp[~df_imp["feature"].isin(actionable_features)]

    return jsonify({
        "actionable": df_actionable.to_dict(orient="records"),
        "conceptual": df_conceptual.to_dict(orient="records")
    })
