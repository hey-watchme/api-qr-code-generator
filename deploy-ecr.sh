#!/bin/bash

# WatchMe QR Code Generator API - ECR Deployment Script
# Builds and pushes Docker image to AWS ECR

set -e

# Configuration
AWS_REGION="ap-southeast-2"
AWS_ACCOUNT_ID="754724220380"
ECR_REPOSITORY="watchme-api-qr-code-generator"
IMAGE_TAG="latest"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}WatchMe QR Code Generator - ECR Deploy${NC}"
echo -e "${BLUE}========================================${NC}"

# Step 1: Login to ECR
echo -e "\n${GREEN}[1/4] Logging in to ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Step 2: Build Docker image
echo -e "\n${GREEN}[2/4] Building Docker image...${NC}"
docker build -f Dockerfile.prod -t $ECR_REPOSITORY:$IMAGE_TAG .

# Step 3: Tag image
echo -e "\n${GREEN}[3/4] Tagging image...${NC}"
docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# Add timestamp tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$TIMESTAMP

# Step 4: Push to ECR
echo -e "\n${GREEN}[4/4] Pushing to ECR...${NC}"
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$TIMESTAMP

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nImage pushed to:"
echo -e "  ${BLUE}$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG${NC}"
echo -e "  ${BLUE}$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$TIMESTAMP${NC}"
echo -e "\nNext steps:"
echo -e "  1. SSH to EC2: ${BLUE}ssh -i ~/watchme-key.pem ubuntu@3.24.16.82${NC}"
echo -e "  2. Restart service: ${BLUE}sudo systemctl restart watchme-qr-code-generator${NC}"
