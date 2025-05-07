#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color


print_status() {
    echo -e "${GREEN}[STATUS]${NC} $1"
}
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

cleanup_docker_version() {
    local version_dir=$1
    print_status "Cleaning up Docker resources for $version_dir..."
    
    # Stop all containers
    if [ -f "$version_dir/docker-compose.yml" ]; then
        docker-compose -f "$version_dir/docker-compose.yml" down --remove-orphans
    fi
    # Remove all containers
    docker ps -a | grep "$version_dir" | awk '{print $1}' | xargs -r docker rm -f
    
    # Remove all images
    docker images | grep "$version_dir" | awk '{print $3}' | xargs -r docker rmi -f
    
    # Remove all volumes
    docker volume ls | grep "$version_dir" | awk '{print $2}' | xargs -r docker volume rm -f
    
    # Remove all networks
    docker network ls | grep "$version_dir" | awk '{print $1}' | xargs -r docker network rm
}

# Function to clean Minikube resources
cleanup_minikube() {
    print_status "Cleaning up Minikube resources..."
    
    # Stop Minikube
    minikube stop 2>/dev/null
    
    # Delete Minikube cluster
    minikube delete 2>/dev/null
    
    # Remove all containers using mesh-node image
    eval $(minikube docker-env 2>/dev/null)
    docker ps -a --filter ancestor=mesh-node:latest -q | xargs -r docker rm -f
    
    # Remove the mesh-node image
    docker rmi mesh-node:latest --force 2>/dev/null
    
    # Remove all dangling volumes
    docker volume prune -f
    
    # Reset Docker environment
    eval $(minikube docker-env -u 2>/dev/null)
}

setup_venv() {
    print_status "Setting up single virtual environment for all versions..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating new virtual environment..."
        python3 -m venv venv
        
        
        source venv/bin/activate
        # Upgrade pip
        pip install --upgrade pip
        
        print_status "Installing common dependencies..."
        pip install networkx matplotlib numpy pandas seaborn scipy pyyaml
        
        # Install version-specific dependencies if requirements.txt exists
        for version in "LoRAWAN_Docker" "LoRAWAN_Subnet" "LoRAWAN_MutliSubnet" "LoRAWAN_MiniKube"; do
            if [ -f "$version/requirements.txt" ]; then
                print_status "Installing dependencies from $version..."
                pip install -r "$version/requirements.txt"
            fi
        done
        
    else
        # Activate existing virtual environment
        source venv/bin/activate
    fi
}

# Function to run a version
run_version() {
    local version_dir=$1
    local version_name=$2
    
    print_status "Running $version_name..."
    
    # Ensure we're in the virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi
    
   
    cleanup_docker_version "$version_dir"
    cd "$version_dir"
    
    # Check if start.sh exists and is executable
    if [ -f "start.sh" ]; then
        chmod +x start.sh
        ./start.sh
    else
        print_error "No start script found in $version_dir"
        exit 1
    fi
    

    cd - > /dev/null
    cleanup_docker_version "$version_dir"
    if [ "$version_dir" = "LoRAWAN_MiniKube" ]; then
        cleanup_minikube
    fi
}

# Function to collect data files
collect_data() {
    print_status "Collecting data files..."
    
    
    # Copy data files from each version
    cp LoRAWAN_Docker/mesh_analysis/data/*.txt Summary_LoRAWAN_DockerV1.txt
    cp LoRAWAN_Subnet/mesh_analysis/data/*.txt Summary_LoRAWAN_SubnetV2.txt
    cp LoRAWAN_MutliSubnet/mesh_analysis/data/*.txt Summary_LoRAWAN_MutliSubnetV3.txt
    cp LoRAWAN_MiniKube/mesh_analysis/data/*.txt Summary_LoRAWAN_minikubeV4.txt

    mkdir -p Report_LoRAWAN_Docker Report_LoRAWAN_Subnet Report_LoRAWAN_MutliSubnet Report_LoRAWAN_minikube

    cp LoRAWAN_Docker/mesh_analysis/plots/*.png Report_LoRAWAN_Docker/
    cp LoRAWAN_Subnet/mesh_analysis/plots/*.png Report_LoRAWAN_Subnet/
    cp LoRAWAN_MutliSubnet/mesh_analysis/plots/*.png Report_LoRAWAN_MutliSubnet/
    cp LoRAWAN_minikube/mesh_analysis/plots/*.png Report_LoRAWAN_minikube/
}

cleanup_docker() {
    print_status "Cleaning up all Docker resources..."
    docker system prune -af --volumes
}


print_status "Starting LoRAWAN versions execution..."
cleanup_docker
setup_venv

run_version "LoRAWAN_Docker" "Version 1 (Docker)"
run_version "LoRAWAN_minikube" "Version 4 (MiniKube)"
run_version "LoRAWAN_Subnet" "Version 2 (Subnet)"
run_version "LoRAWAN_MutliSubnet" "Version 3 (MultiSubnet)"

collect_data
print_status "Running comparison analysis..."
python3 AllComparision.py

cleanup_docker
cleanup_minikube

# Deactivate virtual environment
deactivate

print_status "All versions have been executed and compared successfully!" 