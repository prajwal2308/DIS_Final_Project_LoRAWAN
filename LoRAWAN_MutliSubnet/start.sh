#!/bin/bash

echo "Installing requirements"
pip install -r requirements.txt

echo "Generating docker-compose.yml"
#python generate_mesh_compose.py
python generate_mesh_compose_subnet.py

echo "Starting containers in background"
docker-compose up -d --build &
DOCKER_PID=$!

echo "Waiting for containers to initialize..."
sleep 15  

echo "Checking container status"
docker-compose ps

echo "Waiting for containers to be healthy..."
while true; do
    if docker-compose ps | grep -q "unhealthy"; then
        echo "Some containers are still pending, waiting..."
        sleep 10
    else
        echo "All containers are healthy!"
        break
    fi
done

wait $DOCKER_PID
sleep 10

echo "Showing node communication logs for 10 seconds..."
docker-compose logs -f &
LOGS_PID=$!
sleep 10
kill $LOGS_PID 2>/dev/null

echo "Waiting for 15 seconds to ensure logs are available..."
sleep 15

echo "Fetching logs"
mkdir -p ./collected_logs
for i in $(seq 1 150); do
    container="node$i"
    if docker ps -a --format '{{.Names}}' | grep -q "^$container$"; then
        echo "Fetching log from $container..."
        docker cp $container:/app/events.json ./collected_logs/${container}_events.json 2>/dev/null || echo "  No events.json found in $container"
    fi
done
echo "✅ Done fetching logs. Check ./collected_logs/"


echo "Running analysis scripts..."
python analyze_mesh.py

echo "Analysis complete."

echo "Run ( docker-compose down )to stop and remove containers"

docker-compose down
