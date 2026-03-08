#!/bin/bash
# Update Lambda environment variables

REGION="eu-west-1"
PROJECT="accounting-copilot"

# Get values from Terraform outputs
DYNAMODB_TABLE="AccountingCopilot"
DOCUMENTS_BUCKET="accounting-copilot-documents-280250685594"
WEBSITE_BUCKET="accounting-copilot-web-280250685594"
COGNITO_USER_POOL_ID="eu-west-1_dRl4wmfEE"
COGNITO_CLIENT_ID="61u3hub5dftsntsh9o4tasis75"
WORKFLOW_ARN="arn:aws:states:eu-west-1:280250685594:stateMachine:accounting-copilot-document-processing"
SNS_PENDING_APPROVALS="arn:aws:sns:eu-west-1:280250685594:accounting-copilot-pending-approvals"
SNS_OCR_FAILURES="arn:aws:sns:eu-west-1:280250685594:accounting-copilot-ocr-failures"
SNS_UNMATCHED_TRANSACTIONS="arn:aws:sns:eu-west-1:280250685594:accounting-copilot-unmatched-transactions"
SNS_APPROVAL_REMINDERS="arn:aws:sns:eu-west-1:280250685594:accounting-copilot-approval-reminders"

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

echo "Updating Lambda environment variables..."
echo ""

for FUNC in "${FUNCTIONS[@]}"; do
    echo "Updating $FUNC..."
    
    aws lambda update-function-configuration \
        --function-name "${PROJECT}-${FUNC}" \
        --environment Variables="{DYNAMODB_TABLE=${DYNAMODB_TABLE},DOCUMENTS_BUCKET=${DOCUMENTS_BUCKET},WEBSITE_BUCKET=${WEBSITE_BUCKET},COGNITO_USER_POOL_ID=${COGNITO_USER_POOL_ID},COGNITO_CLIENT_ID=${COGNITO_CLIENT_ID},WORKFLOW_ARN=${WORKFLOW_ARN},SNS_PENDING_APPROVALS=${SNS_PENDING_APPROVALS},SNS_OCR_FAILURES=${SNS_OCR_FAILURES},SNS_UNMATCHED_TRANSACTIONS=${SNS_UNMATCHED_TRANSACTIONS},SNS_APPROVAL_REMINDERS=${SNS_APPROVAL_REMINDERS},XRAY_ENABLED=true,LOG_LEVEL=INFO}" \
        --region "$REGION" \
        --output text \
        --query 'FunctionName' 2>&1 | head -1
    
    if [ $? -eq 0 ]; then
        echo "✓ $FUNC updated"
    else
        echo "✗ $FUNC failed"
    fi
    echo ""
done

echo "Environment variables update complete!"
