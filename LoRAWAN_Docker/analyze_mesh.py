"""
Combined Mesh Network Analysis Script
This script analyzes the mesh network logs and generates comprehensive metrics and visualizations.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from pathlib import Path
import yaml


output_dir = Path("mesh_analysis")
plots_dir = output_dir / "plots"
data_dir = output_dir / "data"
output_dir.mkdir(exist_ok=True)
plots_dir.mkdir(exist_ok=True)
data_dir.mkdir(exist_ok=True)

print(" Starting mesh network analysis...")

# Path to collected logs
log_dir = Path("collected_logs")
log_files = list(log_dir.glob("*_events.json"))

# Load all events
events = []
for file in log_files:
    with open(file) as f:
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

# Convert to DataFrame
df = pd.DataFrame(events)

if df.empty:
    print("No events found in logs.")
    exit()

# Sort for clarity
df = df.sort_values("timestamp")

# Save raw merged events
df.to_csv(data_dir / "merged_events.csv", index=False)
print(f"Merged {len(df)} events from {len(log_files)} files.")

# ----------------------------
# 1. Basic Metrics
# ----------------------------
total_msgs = df["msg_id"].nunique()
nodes_reached = df["node"].nunique()
all_nodes = len(log_files)
nodes_no_events = all_nodes - nodes_reached
ttl_expired = df[df["ttl"] <= 0].shape[0]

# ----------------------------
# 2. Hop Count Analysis
# ----------------------------
hop_stats = {
    "max_hop": df["hop"].max(),
    "min_hop": df["hop"].min(),
    "avg_hop": round(df["hop"].mean(), 2),
}

plt.figure(figsize=(10, 5))
sns.histplot(df["hop"], bins=range(1, df["hop"].max() + 2), kde=False)
plt.title("Hop Count Distribution")
plt.xlabel("Hop Count")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(plots_dir / "hop_distribution.png")
print("Saved hop_distribution.png")

# ----------------------------
# 3. Latency Analysis
# ----------------------------
latency = df.groupby("msg_id").agg(
    first_seen=("timestamp", "min"),
    last_seen=("timestamp", "max"),
    hops=("hop", "max"),
    receivers=("node", "nunique"),
)
latency["latency"] = latency["last_seen"] - latency["first_seen"]

latency_stats = {
    "max_latency": round(latency["latency"].max(), 4),
    "min_latency": round(latency["latency"].min(), 4),
    "avg_latency": round(latency["latency"].mean(), 4),
}

plt.figure(figsize=(10, 5))
sns.histplot(latency["latency"], bins=30, kde=True)
plt.title("Latency Distribution")
plt.xlabel("Latency (seconds)")
plt.tight_layout()
plt.savefig(plots_dir / "latency_distribution.png")
print("Saved latency_distribution.png")

# ----------------------------
# 4. Message Flow Network
# ----------------------------
G = nx.DiGraph()
for _, row in df.iterrows():
    G.add_edge(row["from"], row["node"])

plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, seed=42)
nx.draw(
    G,
    pos,
    with_labels=True,
    node_color="skyblue",
    edge_color="gray",
    node_size=600,
    arrows=True,
)
plt.title("Message Flow Network")
plt.tight_layout()
plt.savefig(plots_dir / "message_flow_graph.png")
print("Saved message_flow_graph.png")

# ----------------------------
# 5. Node Activity Analysis
# ----------------------------
forward_counts = df["node"].value_counts().to_dict()
most_active = max(forward_counts, key=forward_counts.get)
least_active = min(forward_counts, key=forward_counts.get)


# ----------------------------
# 6. Generate Mesh Topology
# ----------------------------
def generate_mesh_topology():
    with open("docker-compose.yml", "r") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    G = nx.DiGraph()

    for node, config in services.items():
        G.add_node(node)
        env_vars = config.get("environment", [])
        for var in env_vars:
            if var.startswith("NEXT_NODES="):
                targets = var.split("=")[1].split(",")
                for target in targets:
                    if ":" in target:
                        target_name = target.split(":")[0].strip()
                        G.add_edge(node, target_name)

    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G, k=0.2)
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=500,
        node_color="skyblue",
        font_size=8,
        arrowsize=12,
    )
    plt.title("Mesh Network Topology")
    plt.savefig(plots_dir / "mesh_topology.png", bbox_inches="tight")
    plt.close()
    print("Saved mesh_topology.png")


generate_mesh_topology()

# ----------------------------
# 7. Save Comprehensive Metrics
# ----------------------------
with open(data_dir / "mesh_metrics.txt", "w") as f:
    f.write("Mesh Network Analysis Report\n")
    f.write("=" * 50 + "\n\n")

    f.write("1. Message Statistics\n")
    f.write("-" * 20 + "\n")
    f.write(f"Total Unique Messages: {total_msgs}\n")
    f.write(f"Total Nodes: {all_nodes}\n")
    f.write(f"Nodes That Received Messages: {nodes_reached}\n")
    f.write(f"Nodes With No Events: {nodes_no_events}\n")
    f.write(f"TTL Expiry Events: {ttl_expired}\n\n")

    f.write("2. Hop Statistics\n")
    f.write("-" * 20 + "\n")
    f.write(f"Maximum Hops: {hop_stats['max_hop']}\n")
    f.write(f"Minimum Hops: {hop_stats['min_hop']}\n")
    f.write(f"Average Hops: {hop_stats['avg_hop']}\n\n")

    f.write("3. Latency Statistics\n")
    f.write("-" * 20 + "\n")
    f.write(f"Maximum Latency: {latency_stats['max_latency']}s\n")
    f.write(f"Minimum Latency: {latency_stats['min_latency']}s\n")
    f.write(f"Average Latency: {latency_stats['avg_latency']}s\n\n")

    f.write("4. Node Activity\n")
    f.write("-" * 20 + "\n")
    f.write(
        f"Most Active Node: {most_active} ({forward_counts[most_active]} messages)\n"
    )
    f.write(
        f"Least Active Node: {least_active} ({forward_counts[least_active]} messages)\n"
    )

    # ----------------------------
# 8. Advanced Metrics & Visualizations
# ----------------------------

# 8.1 Message Delivery Ratio
message_delivery = df.groupby("msg_id")["node"].nunique()
delivery_ratio = (message_delivery > 1).sum() / len(message_delivery)

# 8.2 Per-Node Load (Messages Handled)
node_msg_counts = df["node"].value_counts()
plt.figure(figsize=(12, 6))
node_msg_counts.plot(kind="bar", title="Messages Handled per Node")
plt.xlabel("Node")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig(plots_dir / "node_message_load.png")
print(" Saved node_message_load.png")

# 8.3 Latency vs Hop Correlation
plt.figure(figsize=(8, 6))
sns.scatterplot(data=latency, x="hops", y="latency")
plt.title("Latency vs. Hop Count")
plt.xlabel("Hop Count")
plt.ylabel("Latency (s)")
plt.tight_layout()
plt.savefig(plots_dir / "latency_vs_hop.png")
print(" Saved latency_vs_hop.png")

# 8.4 Redundant Flow Paths
paths_per_msg = df.groupby("msg_id").apply(
    lambda g: g[["from", "node"]].drop_duplicates().shape[0]
)
plt.figure(figsize=(10, 5))
sns.histplot(paths_per_msg)
plt.title("Unique Flow Paths per Message")
plt.tight_layout()
plt.savefig(plots_dir / "path_redundancy.png")
print(" Saved path_redundancy.png")

# 8.5 Dead-End Nodes
forwarding_nodes = df[df["ttl"] > 0]["from"].value_counts()
inactive_nodes = all_nodes - len(forwarding_nodes)

# ----------------------------
# 9. Delivery Ratio Analysis
# ----------------------------
delivery_ratios = df.groupby("msg_id")["node"].nunique() / all_nodes
plt.figure(figsize=(10, 5))
sns.histplot(delivery_ratios * 100, bins=20)
plt.title("Delivery Ratio per Message")
plt.xlabel("Delivery Ratio (%)")
plt.ylabel("Message Count")
plt.tight_layout()
plt.savefig(plots_dir / "delivery_ratio_hist.png")
print("Saved delivery_ratio_hist.png")

# ----------------------------
# 10. Redundancy (Duplicate Handling)
# ----------------------------
duplicates = df.duplicated(subset=["node", "msg_id"]).sum()
dup_stats = df.groupby("msg_id")["node"].value_counts().reset_index(name="count")
dup_stats = dup_stats[dup_stats["count"] > 1]
plt.figure(figsize=(10, 5))
sns.histplot(dup_stats["count"], bins=10)
plt.title("Redundant Receives per Message")
plt.xlabel("Redundant Count")
plt.tight_layout()
plt.savefig(plots_dir / "redundancy_hist.png")
print("Saved redundancy_hist.png")

# ----------------------------
# 11. Energy Consumption Estimate
# ----------------------------
energy_data = df["node"].value_counts().reset_index()
energy_data.columns = ["node", "received"]
energy_data["sent"] = df["from"].value_counts()
energy_data = energy_data.fillna(0)
energy_data["energy"] = energy_data["sent"] * 1 + energy_data["received"] * 0.5
energy_data.to_csv(data_dir / "node_energy.csv", index=False)
plt.figure(figsize=(12, 6))
sns.barplot(x="node", y="energy", data=energy_data.sort_values("energy", ascending=False).head(20))
plt.xticks(rotation=90)
plt.title("Top 20 Nodes by Energy Consumption")
plt.tight_layout()
plt.savefig(plots_dir / "energy_consumption_top20.png")
print("Saved energy_consumption_top20.png")


# ----------------------------
# 12. Spread Efficiency
# ----------------------------
# For each message: unique receivers / max hop count
latency_df = df.groupby("msg_id").agg(
    hops=("hop", "max"),
    reach=("node", "nunique")
)
latency_df["spread_efficiency"] = latency_df["reach"] / latency_df["hops"]
avg_spread_efficiency = latency_df["spread_efficiency"].mean()

# ----------------------------
# 13. Jain’s Fairness Index
# ----------------------------
node_counts = df["node"].value_counts().values
n = len(node_counts)
fairness_index = (node_counts.sum() ** 2) / (n * (node_counts**2).sum())

# Save CSV summaries
latency.to_csv(data_dir / "latency_summary.csv")
node_msg_counts.to_csv(data_dir / "node_load.csv")

# Append to report
with open(data_dir / "mesh_metrics.txt", "a") as f:
    f.write("\n5. Advanced Metrics\n")
    f.write("-" * 20 + "\n")
    f.write(f"Message Delivery Ratio (>1 receiver): {delivery_ratio:.2f}\n")
    f.write(f"Nodes That Participated in Forwarding: {len(forwarding_nodes)}\n")
    f.write(f"Dead-End Nodes (only received): {inactive_nodes}\n")
    f.write(f"Unique Flow Paths per Message (avg): {round(paths_per_msg.mean(), 2)}\n")
    f.write("6. Delivery Quality\n")
    f.write("-" * 20 + "\n")
    f.write(f"Average Delivery Ratio: {round(delivery_ratios.mean()*100, 2)}%\n")
    f.write(f"Total Duplicates (same msg to same node): {duplicates}\n\n")

    f.write("7. Energy Metrics\n")
    f.write("-" * 20 + "\n")
    f.write(f"Top Energy Node: {energy_data.sort_values('energy', ascending=False).iloc[0]['node']} with {energy_data['energy'].max()} units\n")
    f.write(f"Avg Energy Used per Node: {energy_data['energy'].mean():.2f} units\n")
    
    f.write("\n8. Spread Efficiency\n---------------------\n")
    f.write(f"Average Spread Efficiency (reach / hops): {avg_spread_efficiency:.4f}\n")
    f.write("\n9. Network Fairness\n---------------------\n")
    f.write(f"Jain's Fairness Index on Node Load: {fairness_index:.4f}\n")



print("✅ Advanced metrics added and visualizations saved.")
print("\nAnalysis complete! All outputs saved in 'mesh_analysis' directory:")
print(f"  - Plots: {plots_dir}")
print(f"  - Data: {data_dir}")
print(f"  - Metrics: {data_dir}/mesh_metrics.txt")
