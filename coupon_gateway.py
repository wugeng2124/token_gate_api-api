# === coupon_gateway.py (Final Version with Max Uses Fix) ===

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os

app = Flask(__name__)
CORS(app)

DB_FILE = "coupon.db"
ADMIN_PASS = os.getenv("COUPON_ADMIN_PASS", "super2121")  # from .env or default

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS coupons (
        code TEXT PRIMARY KEY,
        max_uses INTEGER,
        used INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route("/token_gate_api", methods=["POST"])
def validate_coupon():
    data = request.get_json()
    code = data.get("coupon", "").strip()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT max_uses, used FROM coupons WHERE code = ?", (code,))
    row = c.fetchone()
    if not row:
        return jsonify({"success": False, "message": "Invalid code."})
    max_uses, used = row
    if used >= max_uses:
        return jsonify({"success": False, "message": "This code has been fully used."})

    # increment used
    c.execute("UPDATE coupons SET used = used + 1 WHERE code = ?", (code,))
    conn.commit()
    remaining = max_uses - (used + 1)
    return jsonify({"success": True, "remaining": remaining, "max_uses": max_uses})

@app.route("/coupon_admin", methods=["GET"])
def coupon_admin():
    if request.args.get("pass") != ADMIN_PASS:
        return "<h3>❌ Access Denied. Provide correct ?pass=yourpassword in URL.</h3>"
    return send_from_directory(".", "dashboard.html")

@app.route("/coupon_api", methods=["GET", "POST", "DELETE"])
def coupon_api():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if request.method == "GET":
        c.execute("SELECT code, max_uses, used FROM coupons")
        result = [
            {
                "code": row[0],
                "max_uses": row[1],
                "used": row[2],
                "remaining": row[1] - row[2]
            } for row in c.fetchall()
        ]
        return jsonify(result)

    elif request.method == "POST":
        data = request.get_json()
        code = data.get("code", "").strip()
        max_uses = int(data.get("max_uses", 5))
        if not code:
            return jsonify({"error": "Missing code"}), 400

        # Replace mode: reset usage
        c.execute("REPLACE INTO coupons (code, max_uses, used) VALUES (?, ?, 0)", (code, max_uses))
        conn.commit()
        return jsonify({"message": f"Code {code} added/reset."})

    elif request.method == "DELETE":
        data = request.get_json()
        code = data.get("code", "").strip()
        c.execute("DELETE FROM coupons WHERE code = ?", (code,))
        conn.commit()
        return jsonify({"message": f"Code {code} deleted."})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
