import yaml
import random

num_nodes = 120
base_port = 5000
max_neighbors = 3
cpu_limit = "0.05"  # 5% of a CPU
mem_limit = "20m"  # 20MB RAM

compose = {
    "services": {},
    "networks": {
        "meshnet": {
            "driver": "bridge"
        }
    }
}

for i in range(1, num_nodes + 1):
    node_name = f"node{i}"
    listen_port = base_port + i

    next_nodes = random.sample(
        [f"node{j}:{base_port + j}" for j in range(1, num_nodes + 1) if j != i],
        k=min(max_neighbors, num_nodes - 1)
    )

    compose["services"][node_name] = {
        "build": ".",
        "container_name": node_name,
        "environment": [
            f"NODE_NAME={node_name}",
            f"LISTEN_PORT={listen_port}",
            f"NEXT_NODES={','.join(next_nodes)}",
            f"START_NODE={'true' if i == 1 else 'false'}"
        ],
        "networks": {
            "meshnet": {
                "aliases": [node_name]
            }
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

with open("docker-compose.yml", "w") as f:
    yaml.dump(compose, f, default_flow_style=False)

print(f"✅ docker-compose.yml for {num_nodes} nodes generated with resource constraints.")
