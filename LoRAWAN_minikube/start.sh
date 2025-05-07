#!/bin/bash
echo "Starting up Kubernetes Mesh Project..."

minikube start --extra-config=kubelet.max-pods=600
#minikube start --cpus=7 --memory=14000

eval $(minikube docker-env)

docker build -t mesh-node:latest .

kubectl apply -f mesh-headless-service.yaml
kubectl apply -f mesh-deployment.yaml
kubectl apply -f starter-node.yaml

eval $(minikube docker-env -u)

echo "Waiting 60 seconds for pods to stabilize..."
while true; do
    pending=$(kubectl get pods --no-headers | grep -c Pending)
    not_running=$(kubectl get pods --no-headers | grep -v Running | wc -l)
    total=$(kubectl get pods --no-headers | wc -l)
    running=$(kubectl get pods --no-headers | grep -c Running)
    echo "Pods: $running/$total Running, $pending Pending"
    if [[ $pending -eq 0 && $not_running -eq 0 ]]; then
        echo "All pods are Running!"
        break
    fi
    sleep 5
done

echo "Sleep 60 seconds to ensure all pods are up and running..."
sleep 60


echo "Showing node communication logs for 10 seconds..."
kubectl logs -l app=mesh-node -f --max-log-requests=150 &
LOGS_PID=$!
sleep 10
kill $LOGS_PID 2>/dev/null

echo "Waiting for 15 seconds to ensure logs are available..."
sleep 15

echo " Cleaning old collected_logs..."
rm -rf collected_logs
mkdir -p collected_logs
echo "Fetching logs from all mesh-node pods"
for pod in $(kubectl get pods -l app=mesh-node -o jsonpath='{.items[*].metadata.name}'); do
    echo "Fetching log from $pod"
    kubectl cp $pod:/app/events.json collected_logs/${pod}_events.json 2>/dev/null || echo "No events.json found in $pod"

done
echo "Fetch Complete"

# # Install required Python packages
# python3 -m venv venv
# source venv/bin/activate
# pip install networkx matplotlib numpy pandas seaborn scipy

# Generate Metrics
echo "Generating Metrics"
mkdir report
echo "Analysing main metrics"
python3 analyze_mesh.py


echo "Cleaning up Kubernetes Mesh Project..."
# Delete deployments and service
kubectl delete deployment mesh-nodes --ignore-not-found
kubectl delete deployment mesh-starter --ignore-not-found
kubectl delete service mesh-node --ignore-not-found
# Stop Minikube
docker volume prune -f
minikube stop

eval $(minikube docker-env)

docker ps -a --filter ancestor=mesh-node:latest -q | xargs -r docker rm -f

docker rmi mesh-node:latest --force 2>/dev/null

docker volume prune -f

echo " Cleanup complete."

# kubectl logs deployment/mesh-starter --follow

# sleep(10)

# exit 0

# kubectl rollout restart deployment mesh-nodes
# kubectl rollout restart deployment mesh-starter