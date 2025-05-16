from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from db_init import db_init

import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/postgres")

app = Flask(__name__)
db_init()
CORS(app, origins=["http://localhost:3000"])  # allow Next.js
# In-memory store
pi_status = {}

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    hostname = data.get("hostname")
    if not hostname:
        return jsonify({"error": "Missing hostname"}), 400

    timestamp = datetime.utcnow().isoformat()

    # Save full payload with a few extra fields
    pi_status[hostname] = {
        "last_seen": timestamp,
        "ip_from_request": request.remote_addr,
        "payload": data
    }

    # Extract metrics from payload if available
    metrics = data.get("metrics", {})
    cpu_percent = metrics.get("cpu_percent")
    memory = metrics.get("memory", {})
    disk = metrics.get("disk", {})
    uptime = metrics.get("uptime")

    # Insert metrics into TimescaleDB
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()


        cur.execute("""
            INSERT INTO pi_metrics (time, hostname, cpu_percent, memory_used, memory_total, disk_used, disk_total, uptime)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (time, hostname) DO UPDATE SET
              cpu_percent = EXCLUDED.cpu_percent,
              memory_used = EXCLUDED.memory_used,
              memory_total = EXCLUDED.memory_total,
              disk_used = EXCLUDED.disk_used,
              disk_total = EXCLUDED.disk_total,
              uptime = EXCLUDED.uptime;
        """, (
            timestamp,
            hostname,
            cpu_percent,
            memory.get("used"),
            memory.get("total"),
            disk.get("used"),
            disk.get("total"),
            uptime
        ))
    except Exception as e:
        print(f"Error inserting metrics: {e}")

    print(f"[{timestamp}] Heartbeat from {hostname} ({request.remote_addr})")

    return jsonify({"status": "ok", "hostname": hostname, "last_seen": timestamp})

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify(pi_status)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
