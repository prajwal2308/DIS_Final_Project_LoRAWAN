import socket
import os
import threading
import time
import json
import uuid
import random

NODE_NAME = os.getenv("NODE_NAME", "nodeX")
NEXT_NODES = os.getenv("NEXT_NODES", "").split(",")  # Format: IP:PORT,IP:PORT,...
PORT = int(os.getenv("LISTEN_PORT", "5000"))
START_NODE = os.getenv("START_NODE", "false").lower() == "true"

RECEIVED_IDS = set()

print(f"[{NODE_NAME}] Node script started", flush=True)
print(f"[{NODE_NAME}] NEXT_NODES: {NEXT_NODES}", flush=True)

def send_sensor_data_periodically():
    if not START_NODE:
        return

    time.sleep(3)  # buffer so receivers are ready

    while True:
        msg_id = str(uuid.uuid4())
        sensor_data = {
            "temperature": round(random.uniform(20.0, 30.0), 2),
            "humidity": round(random.uniform(40.0, 60.0), 2)
        }

        msg = {
            "id": msg_id,
            "src": NODE_NAME,
            "payload": sensor_data,
            "hop": 1,
            "ttl": 10,
            "ts": time.time()
        }

        for target in NEXT_NODES:
            try:
                if ":" not in target or not target.strip():
                    print(f"[{NODE_NAME}] Skipping invalid NEXT_NODE: {target}", flush=True)
                    continue
                ip, port = target.strip().split(":")
                port = int(port)

                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(json.dumps(msg).encode(), (ip, port))
                print(f"[{NODE_NAME}]Sent sensor data to {ip}:{port}", flush=True)

            except Exception as e:
                print(f"[{NODE_NAME}] Error sending to {target}: {e}", flush=True)

        time.sleep(10)  

def listen_and_forward():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("", PORT))
        print(f"[{NODE_NAME}] Listening on port {PORT}...", flush=True)
    except Exception as e:
        print(f"[{NODE_NAME}] Port bind failed: {e}", flush=True)
        return

    while True:
        try:
            data, addr = sock.recvfrom(2048)
            msg = json.loads(data.decode())
            msg_id = msg.get("id")

            if msg_id in RECEIVED_IDS:
                continue 

            RECEIVED_IDS.add(msg_id)
            msg["hop"] += 1
            msg["ttl"] -= 1

            print(f"[{NODE_NAME}] Received: {msg}", flush=True)

            # log it
            log_entry = {
                "node": NODE_NAME,
                "from": addr[0],
                "msg_id": msg["id"],
                "hop": msg["hop"],
                "ttl": msg["ttl"],
                "payload": msg["payload"],
                "timestamp": time.time()
            }

            with open("events.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            if msg["ttl"] <= 0:
                print(f"[{NODE_NAME}] TTL expired. Not forwarding.", flush=True)
                continue

            for target in NEXT_NODES:
                if ":" not in target or not target.strip():
                    continue
                ip, port = target.strip().split(":")
                port = int(port)
                fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                fwd_sock.sendto(json.dumps(msg).encode(), (ip, port))
                print(f"[{NODE_NAME}] Forwarded to {ip}:{port}", flush=True)

        except Exception as e:
            print(f"[{NODE_NAME}] Error in loop: {e}", flush=True)

if __name__ == "__main__":
    print(f"[{NODE_NAME}] Node is starting up...", flush=True)
    threading.Thread(target=send_sensor_data_periodically, daemon=True).start()
    listen_and_forward()
