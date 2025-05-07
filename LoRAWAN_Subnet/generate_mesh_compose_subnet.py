import yaml
import random
import math

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

# Create services
for i in range(1, num_nodes + 1):
    node_name = f"node{i}"
    listen_port = base_port + i
    subnet_idx = min((i - 1) // nodes_per_subnet, subnet_count - 1)
    subnet = subnet_names[subnet_idx]

   
    compose["services"][node_name] = {
        "build": ".",
        "container_name": node_name,
        "environment": [
            f"NODE_NAME={node_name}",
            f"LISTEN_PORT={listen_port}",
            f"NEXT_NODES=PLACEHOLDER",  
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


bridge_indices = [nodes_per_subnet * (i + 1) for i in range(subnet_count - 1)]
for idx in bridge_indices:
    if idx <= num_nodes:
        node_name = f"node{idx}"
        subnet_a = subnet_names[(idx - 1) // nodes_per_subnet]
        subnet_b = subnet_names[min(idx // nodes_per_subnet, subnet_count - 1)]
        if node_name in compose["services"]:
            compose["services"][node_name]["networks"] = {
                subnet_a: {"aliases": [node_name]},
                subnet_b: {"aliases": [node_name]}
            }


for i in range(1, num_nodes + 1):
    node_name = f"node{i}"
    service = compose["services"][node_name]
    node_networks = set(service["networks"].keys())
    reachable_nodes = []
    for j in range(1, num_nodes + 1):
        if j == i:
            continue
        other_node = f"node{j}"
        other_networks = set(compose["services"][other_node]["networks"].keys())
        if node_networks & other_networks:
            reachable_nodes.append(f"node{j}:{base_port + j}")
    next_nodes = random.sample(reachable_nodes, k=min(max_neighbors, len(reachable_nodes)))

    env = service["environment"]
    for idx, var in enumerate(env):
        if var.startswith("NEXT_NODES="):
            env[idx] = f"NEXT_NODES={','.join(next_nodes)}"
            break

# Output to YAML
with open("docker-compose.yml", "w") as f:
    yaml.dump(compose, f, default_flow_style=False)

print(f"✅ Generated docker-compose-subnet.yml for {num_nodes} nodes across {subnet_count} subnets.")
