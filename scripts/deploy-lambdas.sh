#!/bin/bash
# Deploy Lambda functions to AWS
# This script uploads Lambda deployment packages to AWS

set -e

PROJECT_NAME="accounting-copilot"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

echo "Deploying Lambda functions for ${PROJECT_NAME} (${ENVIRONMENT}) in ${REGION}..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    exit 1
fi

# Check if packages exist
if [ ! -d "lambda-packages" ]; then
    echo "Error: lambda-packages directory not found"
    echo "Run: ./scripts/build-lambda-packages.sh first"
    exit 1
fi

# List of Lambda functions
FUNCTIONS=(
    "document_upload_handler"
    "ocr_processor"
    "transaction_classifier"
    "data_validator"
    "reconciliation_engine"
    "dashboard_api"
    "financial_assistant"
    "audit_logger"
)

# Deploy each function
DEPLOYED=0
FAILED=0

for FUNCTION in "${FUNCTIONS[@]}"; do
    ZIP_FILE="lambda-packages/${FUNCTION}.zip"
    
    if [ ! -f "${ZIP_FILE}" ]; then
        echo "⚠ Skipping ${FUNCTION} - package not found"
        FAILED=$((FAILED + 1))
        continue
    fi
    
    echo "Deploying ${FUNCTION}..."
    
    # Try to update function code
    if aws lambda update-function-code \
        --function-name "${PROJECT_NAME}-${ENVIRONMENT}-${FUNCTION}" \
        --zip-file "fileb://${ZIP_FILE}" \
        --region "${REGION}" \
        > /dev/null 2>&1; then
        echo "✓ ${FUNCTION} deployed successfully"
        DEPLOYED=$((DEPLOYED + 1))
    else
        echo "✗ Failed to deploy ${FUNCTION}"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "Deployment Summary:"
echo "  Deployed: ${DEPLOYED}"
echo "  Failed: ${FAILED}"

if [ ${FAILED} -gt 0 ]; then
    echo ""
    echo "Some deployments failed. Check that Lambda functions exist in AWS."
    exit 1
fi

echo ""
echo "All Lambda functions deployed successfully!"
