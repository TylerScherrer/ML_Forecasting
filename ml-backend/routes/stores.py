from flask import Blueprint, jsonify, current_app

stores_bp = Blueprint("stores", __name__)

@stores_bp.route("/stores", methods=["GET"])
def get_stores():
    df = current_app.config["df"]  # Access from app config
    store_ids = sorted(df["Store Number"].unique().astype(int).tolist())
    return jsonify({"stores": store_ids})
