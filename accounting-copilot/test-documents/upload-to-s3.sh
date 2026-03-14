#!/bin/bash

# Upload Test Documents to S3
# This script uploads all test documents to the accounting copilot S3 bucket

BUCKET_NAME="accounting-copilot-documents-280250685594"
REGION="eu-west-1"
PREFIX="documents/"

echo "=========================================="
echo "Uploading Test Documents to S3"
echo "=========================================="
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"
echo "Prefix: $PREFIX"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity --region $REGION &> /dev/null; then
    echo "ERROR: AWS credentials not configured or invalid"
    echo "Please run: aws configure"
    exit 1
fi

echo "✓ AWS CLI configured"
echo ""

# Upload customer invoices
echo "Uploading customer invoices..."
INVOICE_COUNT=$(ls -1 invoices/*.txt 2>/dev/null | wc -l)
if [ $INVOICE_COUNT -gt 0 ]; then
    aws s3 cp invoices/ s3://$BUCKET_NAME/$PREFIX --recursive --exclude "*.md" --region $REGION
    echo "✓ Uploaded $INVOICE_COUNT invoice files"
else
    echo "⚠ No invoice files found"
fi
echo ""

# Upload expense documents
echo "Uploading expense documents..."
EXPENSE_COUNT=$(ls -1 expenses/*.txt 2>/dev/null | wc -l)
if [ $EXPENSE_COUNT -gt 0 ]; then
    aws s3 cp expenses/ s3://$BUCKET_NAME/$PREFIX --recursive --exclude "*.md" --region $REGION
    echo "✓ Uploaded $EXPENSE_COUNT expense files"
else
    echo "⚠ No expense files found"
fi
echo ""

# Verify upload
echo "Verifying upload..."
TOTAL_FILES=$(aws s3 ls s3://$BUCKET_NAME/$PREFIX --recursive --region $REGION | grep -E '\.(txt|pdf)$' | wc -l)
echo "✓ Total files in S3: $TOTAL_FILES"
echo ""

echo "=========================================="
echo "Upload Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Check CloudWatch Logs for workflow_trigger Lambda"
echo "2. Monitor Step Functions executions"
echo "3. View transactions in the web interface"
echo "4. Test Financial Assistant queries"
echo ""
echo "Web Interface: http://accounting-copilot-web-280250685594.s3-website-eu-west-1.amazonaws.com"
echo ""
