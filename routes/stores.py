from flask import Blueprint, jsonify, current_app

stores_bp = Blueprint("stores", __name__)

@stores_bp.route("/", methods=["GET"])

def get_stores():
    try:
        df = current_app.config["df"]
        if "Store Number" not in df.columns:
            return jsonify({"error": "Missing 'Store Number'"}), 500

        store_ids = sorted(df["Store Number"].dropna().astype(int).unique().tolist())
        return jsonify({"stores": store_ids})
    except Exception as e:
        return jsonify({"error": f"Could not fetch store IDs: {str(e)}"}), 500
