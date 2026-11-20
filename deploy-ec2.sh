#!/bin/bash
# Creates the EC2 instance for this workshop with the AWS CLI (e.g. from the
# AWS Academy Sandbox terminal). Equivalent to the console steps in README.md:
# Ubuntu 24.04 + security group with HTTP (80) open + ec2-user-data.sh as user data.
set -euo pipefail

NAME="demo_docker"
SG_NAME="stock-market-sg"
REPO_RAW="https://raw.githubusercontent.com/Cristian-droi/taller1-web-service/main"

curl -fsSL -o /tmp/ec2-user-data.sh "$REPO_RAW/ec2-user-data.sh"

echo "==> Latest Ubuntu 24.04 AMI (Canonical)"
AMI=$(aws ec2 describe-images --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" "Name=state,Values=available" \
  --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)
echo "    $AMI"

echo "==> Public subnet"
SUBNET=$(aws ec2 describe-subnets --filters Name=map-public-ip-on-launch,Values=true \
  --query 'Subnets[0].SubnetId' --output text)
if [ "$SUBNET" = "None" ]; then
  SUBNET=$(aws ec2 describe-subnets --query 'Subnets[0].SubnetId' --output text)
fi
VPC=$(aws ec2 describe-subnets --subnet-ids "$SUBNET" --query 'Subnets[0].VpcId' --output text)
echo "    $SUBNET ($VPC)"

echo "==> Security group with HTTP (80) open"
SG=$(aws ec2 describe-security-groups --filters Name=group-name,Values="$SG_NAME" Name=vpc-id,Values="$VPC" \
  --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG" = "None" ]; then
  SG=$(aws ec2 create-security-group --group-name "$SG_NAME" --description "Stock market web service: HTTP" \
    --vpc-id "$VPC" --query GroupId --output text)
  aws ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 80 --cidr 0.0.0.0/0 >/dev/null
fi
echo "    $SG"

echo "==> Launching instance $NAME"
INSTANCE=$(aws ec2 run-instances --image-id "$AMI" --instance-type t3.micro \
  --subnet-id "$SUBNET" --security-group-ids "$SG" --associate-public-ip-address \
  --user-data file:///tmp/ec2-user-data.sh \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME}]" \
  --query 'Instances[0].InstanceId' --output text)
echo "    $INSTANCE"

aws ec2 wait instance-running --instance-ids "$INSTANCE"
DNS=$(aws ec2 describe-instances --instance-ids "$INSTANCE" \
  --query 'Reservations[0].Instances[0].[PublicDnsName,PublicIpAddress]' --output text)

echo
echo "Instance running: $INSTANCE  ->  $DNS"
echo "Docker install + container start takes ~3 minutes. Then open: http://$(echo "$DNS" | awk '{print $1}')/"
echo "Terminate when done: aws ec2 terminate-instances --instance-ids $INSTANCE"
