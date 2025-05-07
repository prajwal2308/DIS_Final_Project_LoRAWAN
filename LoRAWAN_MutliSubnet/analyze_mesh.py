import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from pathlib import Path
import yaml
import random


output_dir = Path("mesh_analysis")
plots_dir = output_dir / "plots"
data_dir = output_dir / "data"
output_dir.mkdir(exist_ok=True)
plots_dir.mkdir(exist_ok=True)
data_dir.mkdir(exist_ok=True)

print("Starting mesh network analysis...")

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

df = df.sort_values("timestamp")
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
    "avg_hop": round(df["hop"].mean(), 2)
}

plt.figure(figsize=(10, 5))
sns.histplot(df["hop"], bins=range(1, df["hop"].max()+2), kde=False)
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
    receivers=("node", "nunique")
)
latency["latency"] = latency["last_seen"] - latency["first_seen"]

latency_stats = {
    "max_latency": round(latency["latency"].max(), 4),
    "min_latency": round(latency["latency"].min(), 4),
    "avg_latency": round(latency["latency"].mean(), 4)
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
nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray', node_size=600, arrows=True)
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
# 5. Advanced Metrics
# ----------------------------
# Message Delivery Ratio (>1 receiver)
delivered_msgs = latency[latency["receivers"] > 1].shape[0]
delivery_ratio = round(delivered_msgs / total_msgs, 2) if total_msgs else 0

# Nodes That Participated in Forwarding
nodes_forwarded = set(df["node"].unique())
num_forwarded = len(nodes_forwarded)


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


# Dead-End Nodes (only received, never forwarded)
all_nodes_set = set(df["node"]).union(set(df["from"]))
received_only = set(df["node"]) - set(df["from"])  # nodes that never appear as 'from'
num_dead_ends = len(received_only)

# Unique Flow Paths per Message (avg)
unique_paths = df.groupby("msg_id").apply(lambda x: x[["from", "node"]].drop_duplicates().shape[0])
avg_unique_paths = round(unique_paths.mean(), 2)

# Average Delivery Ratio (receivers per message / total nodes)
avg_delivery_ratio = round(latency["receivers"].mean() / all_nodes * 100, 2) if all_nodes else 0

# Total Duplicates (same msg to same node)
duplicates = df.groupby(["msg_id", "node"]).size()
total_duplicates = int((duplicates > 1).sum())

# ----------------------------
# 6. Energy Metrics (simulate: each forward = 0.5 units)
energy_per_node = df["node"].value_counts() * 0.5
if not energy_per_node.empty:
    top_energy_node = energy_per_node.idxmax()
    top_energy_val = energy_per_node.max()
    avg_energy = round(energy_per_node.mean(), 2)
else:
    top_energy_node = None
    top_energy_val = 0
    avg_energy = 0

# ----------------------------
# 7. Spread Efficiency (reach/hops)
spread_efficiency = latency["receivers"] / latency["hops"].replace(0, 1)
avg_spread_eff = round(spread_efficiency.mean(), 4)

# ----------------------------
# 8. Jain's Fairness Index on Node Load
node_loads = df["node"].value_counts().values
if node_loads.size > 0:
    fairness = (sum(node_loads) ** 2) / (len(node_loads) * sum(node_loads ** 2))
    fairness = round(fairness, 4)
else:
    fairness = 0
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
# 6. Generate Mesh Topology
# ----------------------------
def generate_mesh_topology():
    with open("docker-compose.yml", "r") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    G = nx.DiGraph()

    # Extract subnet info for each node
    node_subnet_map = {}
    network_map = data.get("networks", {})
    subnet_colors = {
        "meshnet1": "lightblue",
        "meshnet2": "lightgreen",
        "meshnet3": "lightpink",
        "meshnet4": "lightyellow"
    }

    # First pass: Add nodes and collect subnet info
    for node, config in services.items():
        node_networks = config.get("networks", {})
        subnets = list(node_networks.keys())
        node_subnet_map[node] = subnets
        G.add_node(node)
        # Store subnet info in node attributes
        G.nodes[node]['subnets'] = subnets
        G.nodes[node]['is_bridge'] = len(subnets) > 1

    # Second pass: Add edges
    for node, config in services.items():
        env_vars = config.get("environment", [])
        for var in env_vars:
            if var.startswith("NEXT_NODES="):
                targets = var.split("=")[1].split(",")
                for target in targets:
                    if ":" in target:
                        target_name = target.split(":")[0].strip()
                        G.add_edge(node, target_name)

    # Create a custom layout that groups nodes by subnet
    pos = {}
    subnet_positions = {
        "meshnet1": (0, 0),
        "meshnet2": (1, 0),
        "meshnet3": (0, 1),
        "meshnet4": (1, 1)
    }

    # Position nodes based on their primary subnet
    for node in G.nodes():
        subnets = G.nodes[node]['subnets']
        if subnets:
            primary_subnet = subnets[0]
            base_x, base_y = subnet_positions[primary_subnet]
            # Add some random offset within the subnet's area
            pos[node] = (
                base_x + random.uniform(-0.3, 0.3),
                base_y + random.uniform(-0.3, 0.3)
            )

    plt.figure(figsize=(15, 15))

    nx.draw_networkx_edges(G, pos, edge_color='gray', alpha=0.5, arrows=True, arrowsize=10)
    for subnet, color in subnet_colors.items():
        subnet_nodes = [n for n in G.nodes() if subnet in G.nodes[n]['subnets']]
        nx.draw_networkx_nodes(G, pos, nodelist=subnet_nodes, node_color=color, 
                             node_size=500, alpha=0.7)

    # Highlight bridge nodes
    bridge_nodes = [n for n in G.nodes() if G.nodes[n]['is_bridge']]
    nx.draw_networkx_nodes(G, pos, nodelist=bridge_nodes, node_color='red',
                          node_size=700, alpha=0.8)

    # Add labels
    labels = {node: f"{node}\n({','.join(G.nodes[node]['subnets'])})" 
             for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=8)
    for subnet, (x, y) in subnet_positions.items():
        plt.text(x, y + 0.4, subnet, fontsize=12, ha='center', 
                bbox=dict(facecolor=subnet_colors[subnet], alpha=0.5))

    plt.title("Mesh Network Topology with Subnet Groupings")
    plt.axis('off')
    plt.savefig(plots_dir / "mesh_topology.png", bbox_inches='tight', dpi=300)
    plt.close()
    print("Saved mesh_topology.png with subnet visualization")

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
    f.write(f"Most Active Node: {most_active} ({forward_counts[most_active]} messages)\n")
    f.write(f"Least Active Node: {least_active} ({forward_counts[least_active]} messages)\n\n")

    f.write("5. Advanced Metrics\n")
    f.write("-" * 20 + "\n")
    f.write(f"Message Delivery Ratio (>1 receiver): {delivery_ratio}\n")
    f.write(f"Nodes That Participated in Forwarding: {num_forwarded}\n")
    f.write(f"Dead-End Nodes (only received): {num_dead_ends}\n")
    f.write(f"Unique Flow Paths per Message (avg): {avg_unique_paths}\n")

    f.write("6. Delivery Quality\n")
    f.write("-" * 20 + "\n")
    f.write(f"Average Delivery Ratio: {avg_delivery_ratio}%\n")
    f.write(f"Total Duplicates (same msg to same node): {total_duplicates}\n\n")

    f.write("7. Energy Metrics\n")
    f.write("-" * 20 + "\n")
    f.write(f"Top Energy Node: {top_energy_node} with {top_energy_val} units\n")
    f.write(f"Avg Energy Used per Node: {avg_energy} units\n\n")

    f.write("8. Spread Efficiency\n")
    f.write("-" * 20 + "\n")
    f.write(f"Average Spread Efficiency (reach / hops): {avg_spread_eff}\n\n")

    f.write("9. Network Fairness\n")
    f.write("-" * 20 + "\n")
    f.write(f"Jain's Fairness Index on Node Load: {fairness}\n\n")

print("\nAnalysis complete! All outputs saved in 'mesh_analysis' directory:")
print(f"  - Plots: {plots_dir}")
print(f"  - Data: {data_dir}")
print(f"  - Metrics: {data_dir}/mesh_metrics.txt") 