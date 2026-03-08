#!/bin/bash
# Deploy CloudFormation stack or Terraform infrastructure
# This script deploys the complete AWS infrastructure

set -e

PROJECT_NAME="accounting-copilot"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

echo "Deploying infrastructure for ${PROJECT_NAME} (${ENVIRONMENT}) in ${REGION}..."

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "Error: Terraform is not installed"
    echo "Please install Terraform: https://www.terraform.io/downloads"
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Verify AWS credentials
echo "Verifying AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "Error: AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

# Navigate to infrastructure directory
cd infrastructure

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Validate configuration
echo "Validating Terraform configuration..."
terraform validate

# Plan deployment
echo "Planning infrastructure changes..."
terraform plan -out=tfplan

# Ask for confirmation
read -p "Do you want to apply these changes? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    rm -f tfplan
    exit 0
fi

# Apply changes
echo "Applying infrastructure changes..."
terraform apply tfplan

# Clean up plan file
rm -f tfplan

# Output important values
echo ""
echo "Infrastructure deployed successfully!"
echo "=========================================="
terraform output

# Save outputs to file for CI/CD
terraform output -json > ../terraform-outputs.json
echo ""
echo "Outputs saved to terraform-outputs.json"

cd ..
