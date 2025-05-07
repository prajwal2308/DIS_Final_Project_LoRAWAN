import socket
import os
import threading
import time
import json
import uuid
import random
import subprocess

NODE_NAME = os.getenv("NODE_NAME", "nodeX")
PORT = int(os.getenv("LISTEN_PORT", "5000"))
START_NODE = os.getenv("START_NODE", "false").lower() == "true"
SERVICE_NAME = "mesh-node.default.svc.cluster.local"
PEER_REFRESH_INTERVAL = 300  # refresh peers every 5 minutes
PACKET_DROP_RATE = 0.02  # 2% packet loss simulation

RECEIVED_IDS = set()
KNOWN_PEERS = []
last_peer_refresh = 0

def resolve_peers():
    global KNOWN_PEERS, last_peer_refresh
    try:
        output = subprocess.check_output(["getent", "hosts", SERVICE_NAME], stderr=subprocess.DEVNULL).decode()
        lines = output.strip().split("\n")
        peers = list({line.split()[0] for line in lines if line.split()[0] != socket.gethostbyname(socket.gethostname())})
        if peers:
            KNOWN_PEERS = peers
            last_peer_refresh = time.time()
    except Exception as e:
        print(f"[{NODE_NAME}] DNS resolution failed: {e}", flush=True)

def refresh_peers_if_needed():
    if time.time() - last_peer_refresh > PEER_REFRESH_INTERVAL:
        resolve_peers()

def simulate_packet_loss():
    return random.random() < PACKET_DROP_RATE

def send_sensor_data_periodically():
    if not START_NODE:
        return
    time.sleep(3)
    resolve_peers()

    while True:
        refresh_peers_if_needed()

        if simulate_packet_loss():
            print(f"[{NODE_NAME}] Simulating packet loss (not sending this cycle)", flush=True)
            time.sleep(1)
            continue

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
            "ttl": 25,
            "ts": time.time()
        }

        targets = KNOWN_PEERS[:]
        random.shuffle(targets)
        for ip in targets[:random.randint(2, 4)]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(json.dumps(msg).encode(), (ip, PORT))
                print(f"[{NODE_NAME}]Sent to {ip}:{PORT}", flush=True)
            except Exception as e:
                print(f"[{NODE_NAME}]Send error: {e}", flush=True)

        time.sleep(1)

def listen_and_forward():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("", PORT))
        print(f"[{NODE_NAME}] Listening on port {PORT}...", flush=True)
    except Exception as e:
        print(f"[{NODE_NAME}] Port bind failed: {e}", flush=True)
        return

    resolve_peers()

    while True:
        refresh_peers_if_needed()

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
                print(f"[{NODE_NAME}] 🧯 TTL expired. Not forwarding.", flush=True)
                continue

            targets = [ip for ip in KNOWN_PEERS if ip != addr[0]]
            random.shuffle(targets)
            for ip in targets[:random.randint(2, 4)]:
                try:
                    fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    fwd_sock.sendto(json.dumps(msg).encode(), (ip, PORT))
                    print(f"[{NODE_NAME}] Forwarded to {ip}:{PORT}", flush=True)
                except Exception as e:
                    print(f"[{NODE_NAME}] Forward error: {e}", flush=True)

        except Exception as e:
            print(f"[{NODE_NAME}] Error in loop: {e}", flush=True)

if __name__ == "__main__":
    threading.Thread(target=send_sensor_data_periodically, daemon=True).start()
    listen_and_forward()
