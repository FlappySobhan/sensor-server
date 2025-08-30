import os
import sqlite3
import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

# ---------------- CONFIG ----------------
DB_PATH = os.environ.get("DB_PATH", "database.db")
API_KEY = "shayan123"  # خودت مقدار دلخواهت رو اینجا قرار بده

# ---------------- DATABASE ----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL,
            humidity REAL,
            soil REAL,
            pump_status INTEGER,
            fan_status INTEGER,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------
@app.route("/health")
def health():
    return "ok", 200

@app.route("/data", methods=["GET", "POST"])
def receive_data():
    # API Key check
    key = request.args.get("key") or request.headers.get("X-API-Key")
    if key != API_KEY:
        return "unauthorized", 401

    # داده رو از JSON یا query string بگیر
    data = request.get_json(silent=True) if request.is_json else request.args
    try:
        temp  = float(data.get("temp"))
        hum   = float(data.get("hum"))
        soil  = float(data.get("soil"))
        pump  = int(data.get("pump"))
        fan   = int(data.get("fan"))
        timestamp = data.get("ts") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"invalid data: {e}", 400

    conn = get_conn()
    conn.execute(
        "INSERT INTO sensor_data (temperature, humidity, soil, pump_status, fan_status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (temp, hum, soil, pump, fan, timestamp)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "temperature": temp,
        "humidity": hum,
        "soil": soil,
        "pump": pump,
        "fan": fan,
        "timestamp": timestamp
    }), 200

@app.route("/data/all", methods=["GET"])
def get_all_data():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sensor_data ORDER BY id DESC").fetchall()
    conn.close()
    result = [dict(row) for row in rows]
    return jsonify(result), 200

@app.route("/data/latest", methods=["GET"])
def get_latest_data():
    conn = get_conn()
    row = conn.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return jsonify(dict(row)) if row else jsonify({}), 200

# Serve static HTML
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
