import os
import openai
import logging
from flask import Blueprint, request, jsonify

ai_feature_importance_bp = Blueprint("ai_feature_importance", __name__)

# Use your environment variable for the API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if openai.api_key is None:
    logging.error("OPENAI_API_KEY is not set!")

@ai_feature_importance_bp.route("/ai_feature_importance", methods=["POST"])
def ai_feature_importance():
    """
    Expects JSON like:
    {
      "actionable": [
         {"feature": "Profit_Margin", "importance": 0.27},
         {"feature": "Is_Promotion_Month", "importance": 0.15},
         {"feature": "Average_Price", "importance": 0.10},
         ... possibly more ...
      ],
      "conceptual": [
         {"feature": "Lag_1", "importance": 0.20},
         {"feature": "Lag_2", "importance": 0.13},
         {"feature": "rolling_mean_3", "importance": 0.08},
         ... possibly more ...
      ]
    }
    
    Returns a plain-English summary of the feature importances.
    """
    data = request.get_json()
    if not data or ("actionable" not in data and "conceptual" not in data):
        return jsonify({"error": "Missing actionable and/or conceptual data"}), 400

    actionable = data.get("actionable", [])
    conceptual = data.get("conceptual", [])

    # Helper to format a list of features as a human-friendly string (top 3 only)
    def format_feature_list(features):
        sorted_features = sorted(features, key=lambda x: x.get("importance", 0), reverse=True)
        if not sorted_features:
            return "None"
        # Format each feature to show its name and importance as a percentage.
        feature_strings = [
            f"{feat['feature']} ({feat['importance']*100:.2f}%)"
            for feat in sorted_features[:3]
        ]
        return ", ".join(feature_strings)

    actionable_str = format_feature_list(actionable)
    conceptual_str = format_feature_list(conceptual)

    prompt = (
        f"You are a data assistant. Below are the top feature importances from an ML model for predicting liquor sales. "
        f"Actionable features (manager-controllable) are: {actionable_str}. "
        f"Conceptual features (contextual insights) are: {conceptual_str}. "
        "Please provide a brief, plain-English summary that explains how these features influence the model's predictions and "
        "suggests any potential actions a store manager might consider to improve performance."
    )

    logging.debug(f"Constructed prompt for feature importance: {prompt}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        logging.debug(f"OpenAI response (raw): {response}")
        summary = response["choices"][0]["message"]["content"]
        logging.debug(f"Extracted summary: {summary}")
        return jsonify({"summary": summary})
    except Exception as e:
        logging.exception("Exception in /ai_feature_importance endpoint")
        return jsonify({"error": str(e)}), 500
