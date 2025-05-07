import yaml
import random
import math
from itertools import combinations

# Configuration
num_nodes = 120
base_port = 5000
max_neighbors = 3
cpu_limit = "0.05"  # 5% CPU
mem_limit = "20m"   # 20MB memory
subnet_count = 4
nodes_per_subnet = math.ceil(num_nodes / subnet_count)
subnet_names = [f"meshnet{i+1}" for i in range(subnet_count)]

# Initialize docker-compose structure
compose = {
    "services": {},
    "networks": {subnet: {"driver": "bridge"} for subnet in subnet_names}
}

# Create regular node services
for i in range(1, num_nodes + 1):
    node_name = f"node{i}"
    listen_port = base_port + i
    subnet_idx = min((i - 1) // nodes_per_subnet, subnet_count - 1)
    subnet = subnet_names[subnet_idx]

    # We'll fill NEXT_NODES after all services are created and bridge nodes are set
    compose["services"][node_name] = {
        "build": ".",
        "container_name": node_name,
        "environment": [
            f"NODE_NAME={node_name}",
            f"LISTEN_PORT={listen_port}",
            f"NEXT_NODES=PLACEHOLDER",  # Will fill after bridge logic
            f"START_NODE={'true' if i == 1 else 'false'}"
        ],
        "networks": {
            subnet: {"aliases": [node_name]}
        },
        "deploy": {
            "resources": {
                "limits": {
                    "cpus": cpu_limit,
                    "memory": mem_limit
                }
            }
        }
    }

# Add bridge nodes for every pair of subnets
bridge_pairs = list(combinations(subnet_names, 2))
bridge_node_idx = num_nodes + 1  # Start after the last regular node
for subnet_a, subnet_b in bridge_pairs:
    node_name = f"bridge_{subnet_a}_{subnet_b}"
    compose["services"][node_name] = {
        "build": ".",
        "container_name": node_name,
        "environment": [
            f"NODE_NAME={node_name}",
            f"LISTEN_PORT={base_port + bridge_node_idx}",
            f"NEXT_NODES=PLACEHOLDER",
            f"START_NODE=false"
        ],
        "networks": {
            subnet_a: {"aliases": [node_name]},
            subnet_b: {"aliases": [node_name]}
        },
        "deploy": {
            "resources": {
                "limits": {
                    "cpus": cpu_limit,
                    "memory": mem_limit
                }
            }
        }
    }
    bridge_node_idx += 1

# Now, update NEXT_NODES for all nodes (including bridges)
all_node_names = list(compose["services"].keys())
for node_name in all_node_names:
    service = compose["services"][node_name]
    node_networks = set(service["networks"].keys())
    # Find all nodes that share at least one subnet with this node
    reachable_nodes = []
    for other_node in all_node_names:
        if other_node == node_name:
            continue
        other_networks = set(compose["services"][other_node]["networks"].keys())
        if node_networks & other_networks:
            # Use the correct port for each node
            env = compose["services"][other_node]["environment"]
            listen_port = None
            for var in env:
                if var.startswith("LISTEN_PORT="):
                    listen_port = var.split("=", 1)[1]
                    break
            if listen_port:
                reachable_nodes.append(f"{other_node}:{listen_port}")
    next_nodes = random.sample(reachable_nodes, k=min(max_neighbors, len(reachable_nodes)))
    # Update environment
    env = service["environment"]
    for idx, var in enumerate(env):
        if var.startswith("NEXT_NODES="):
            env[idx] = f"NEXT_NODES={','.join(next_nodes)}"
            break

# Output to YAML
with open("docker-compose.yml", "w") as f:
    yaml.dump(compose, f, default_flow_style=False)

print(f"✅ Generated docker-compose-subnet.yml for {num_nodes} nodes across {subnet_count} subnets, with full inter-subnet bridges.")
