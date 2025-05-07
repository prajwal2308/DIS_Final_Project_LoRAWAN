# Simulating a LoRaWAN Style Mesh Network Using Containers

## Overview
This project contains multiple versions LoRAWAN implementations and analysis tools. It includes Docker setups, Minikube configurations, and scripts to start different versions of the LoRAWAN network.

## Prerequisites
- Docker and Docker Compose installed
- Minikube installed 
- Python
- Bash shell to run shell scripts
- Virtual Environment (venv) for python dependencies. Created within script.sh files

## Warnings
- Script has Deeper cleanup of Docker Images, Containers, Volumes and Networks used within project <br>
- Necessary backup is required if there are other containers.

## Run time
- Run time depends on the choice of script version
- `./start_two_versions.sh` (takes approx: 4-8 mins)
- `./start_all_versions.sh` (takes approx 8-15 mins)

## How to Run

### Starting Different Versions in Terminal 

There are multiple version of scripts. Use of first version is recommended.<br>

1. For running only two version of LoRAWAN Implementation using Docker and minikube.  (Recommended) <br>
`chmod +x start_two_versions.sh` <br>
`./start_two_versions.sh` <br>
2. For running all four version of LoRAWAN Implementation use <br>
`chmod +x start_all_versions.sh` <br>
`./start_all_versions.sh` 

### Running Python Scripts 
### (Not required to run if ./start_*_versions.sh is ran)
- Creating of Virtual Environment is needed for plot creations and graph (start_*_versions does for you)<br>
- Python scripts `AllComparision.py` is run from within shart_*_versions script for analysis.

## Comparision Plots and Visual analysis

- Metrics depend on the load on CPU, Better CPU handles load, minikube performs better.
- Once `start_*_version.sh` is ran, It automatically fetches the summay of metrics and stores in the root directry and it can be found under `comparision_plots` dir.
- Additionally for each version, All the plots related to metrics is stored under `Report*_LoRAWAN_*` directory
- Summary text file is stored in `Summary_LoRAWAN_*.txt `

##

## Logs and Ignored Files
- All `collected_logs` directories are ignored in git.
- Python virtual environments (`venv`) are also ignored.

## Additional Notes
- Ensure you have the necessary permissions to run Docker and Kubernetes commands.
- Modify configuration files as needed for your environment.
- Tested for upto 500+ nodes needed. To test that, run `./start.sh` script inside `LoRAWAN_minikube` dir. (need to configure `minikube start --cpus=7 --memory=14000 -extra-config=kubelet.max-pods=600` inside `./start.sh`.
