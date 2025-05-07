#!/bin/bash

echo "Installing requirements"
pip install -r requirements.txt

echo "Generating docker-compose.yml"
python generate_mesh_compose.py

echo "Starting containers in background"
docker-compose up -d --build &
DOCKER_PID=$!

echo "Waiting for containers to initialize..."
sleep 15  # Increased sleep time to ensure all containers are ready

echo "Checking container status"
docker-compose ps

# Wait for all containers to be healthy
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

# Wait for the background process to complete
wait $DOCKER_PID
sleep 10
echo "Showing node communication logs for 15 seconds..."
docker-compose logs -f &
LOGS_PID=$!
sleep 15
kill $LOGS_PID 2>/dev/null


echo "Fetching logs"
mkdir -p ./collected_logs
for i in $(seq 1 120); do
    container="node$i"
    if docker ps -a --format '{{.Names}}' | grep -q "^$container$"; then
        echo "Fetching log from $container..."
        docker cp $container:/app/events.json ./collected_logs/${container}_events.json 2>/dev/null || echo "  No events.json found in $container"
    fi
done
echo "✅ Done fetching logs. Check ./collected_logs/"




# Run analysis scripts
echo "Running analysis scripts..."
python analyze_mesh.py

echo "Analysis complete."

echo "Run ( docker-compose down )to stop and remove containers"

docker-compose down
echo "Cleanup complete. Exiting."
