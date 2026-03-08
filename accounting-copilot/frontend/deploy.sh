#!/bin/bash

# AI Accounting Copilot Frontend Deployment Script
# This script builds and deploys the frontend to S3 + CloudFront

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${ENVIRONMENT:-dev}"
S3_BUCKET="${S3_BUCKET:-accounting-copilot-web-${ENVIRONMENT}}"
CLOUDFRONT_DIST_ID="${CLOUDFRONT_DIST_ID}"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo -e "${GREEN}AI Accounting Copilot - Frontend Deployment${NC}"
echo "=============================================="
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${AWS_REGION}"
echo "S3 Bucket: ${S3_BUCKET}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Using .env.example as template"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env from .env.example - please update with your values"
    fi
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

# Check if CloudFront distribution ID is set
if [ -z "$CLOUDFRONT_DIST_ID" ]; then
    echo -e "${YELLOW}Warning: CLOUDFRONT_DIST_ID not set${NC}"
    echo "CloudFront cache will not be invalidated"
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
npm ci

# Run type checking
echo -e "${GREEN}Running type check...${NC}"
npm run type-check || true

# Run linting
echo -e "${GREEN}Running linter...${NC}"
npm run lint || true

# Build the application
echo -e "${GREEN}Building application...${NC}"
npm run build

# Check if build was successful
if [ ! -d "dist" ]; then
    echo -e "${RED}Error: Build failed - dist directory not found${NC}"
    exit 1
fi

# Check if S3 bucket exists
if ! aws s3 ls "s3://${S3_BUCKET}" --region ${AWS_REGION} > /dev/null 2>&1; then
    echo -e "${RED}Error: S3 bucket ${S3_BUCKET} does not exist${NC}"
    echo "Please create the bucket or check your AWS credentials"
    exit 1
fi

# Upload to S3
echo -e "${GREEN}Uploading to S3 bucket: ${S3_BUCKET}${NC}"
aws s3 sync dist/ s3://${S3_BUCKET}/ \
    --delete \
    --region ${AWS_REGION} \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --exclude "*.map"

# Upload index.html with no-cache
echo -e "${GREEN}Uploading index.html with no-cache...${NC}"
aws s3 cp dist/index.html s3://${S3_BUCKET}/index.html \
    --region ${AWS_REGION} \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

# Invalidate CloudFront cache
if [ ! -z "$CLOUDFRONT_DIST_ID" ]; then
    echo -e "${GREEN}Invalidating CloudFront cache...${NC}"
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id ${CLOUDFRONT_DIST_ID} \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)
    echo -e "${GREEN}CloudFront invalidation created: ${INVALIDATION_ID}${NC}"
fi

echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "=============================================="
echo -e "S3 Website URL: https://${S3_BUCKET}.s3-website-${AWS_REGION}.amazonaws.com"

if [ ! -z "$CLOUDFRONT_DIST_ID" ]; then
    echo -e "CloudFront Distribution: ${CLOUDFRONT_DIST_ID}"
    echo -e "Note: CloudFront invalidation may take a few minutes to complete"
fi
