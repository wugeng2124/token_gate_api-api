# token_gate_api.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import secrets
import time

app = Flask(__name__)
CORS(app)

# Simulated in-memory coupon system
VALID_COUPONS = {
    "FREEA5": 5  # Coupon code: max uses per token
}

# Session memory (this would be in a DB in production)
sessions = {}

@app.route("/validate_coupon", methods=["POST"])
def validate_coupon():
    data = request.json
    code = data.get("code", "").strip().upper()

    if code in VALID_COUPONS:
        token = secrets.token_urlsafe(16)
        sessions[token] = {
            "coupon": code,
            "remaining": VALID_COUPONS[code],
            "created_at": time.time()
        }
        return jsonify({"success": True, "token": token, "remaining": VALID_COUPONS[code]})
    else:
        return jsonify({"success": False, "message": "Invalid coupon code."})

@app.route("/check_access", methods=["POST"])
def check_access():
    data = request.json
    token = data.get("token", "")

    session = sessions.get(token)
    if not session:
        return jsonify({"success": False, "message": "Invalid session token."})

    if session["remaining"] <= 0:
        return jsonify({"success": False, "message": "Coupon usage exhausted."})

    # Decrease remaining use count
    session["remaining"] -= 1
    return jsonify({"success": True, "remaining": session["remaining"]})


if __name__ == "__main__":
    app.run(debug=True)
