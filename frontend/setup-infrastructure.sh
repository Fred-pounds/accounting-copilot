#!/bin/bash

# AI Accounting Copilot - Infrastructure Setup Script
# Creates S3 bucket and CloudFront distribution for frontend hosting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}AI Accounting Copilot - Infrastructure Setup${NC}"
echo "=============================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if jq is installed (for JSON parsing)
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq is not installed. Some features may not work.${NC}"
    echo "Install jq for better experience: https://stedolan.github.io/jq/"
fi

# Get AWS account ID
echo -e "${BLUE}Getting AWS account information...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: Unable to get AWS account ID${NC}"
    echo "Please configure AWS CLI credentials"
    exit 1
fi
echo -e "AWS Account ID: ${GREEN}${AWS_ACCOUNT_ID}${NC}"

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="accounting-copilot-web-${AWS_ACCOUNT_ID}"

echo -e "Region: ${GREEN}${AWS_REGION}${NC}"
echo -e "S3 Bucket: ${GREEN}${S3_BUCKET}${NC}"
echo ""

# Confirm before proceeding
read -p "Do you want to proceed with infrastructure setup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 0
fi

# Step 1: Create S3 Bucket
echo -e "${BLUE}Step 1: Creating S3 bucket...${NC}"

# Check if bucket already exists
if aws s3 ls "s3://${S3_BUCKET}" 2>&1 | grep -q 'NoSuchBucket'; then
    # Create bucket
    if [ "$AWS_REGION" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket ${S3_BUCKET} \
            --region ${AWS_REGION}
    else
        aws s3api create-bucket \
            --bucket ${S3_BUCKET} \
            --region ${AWS_REGION} \
            --create-bucket-configuration LocationConstraint=${AWS_REGION}
    fi
    echo -e "${GREEN}✓ S3 bucket created${NC}"
else
    echo -e "${YELLOW}S3 bucket already exists${NC}"
fi

# Step 2: Configure bucket for static website hosting
echo -e "${BLUE}Step 2: Configuring static website hosting...${NC}"
aws s3 website s3://${S3_BUCKET}/ \
    --index-document index.html \
    --error-document index.html
echo -e "${GREEN}✓ Static website hosting configured${NC}"

# Step 3: Disable block public access
echo -e "${BLUE}Step 3: Configuring public access...${NC}"
aws s3api put-public-access-block \
    --bucket ${S3_BUCKET} \
    --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
echo -e "${GREEN}✓ Public access configured${NC}"

# Step 4: Add bucket policy
echo -e "${BLUE}Step 4: Adding bucket policy...${NC}"
cat > /tmp/bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${S3_BUCKET}/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
    --bucket ${S3_BUCKET} \
    --policy file:///tmp/bucket-policy.json
rm /tmp/bucket-policy.json
echo -e "${GREEN}✓ Bucket policy added${NC}"

# Step 5: Enable bucket encryption
echo -e "${BLUE}Step 5: Enabling bucket encryption...${NC}"
aws s3api put-bucket-encryption \
    --bucket ${S3_BUCKET} \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
echo -e "${GREEN}✓ Bucket encryption enabled${NC}"

# Step 6: Create CloudFront distribution
echo -e "${BLUE}Step 6: Creating CloudFront distribution...${NC}"
echo -e "${YELLOW}This may take several minutes...${NC}"

# Get S3 website endpoint
S3_WEBSITE_ENDPOINT="${S3_BUCKET}.s3-website-${AWS_REGION}.amazonaws.com"

# Create distribution configuration
cat > /tmp/cloudfront-config.json <<EOF
{
  "CallerReference": "accounting-copilot-$(date +%s)",
  "Comment": "AI Accounting Copilot Frontend Distribution",
  "Enabled": true,
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-${S3_BUCKET}",
        "DomainName": "${S3_WEBSITE_ENDPOINT}",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only"
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-${S3_BUCKET}",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 3,
      "Items": ["GET", "HEAD", "OPTIONS"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 3600,
    "MaxTTL": 31536000,
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    }
  },
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      },
      {
        "ErrorCode": 403,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  },
  "PriceClass": "PriceClass_100"
}
EOF

# Create the distribution
DISTRIBUTION_OUTPUT=$(aws cloudfront create-distribution \
    --distribution-config file:///tmp/cloudfront-config.json \
    --output json)

rm /tmp/cloudfront-config.json

# Extract distribution ID and domain name
if command -v jq &> /dev/null; then
    CLOUDFRONT_DIST_ID=$(echo $DISTRIBUTION_OUTPUT | jq -r '.Distribution.Id')
    CLOUDFRONT_DOMAIN=$(echo $DISTRIBUTION_OUTPUT | jq -r '.Distribution.DomainName')
else
    # Fallback if jq is not available
    CLOUDFRONT_DIST_ID=$(echo $DISTRIBUTION_OUTPUT | grep -o '"Id": "[^"]*"' | head -1 | cut -d'"' -f4)
    CLOUDFRONT_DOMAIN=$(echo $DISTRIBUTION_OUTPUT | grep -o '"DomainName": "[^"]*"' | head -1 | cut -d'"' -f4)
fi

echo -e "${GREEN}✓ CloudFront distribution created${NC}"

# Step 7: Save configuration
echo -e "${BLUE}Step 7: Saving configuration...${NC}"

cat > deploy.env <<EOF
# AI Accounting Copilot - Deployment Configuration
# Generated on $(date)

S3_BUCKET=${S3_BUCKET}
CLOUDFRONT_DIST_ID=${CLOUDFRONT_DIST_ID}
AWS_REGION=${AWS_REGION}
EOF

echo -e "${GREEN}✓ Configuration saved to deploy.env${NC}"

# Summary
echo ""
echo -e "${GREEN}=============================================="
echo "Infrastructure Setup Complete!"
echo "=============================================="
echo -e "${NC}"
echo -e "S3 Bucket: ${GREEN}${S3_BUCKET}${NC}"
echo -e "S3 Website URL: ${BLUE}http://${S3_WEBSITE_ENDPOINT}${NC}"
echo -e "CloudFront Distribution ID: ${GREEN}${CLOUDFRONT_DIST_ID}${NC}"
echo -e "CloudFront URL: ${BLUE}https://${CLOUDFRONT_DOMAIN}${NC}"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo "1. CloudFront distribution is being deployed (takes 15-20 minutes)"
echo "2. Configuration saved to deploy.env"
echo "3. Source deploy.env before running deploy.sh:"
echo -e "   ${BLUE}source deploy.env${NC}"
echo "4. Create .env file with your API and Cognito configuration"
echo "5. Run ./deploy.sh to deploy the frontend"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Wait for CloudFront distribution to deploy"
echo "2. Configure .env file (copy from .env.example)"
echo "3. Run: source deploy.env && ./deploy.sh"
echo ""
