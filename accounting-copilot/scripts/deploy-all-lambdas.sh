#!/bin/bash
# Deploy all Lambda functions from S3

REGION="eu-west-1"
BUCKET="accounting-copilot-documents-280250685594"
PROJECT="accounting-copilot"

FUNCTIONS=(
    "document-upload-handler"
    "ocr-processor"
    "transaction-classifier"
    "data-validator"
    "reconciliation-engine"
    "dashboard-api"
    "financial-assistant"
    "audit-logger"
    "transaction-api"
    "document-api"
    "audit-trail-api"
    "approval-manager"
)

echo "Deploying all Lambda functions..."
echo ""

for FUNC in "${FUNCTIONS[@]}"; do
    # Convert hyphen to underscore for zip file name
    ZIP_NAME=$(echo "$FUNC" | tr '-' '_')
    
    echo "Deploying $FUNC..."
    
    aws lambda update-function-code \
        --function-name "${PROJECT}-${FUNC}" \
        --s3-bucket "$BUCKET" \
        --s3-key "lambda-packages/${ZIP_NAME}.zip" \
        --region "$REGION" \
        --output text \
        --query 'FunctionName'
    
    if [ $? -eq 0 ]; then
        echo "✓ $FUNC deployed"
    else
        echo "✗ $FUNC failed"
    fi
    echo ""
done

echo "Deployment complete!"
