import os
import openai
import json
from flask import Blueprint, request, jsonify, current_app
import logging

# Use the standard logging module
logging.basicConfig(level=logging.DEBUG)

ai_summary_bp = Blueprint("ai_summary", __name__)

# IMPORTANT: Use a proper environment variable name for your key.
# Do NOT pass the key as the name to os.getenv; use something like "OPENAI_API_KEY"
openai_key = os.getenv("OPENAI_API_KEY")
logging.debug(f"OPENAI_API_KEY (partial): {openai_key[:6] + '...' + openai_key[-4:] if openai_key else 'None'}")
openai.api_key = openai_key

@ai_summary_bp.route("/ai_summary", methods=["POST"])
def ai_summary():
    """
    Expects JSON like:
    {
      "store": 123,
      "forecastSummary": {
        "totalPredicted": 816784,
        "weeks": 4,
        "confidence_low": 185380,
        "confidence_high": 195380
      }
    }
    Returns a JSON with a "summary" key containing the generated text.
    """
    logging.debug("'/ai_summary' endpoint hit")
    
    data = request.get_json()
    logging.debug(f"Received payload: {data}")
    
    if not data or "forecastSummary" not in data:
        logging.debug("Missing forecastSummary in payload")
        return jsonify({"error": "Missing forecastSummary data"}), 400

    store_id = data["store"]
    forecast = data["forecastSummary"]
    logging.debug(f"Forecast details: {forecast}")

    # Construct a prompt for GPT using a dynamic summary
    prompt = (
        f"You are a data assistant. We have an ML forecast for store #{store_id}. "
        f"The total predicted sales over the next {forecast['weeks']} weeks is about "
        f"${forecast['totalPredicted']:,}. The 95% confidence range is from "
        f"${forecast['confidence_low']:,} to ${forecast['confidence_high']:,}. "
        "Summarize findings from what you can see from the Graph. Help explain the data analysis to someone like they have no prior knowledge"
    )
    logging.debug(f"Constructed prompt: {prompt}")

    try:
        # Use the new API interface for ChatCompletion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        logging.debug(f"Raw OpenAI response: {response}")
        
        summary = response["choices"][0]["message"]["content"]
        logging.debug(f"Extracted summary: {summary}")
        return jsonify({"summary": summary})
    except Exception as e:
        # Using standard logging.exception to log the full traceback
        logging.exception("Exception in /ai_summary endpoint")
        return jsonify({"error": str(e)}), 500
