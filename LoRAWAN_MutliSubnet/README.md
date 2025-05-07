# 🛰️ LoRaWAN-Inspired Mesh Network Simulation using Kubernetes

This project simulates a dynamic multi-hop peer-to-peer mesh network, inspired by LoRaWAN-like IoT architectures, using **Kubernetes-native pods**, **headless services**, and **UDP communication**.

The system is designed for research and education in distributed systems and sensor mesh simulation.

---

## 📦 Components

- `node.py` — Core logic for each mesh node (receiving, forwarding, TTL, hop tracking).
- `topology_neighbors.json` — Random or predefined neighbor graph (used for simulation).
- `topology_mesh_pods.yaml` — Auto-generated pod definitions using neighbor links.
- `mesh-headless-service.yaml` — Kubernetes headless service for DNS-based discovery.
- `starter-node.yaml` — The initiator node that sends the first message.
- `run_k8_new.sh` — Complete end-to-end launcher: build, deploy, and stream.
- `analyze_logs.py` — Log parser to generate hop, latency, and message flow visualizations.
- `fetch_logs.sh` — Fetches `events.json` logs from all pods.
- `clean_k8.sh` — Cleanup script for the cluster and local Docker environment.

---

## 🚀 Getting Started

### 1. Requirements

- macOS/Linux
- [Docker](https://www.docker.com/)
- [Minikube](https://minikube.sigs.k8s.io/)
- [Kubectl](https://kubernetes.io/docs/tasks/tools/)
- Python 3.9+ with `venv` and these packages:
  ```bash
  pip install matplotlib seaborn pandas networkx
  ```

---

### 2. Build and Deploy the Mesh

```bash
chmod +x run_k8_new.sh
./run_k8_new.sh
```

This will:
- Start Minikube
- Build the `mesh-node:latest` Docker image
- Deploy all mesh pods using `topology_mesh_pods.yaml`
- Launch the `mesh-starter` pod
- Stream the initial log output

---

### 3. Monitor the Mesh in Action

Stream logs from all mesh nodes:

```bash
chmod +x stream_mesh_pods.sh
./stream_mesh_pods.sh
```

Or check specific node logs:

```bash
kubectl logs pod/node-3
```

---

### 4. Analyze Logs & Visualize Mesh Behavior

```bash
chmod +x fetch_logs.sh
./fetch_logs.sh

python analyze_logs.py
```

This will:
- Collect `events.json` logs from each pod
- Merge into `merged_events.csv`
- Generate:
  - `hop_distribution.png`
  - `latency_distribution.png`
  - `message_flow_graph.png`
  - `ttl_heatmap.png`
  - `latency_trend.png`

---

## 🧹 Cleanup

```bash
chmod +x clean_k8.sh
./clean_k8.sh
```

This removes all deployments, images, and resets the Minikube environment.

---

## 📡 How It Works

- Nodes discover neighbors from `NEIGHBORS` env var
- UDP is used for message passing (lightweight and connectionless)
- Each message contains:
  - `id`, `src`, `hop`, `ttl`, and timestamp
- Nodes forward messages to neighbors if TTL > 0
- Logs are written in `events.json` per node

---

## 📊 Metrics Tracked

- Hop count distribution
- Per-hop latency
- Message flow graph (directed)
- TTL heatmap (reachability)
- Real-time log streaming per pod

---

## 🧪 Extensible Ideas

- Add packet loss simulation
- Introduce node failure or churn
- Run on real K8s cluster or edge simulators
- Integrate Mininet for custom topologies

---

## 👨‍💻 Author

Prajwal Srinivas  
MS CS – Rutgers University  
Mesh Simulation for Distributed IoT | 2025