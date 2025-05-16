import os
import time
import socket
import requests
from metrics import get_metrics

def send_heartbeat():
    hostname = os.getenv("PI_HOSTNAME", socket.gethostname())
    server_url = os.getenv("SERVER_URL", "http://localhost:8000/api")
    token = os.getenv("TOKEN", "DEV_TOKEN")

    payload = {
        "hostname": hostname,
        "ip": socket.gethostbyname(socket.gethostname()),
        "timestamp": int(time.time()),
        "metrics": get_metrics(),
    }

    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.post(f"{server_url}/heartbeat", json=payload, headers=headers, timeout=5)
        res.raise_for_status()
        print(f"[{hostname}] Heartbeat sent.")
    except Exception as e:
        print(f"[{hostname}] Failed to send heartbeat: {e}")

def main():
    interval = int(os.getenv("INTERVAL", 30))
    while True:
        send_heartbeat()
        time.sleep(interval)

if __name__ == "__main__":
    main()
