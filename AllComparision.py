import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import glob


plt.style.use('ggplot')
sns.set_theme(style="whitegrid")
version_files = glob.glob("Summary_LoRAWAN*.txt")
VERSIONS = {}
for vf in version_files:
    if "DockerV1" in vf:
        version_name = "Docker V1"
    elif "SubnetV2" in vf:
        version_name = "Docker V2"
    elif "MutliSubnetV3" in vf:
        version_name = "Docker V3"
    elif "minikubeV4" in vf:
        version_name = "Kubernetes"
    else:
        version_name = vf.replace(".txt", "")
    VERSIONS[version_name] = vf

# Metrics to extract
METRIC_KEYS = [
    "Total Unique Messages",
    "Total Nodes",
    "Nodes That Received Messages",
    "TTL Expiry Events",
    "Maximum Hops",
    "Minimum Hops",
    "Average Hops",
    "Maximum Latency",
    "Minimum Latency",
    "Average Latency",
    "Most Active Node",
    "Least Active Node",
    "Message Delivery Ratio",
    "Dead-End Nodes",
    "Unique Flow Paths per Message",
    "Average Delivery Ratio",
    "Top Energy Node",
    "Avg Energy Used per Node",
    "Average Spread Efficiency",
    "Jain's Fairness Index"
]

def extract_metrics(filepath):
    with open(filepath) as f:
        lines = f.readlines()

    data = {}
    for line in lines:
        for key in METRIC_KEYS:
            if key in line:
                parts = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                if parts:
                    data[key] = float(parts[-1])
                else:
                    data[key] = line.strip().split(":")[-1].strip()
    return data

# Combine all metrics
rows = []
for version, path in VERSIONS.items():
    metrics = extract_metrics(path)
    metrics["Version"] = version
    rows.append(metrics)

df = pd.DataFrame(rows).set_index("Version")


os.makedirs("comparison_plots", exist_ok=True)

plt.figure(figsize=(20, 15))

# 1. Network Performance Metrics
plt.subplot(2, 2, 1)
metrics = ["Average Delivery Ratio", "Average Spread Efficiency"]
df[metrics].plot(kind='bar', ax=plt.gca())
plt.title("Network Performance", pad=20, size=14)
plt.ylabel("Ratio", size=12)
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
# Add value labels
for i, metric in enumerate(metrics):
    for j, v in enumerate(df[metric]):
        plt.text(j, v, f'{v:.2%}', ha='center', va='bottom')

# 2. Latency Metrics
# plt.subplot(2, 2, 2)
# latency_metrics = ["Minimum Latency", "Average Latency", "Maximum Latency"]
# df[latency_metrics].plot(kind='bar', ax=plt.gca())
# plt.title("Network Latency", pad=20, size=14)
# plt.ylabel("Latency (ms)", size=12)
# plt.xticks(rotation=45)
# plt.grid(True, linestyle='--', alpha=0.7)
# plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
# # Add value labels
# for i, metric in enumerate(latency_metrics):
#     for j, v in enumerate(df[metric]):
#         plt.text(j, v, f'{v:.1f}', ha='center', va='bottom')

# 2. Message Statistics
plt.subplot(2, 2, 2)
message_metrics = ["Total Unique Messages", "TTL Expiry Events"]
df[message_metrics].plot(kind='bar', ax=plt.gca())
plt.title("Message Statistics", pad=20, size=14)
plt.ylabel("Count", size=12)
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
# Add value labels
for i, metric in enumerate(message_metrics):
    for j, v in enumerate(df[metric]):
        plt.text(j, v, f'{v:.0f}', ha='center', va='bottom')

# 3. Node Statistics
plt.subplot(2, 2, 3)
node_metrics = ["Total Nodes", "Nodes That Received Messages", "Dead-End Nodes"]
df[node_metrics].plot(kind='bar', ax=plt.gca())
plt.title("Node Statistics", pad=20, size=14)
plt.ylabel("Number of Nodes", size=12)
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
# Add value labels
for i, metric in enumerate(node_metrics):
    for j, v in enumerate(df[metric]):
        plt.text(j, v, f'{v:.0f}', ha='center', va='bottom')



# 4. Fairness Index
plt.subplot(2, 2, 4)
df["Jain's Fairness Index"].plot(kind='bar', ax=plt.gca(), color='lightgreen')
plt.title("Network Fairness", pad=20, size=14)
plt.ylabel("Fairness Index", size=12)
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.7)
# Add value labels
for i, v in enumerate(df["Jain's Fairness Index"]):
    plt.text(i, v, f'{v:.3f}', ha='center', va='bottom')  

plt.tight_layout()
plt.savefig("comparison_plots/network_dashboard.png", bbox_inches='tight', dpi=300)
plt.close()

plt.figure(figsize=(20, 15))



# 2. Hop Statistics
plt.subplot(2, 2, 1)
hop_metrics = ["Minimum Hops", "Average Hops", "Maximum Hops"]
df[hop_metrics].plot(kind='bar', ax=plt.gca())
plt.title("Message Hop Statistics", pad=20, size=14)
plt.ylabel("Number of Hops", size=12)
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
# Add value labels
for i, metric in enumerate(hop_metrics):
    for j, v in enumerate(df[metric]):
        plt.text(j, v, f'{v:.1f}', ha='center', va='bottom')


# 4. Energy and Efficiency
plt.subplot(2, 2, 2)
energy_metrics = ["Avg Energy Used per Node", "Top Energy Node"]
df[energy_metrics].plot(kind='bar', ax=plt.gca())
plt.title("Energy Usage", pad=20, size=14)
plt.ylabel("Energy Units", size=12)
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
# Add value labels
for i, metric in enumerate(energy_metrics):
    for j, v in enumerate(df[metric]):
        plt.text(j, v, f'{v:.1f}', ha='center', va='bottom')

# # 3. Network Coverage
# plt.subplot(2, 2, 3)
# coverage = (df["Nodes That Received Messages"] / df["Total Nodes"] * 100)
# coverage.plot(kind='bar', ax=plt.gca(), color='skyblue')
# plt.title("Network Coverage", pad=20, size=14)
# plt.ylabel("Percentage of Nodes Reached", size=12)
# plt.xticks(rotation=45)
# plt.grid(True, linestyle='--', alpha=0.7)
# # Add value labels
# for i, v in enumerate(coverage):
#     plt.text(i, v, f'{v:.1f}%', ha='center', va='bottom')

plt.tight_layout()
plt.savefig("comparison_plots/network_dashboard2.png", bbox_inches='tight', dpi=300)
plt.close()
