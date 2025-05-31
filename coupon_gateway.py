# === coupon_gateway.py ===
import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string, redirect
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

app = Flask(__name__)
CORS(app)

DB_FILE = "coupons.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            code TEXT PRIMARY KEY,
            max_uses INTEGER,
            used INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/token_gate_api", methods=["POST"])
def validate_coupon():
    data = request.get_json()
    code = data.get("coupon", "").strip().upper()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT max_uses, used FROM coupons WHERE code = ?", (code,))
    row = cursor.fetchone()

    if row:
        max_uses, used = row
        if used < max_uses:
            cursor.execute("UPDATE coupons SET used = used + 1 WHERE code = ?", (code,))
            conn.commit()
            conn.close()
            return jsonify(success=True, token="valid_session_token", remaining=max_uses - used - 1)
        else:
            conn.close()
            return jsonify(success=False, message="Code has been fully used.")
    else:
        conn.close()
        return jsonify(success=False, message="Invalid code.")

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    password = request.args.get("pass", "")
    if password != ADMIN_PASSWORD:
        return "❌ Access Denied. Provide correct ?pass=yourpassword in URL."

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if request.method == "POST":
        new_code = request.form.get("new_code", "").strip().upper()
        max_uses = int(request.form.get("max_uses", "1"))
        if new_code:
            cursor.execute("INSERT OR REPLACE INTO coupons (code, max_uses, used) VALUES (?, ?, 0)", (new_code, max_uses))
            conn.commit()

    cursor.execute("SELECT code, max_uses, used FROM coupons")
    rows = cursor.fetchall()
    conn.close()

    html = """
    <h2>🎟️ Coupon Admin Panel</h2>
    <form method='POST'>
        <input name='new_code' placeholder='New Code' required>
        <input name='max_uses' type='number' value='5' min='1'>
        <button type='submit'>Add / Replace</button>
    </form>
    <table border=1 cellpadding=8 style='margin-top:20px'>
        <tr><th>Code</th><th>Max Uses</th><th>Used</th><th>Remaining</th></tr>
        {% for code, max_uses, used in rows %}
            <tr><td>{{code}}</td><td>{{max_uses}}</td><td>{{used}}</td><td>{{max_uses - used}}</td></tr>
        {% endfor %}
    </table>
    """
    return render_template_string(html, rows=rows)

@app.route("/", methods=["GET"])
def home():
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
