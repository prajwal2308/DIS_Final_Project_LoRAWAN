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
