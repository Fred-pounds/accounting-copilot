#!/bin/bash

# AI Accounting Copilot - CloudFormation Deployment Script
# Alternative to setup-infrastructure.sh using CloudFormation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}AI Accounting Copilot - CloudFormation Deployment${NC}"
echo "=============================================="

# Configuration
STACK_NAME="${STACK_NAME:-accounting-copilot-frontend}"
AWS_REGION="${AWS_REGION:-us-east-1}"
TEMPLATE_FILE="cloudformation-template.yaml"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if template exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}Error: CloudFormation template not found: $TEMPLATE_FILE${NC}"
    exit 1
fi

echo -e "Stack Name: ${GREEN}${STACK_NAME}${NC}"
echo -e "Region: ${GREEN}${AWS_REGION}${NC}"
echo ""

# Check if stack exists
STACK_EXISTS=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${AWS_REGION} \
    2>&1 || true)

if echo "$STACK_EXISTS" | grep -q "does not exist"; then
    # Create new stack
    echo -e "${BLUE}Creating new CloudFormation stack...${NC}"
    
    aws cloudformation create-stack \
        --stack-name ${STACK_NAME} \
        --template-body file://${TEMPLATE_FILE} \
        --region ${AWS_REGION} \
        --capabilities CAPABILITY_IAM
    
    echo -e "${YELLOW}Waiting for stack creation to complete...${NC}"
    echo -e "${YELLOW}This may take 15-20 minutes...${NC}"
    
    aws cloudformation wait stack-create-complete \
        --stack-name ${STACK_NAME} \
        --region ${AWS_REGION}
    
    echo -e "${GREEN}✓ Stack created successfully${NC}"
else
    # Update existing stack
    echo -e "${BLUE}Updating existing CloudFormation stack...${NC}"
    
    UPDATE_OUTPUT=$(aws cloudformation update-stack \
        --stack-name ${STACK_NAME} \
        --template-body file://${TEMPLATE_FILE} \
        --region ${AWS_REGION} \
        --capabilities CAPABILITY_IAM \
        2>&1 || true)
    
    if echo "$UPDATE_OUTPUT" | grep -q "No updates are to be performed"; then
        echo -e "${YELLOW}No updates needed - stack is up to date${NC}"
    else
        echo -e "${YELLOW}Waiting for stack update to complete...${NC}"
        
        aws cloudformation wait stack-update-complete \
            --stack-name ${STACK_NAME} \
            --region ${AWS_REGION}
        
        echo -e "${GREEN}✓ Stack updated successfully${NC}"
    fi
fi

# Get stack outputs
echo -e "${BLUE}Retrieving stack outputs...${NC}"

OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${AWS_REGION} \
    --query 'Stacks[0].Outputs' \
    --output json)

# Extract values
S3_BUCKET=$(echo $OUTPUTS | grep -o '"OutputKey": "BucketName"[^}]*"OutputValue": "[^"]*"' | grep -o '"OutputValue": "[^"]*"' | cut -d'"' -f4)
CLOUDFRONT_DIST_ID=$(echo $OUTPUTS | grep -o '"OutputKey": "CloudFrontDistributionId"[^}]*"OutputValue": "[^"]*"' | grep -o '"OutputValue": "[^"]*"' | cut -d'"' -f4)
CLOUDFRONT_URL=$(echo $OUTPUTS | grep -o '"OutputKey": "CloudFrontURL"[^}]*"OutputValue": "[^"]*"' | grep -o '"OutputValue": "[^"]*"' | cut -d'"' -f4)
S3_WEBSITE_URL=$(echo $OUTPUTS | grep -o '"OutputKey": "BucketWebsiteURL"[^}]*"OutputValue": "[^"]*"' | grep -o '"OutputValue": "[^"]*"' | cut -d'"' -f4)

# Save configuration
echo -e "${BLUE}Saving configuration...${NC}"

cat > deploy.env <<EOF
# AI Accounting Copilot - Deployment Configuration
# Generated from CloudFormation stack: ${STACK_NAME}
# Generated on $(date)

S3_BUCKET=${S3_BUCKET}
CLOUDFRONT_DIST_ID=${CLOUDFRONT_DIST_ID}
AWS_REGION=${AWS_REGION}
EOF

echo -e "${GREEN}✓ Configuration saved to deploy.env${NC}"

# Summary
echo ""
echo -e "${GREEN}=============================================="
echo "CloudFormation Deployment Complete!"
echo "=============================================="
echo -e "${NC}"
echo -e "Stack Name: ${GREEN}${STACK_NAME}${NC}"
echo -e "S3 Bucket: ${GREEN}${S3_BUCKET}${NC}"
echo -e "S3 Website URL: ${BLUE}${S3_WEBSITE_URL}${NC}"
echo -e "CloudFront Distribution ID: ${GREEN}${CLOUDFRONT_DIST_ID}${NC}"
echo -e "CloudFront URL: ${BLUE}${CLOUDFRONT_URL}${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Configure .env file (copy from .env.example)"
echo "2. Run: source deploy.env && ./deploy.sh"
echo ""
echo -e "${YELLOW}To delete the stack:${NC}"
echo -e "   ${BLUE}aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${AWS_REGION}${NC}"
echo ""
