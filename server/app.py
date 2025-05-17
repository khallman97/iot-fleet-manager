from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from datetime import datetime
import subprocess
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import psycopg2
import os
from db import engine, get_db
from models.PiMetricModel import PiMetric
from models.PiWireGuardKeyModel import PiWireGuardKey, PiWireGuardKeySchema
from sqlalchemy import func, cast, Integer


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/postgres")


app = Flask(__name__)

CORS(app, origins=["http://localhost:3000"])  # allow Next.js
# In-memory store
pi_status = {}


BASE_IP = "10.0.0."
START_OCTET = 100


# TODO: this logic would have to change if we ever delete wg_ips
def get_next_ip():
    # Insert/update with ORM
    db: Session = next(get_db())

    # Extract the last octet from IP string and cast to integer
    last_octet = func.split_part(PiWireGuardKey.wg_ip, '.', 4).cast(Integer)

    max_ip_record = (
        db.query(PiWireGuardKey)
        .order_by(last_octet.desc())
        .first()
    )    

    if max_ip_record:
        # Extract last octet from max_ip_record's wg_ip
        max_ip = max_ip_record.wg_ip
        max_last_octet = int(max_ip.split('.')[-1])
        new_ip_oct = max(max_last_octet + 1, START_OCTET)
        if new_ip_oct > 255:
            raise Exception("No more IPs available") 
        return f"{BASE_IP}{new_ip_oct}"
    else:
        return f"{BASE_IP}{START_OCTET}"


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
    
    # Insert/update with ORM
    db: Session = next(get_db())

    # Insert metrics into TimescaleDB
    try:
        metric = PiMetric(
            time=timestamp,
            hostname=hostname,
            cpu_percent=cpu_percent,
            memory_used=memory.get("used"),
            memory_total=memory.get("total"),
            disk_used=disk.get("used"),
            disk_total=disk.get("total"),
            uptime=uptime,
        )
        db.add(metric)
        db.commit()

        # conn = psycopg2.connect(DATABASE_URL)
        # conn.autocommit = True
        # cur = conn.cursor()


        # cur.execute("""
        #     INSERT INTO pi_metrics (time, hostname, cpu_percent, memory_used, memory_total, disk_used, disk_total, uptime)
        #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        #     ON CONFLICT (time, hostname) DO UPDATE SET
        #       cpu_percent = EXCLUDED.cpu_percent,
        #       memory_used = EXCLUDED.memory_used,
        #       memory_total = EXCLUDED.memory_total,
        #       disk_used = EXCLUDED.disk_used,
        #       disk_total = EXCLUDED.disk_total,
        #       uptime = EXCLUDED.uptime;
        # """, (
        #     timestamp,
        #     hostname,
        #     cpu_percent,
        #     memory.get("used"),
        #     memory.get("total"),
        #     disk.get("used"),
        #     disk.get("total"),
        #     uptime
        # ))
    except IntegrityError as e:
        db.rollback()
        print(f"DB Integrity Error: {e}")
    except Exception as e:
        db.rollback()
        print(f"Error inserting metrics: {e}")
    finally:
        db.close()

    print(f"[{timestamp}] Heartbeat from {hostname} ({request.remote_addr})")

    return jsonify({"status": "ok", "hostname": hostname, "last_seen": timestamp})

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify(pi_status)

@app.route('/api/wg/register', methods=['POST'])
def register_wireguard():
    data = request.get_json()
    hostname = data.get("hostname")
    if not hostname:
        return jsonify({"error": "Missing hostname"}), 400

    # Insert/update with ORM
    db: Session = next(get_db())

    if_exsits_wg =  db.query(PiWireGuardKey).filter_by(hostname=hostname).first()

    if if_exsits_wg:
        schema = PiWireGuardKeySchema()
        return jsonify(schema.dump(if_exsits_wg))

    try:
        private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
        public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode()).decode().strip()
        ip = get_next_ip()

        entry = {
            "private_key": private_key,
            "public_key": public_key,
            "ip": ip,
            "server_pubkey": os.environ.get("WG_SERVER_PUBKEY", "SERVER_PUBLIC_KEY_PLACEHOLDER"),
            "server_endpoint": os.environ.get("WG_SERVER_ENDPOINT", "vpn.example.com:51820"),
        }
        entry = PiWireGuardKey(
            hostname=hostname,
            wg_ip=ip,
            public_key=public_key,
            private_key=private_key,
            server_public_key=os.environ.get("WG_SERVER_PUBKEY", "SERVER_PUBLIC_KEY_PLACEHOLDER"),
            server_endpoint= os.environ.get("WG_SERVER_ENDPOINT", "vpn.example.com:51820"),

        )
        db.add(entry)
        db.commit()

        
        print(f"[WireGuard] Registered {hostname} with IP {ip}")

        schema = PiWireGuardKeySchema()
        return jsonify(schema.dump(entry))
    except Exception as e:
        return jsonify({"error": f"WireGuard setup failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
