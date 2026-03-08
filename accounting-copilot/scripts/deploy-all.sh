#!/bin/bash
# Complete deployment script - deploys infrastructure, Lambda functions, and frontend
# This is the master deployment script that orchestrates all deployment steps

set -e

PROJECT_NAME="accounting-copilot"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

echo "=========================================="
echo "AI Accounting Copilot - Complete Deployment"
echo "=========================================="
echo "Project: ${PROJECT_NAME}"
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo ""

# Step 1: Deploy Infrastructure
echo "Step 1/4: Deploying infrastructure..."
./scripts/deploy-infrastructure.sh

# Step 2: Build Lambda packages
echo ""
echo "Step 2/4: Building Lambda packages..."
./scripts/build-lambda-packages.sh

# Step 3: Deploy Lambda functions
echo ""
echo "Step 3/4: Deploying Lambda functions..."
./scripts/deploy-lambdas.sh

# Step 4: Deploy frontend
echo ""
echo "Step 4/4: Deploying frontend..."
cd frontend
./deploy.sh
cd ..

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Enable Bedrock model access (Claude 3 Haiku) in AWS Console"
echo "2. Subscribe to SNS topics for email notifications"
echo "3. Create test user in Cognito"
echo "4. Test the application"
echo ""
echo "For detailed instructions, see DEPLOYMENT.md"
