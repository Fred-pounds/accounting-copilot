#!/bin/bash
# Deploy Lambda functions via S3 (for large packages)

set -e

PROJECT_NAME="accounting-copilot"
REGION="${AWS_REGION:-eu-west-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="${PROJECT_NAME}-documents-${ACCOUNT_ID}"

echo "Deploying Lambda functions via S3 for ${PROJECT_NAME} in ${REGION}..."
echo "Using S3 bucket: ${S3_BUCKET}"

# Check if packages exist
if [ ! -d "lambda-packages" ]; then
    echo "Error: lambda-packages directory not found"
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
    "transaction_api"
    "document_api"
    "audit_trail_api"
    "approval_manager"
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
    
    # Upload to S3
    S3_KEY="lambda-packages/${FUNCTION}.zip"
    if aws s3 cp "${ZIP_FILE}" "s3://${S3_BUCKET}/${S3_KEY}" --region "${REGION}" > /dev/null 2>&1; then
        echo "  ✓ Uploaded to S3"
    else
        echo "  ✗ Failed to upload to S3"
        FAILED=$((FAILED + 1))
        continue
    fi
    
    # Update Lambda function from S3
    if aws lambda update-function-code \
        --function-name "${PROJECT_NAME}-${FUNCTION}" \
        --s3-bucket "${S3_BUCKET}" \
        --s3-key "${S3_KEY}" \
        --region "${REGION}" \
        --query 'FunctionName' \
        --output text > /dev/null 2>&1; then
        echo "  ✓ ${FUNCTION} deployed successfully"
        DEPLOYED=$((DEPLOYED + 1))
    else
        echo "  ✗ Failed to deploy ${FUNCTION}"
        FAILED=$((FAILED + 1))
    fi
    
    # Clean up S3 (optional - comment out if you want to keep packages)
    # aws s3 rm "s3://${S3_BUCKET}/${S3_KEY}" --region "${REGION}" > /dev/null 2>&1
done

echo ""
echo "Deployment Summary:"
echo "  Deployed: ${DEPLOYED}"
echo "  Failed: ${FAILED}"

if [ ${FAILED} -gt 0 ]; then
    echo ""
    echo "Some deployments failed."
    exit 1
fi

echo ""
echo "All Lambda functions deployed successfully!"
