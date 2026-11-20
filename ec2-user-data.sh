#!/bin/bash
# EC2 "User data" script (Ubuntu 24.04). Runs once at first boot as root:
# installs Docker from the official repository and starts the service on port 80.
# Replace DOCKERHUB_USER before pasting it into the EC2 launch wizard.
set -euxo pipefail

DOCKERHUB_USER="YOUR_DOCKERHUB_USER"
IMAGE="${DOCKERHUB_USER}/stock-market:2.0"

apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Allow the 'ubuntu' user to run containers without sudo (step required by the workshop)
usermod -aG docker ubuntu

# Public port 80 (HTTP, opened in the security group) -> container port 5000
docker run -d --name stock-market --restart unless-stopped -p 80:5000 "$IMAGE"
