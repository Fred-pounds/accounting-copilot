# Deployment Quick Reference

Quick commands for deploying the AI Accounting Copilot.

## Prerequisites

```bash
# Verify tools are installed
terraform --version
aws --version
python --version
node --version

# Verify AWS credentials
aws sts get-caller-identity
```

## Local Deployment

### Complete Deployment (All Components)

```bash
# Deploy everything
make deploy-all

# Or manually:
./scripts/deploy-all.sh
```

### Individual Components

```bash
# 1. Deploy infrastructure
make deploy-infra
# or: ./scripts/deploy-infrastructure.sh

# 2. Build Lambda packages
make build-lambdas
# or: ./scripts/build-lambda-packages.sh

# 3. Deploy Lambda functions
make deploy-lambdas
# or: ./scripts/deploy-lambdas.sh

# 4. Deploy frontend
make deploy-frontend
# or: cd frontend && ./deploy.sh
```

## CI/CD Deployment

### Staging (Automatic)

```bash
# Merge to main branch
git checkout main
git merge feature-branch
git push origin main

# Deployment happens automatically via GitHub Actions
```

### Production (Manual)

1. Go to GitHub repository
2. Click **Actions** tab
3. Select **Deploy to Production** workflow
4. Click **Run workflow**
5. Type "deploy" in confirmation field
6. Click **Run workflow**
7. Wait for approval (if configured)
8. Approve deployment

## Environment Variables

### Staging

```bash
export ENVIRONMENT=staging
export AWS_REGION=us-east-1
export S3_BUCKET=accounting-copilot-web-staging
```

### Production

```bash
export ENVIRONMENT=production
export AWS_REGION=us-east-1
export S3_BUCKET=accounting-copilot-web-production
```

## Common Tasks

### Update Lambda Function

```bash
# Build and deploy specific function
./scripts/build-lambda-packages.sh
aws lambda update-function-code \
  --function-name accounting-copilot-dev-document_upload_handler \
  --zip-file fileb://lambda-packages/document_upload_handler.zip
```

### Update Frontend Only

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://accounting-copilot-web-dev/ --delete
```

### Update Infrastructure Only

```bash
cd infrastructure
terraform plan
terraform apply
```

### View Deployment Status

```bash
# Check Lambda functions
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `accounting-copilot`)].FunctionName'

# Check S3 buckets
aws s3 ls | grep accounting-copilot

# Check API Gateway
aws apigateway get-rest-apis \
  --query 'items[?name==`accounting-copilot-api`]'
```

## Rollback

### Rollback Lambda Function

```bash
# List versions
aws lambda list-versions-by-function \
  --function-name accounting-copilot-dev-document_upload_handler

# Rollback to previous version
aws lambda update-alias \
  --function-name accounting-copilot-dev-document_upload_handler \
  --name live \
  --function-version <previous-version>
```

### Rollback Frontend

```bash
# Restore from S3 versioning
aws s3api list-object-versions \
  --bucket accounting-copilot-web-dev \
  --prefix index.html

aws s3api copy-object \
  --bucket accounting-copilot-web-dev \
  --copy-source accounting-copilot-web-dev/index.html?versionId=<version-id> \
  --key index.html
```

### Rollback Infrastructure

```bash
cd infrastructure
git checkout <previous-commit>
terraform apply
```

## Monitoring

### View Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/accounting-copilot-dev-document_upload_handler --follow

# API Gateway logs
aws logs tail /aws/apigateway/accounting-copilot-api --follow
```

### Check Alarms

```bash
# List alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix accounting-copilot

# Check alarm state
aws cloudwatch describe-alarms \
  --state-value ALARM
```

## Troubleshooting

### Deployment Fails

```bash
# Check Terraform state
cd infrastructure
terraform show

# Check Lambda function status
aws lambda get-function \
  --function-name accounting-copilot-dev-document_upload_handler

# Check S3 bucket
aws s3 ls s3://accounting-copilot-web-dev/
```

### Permission Errors

```bash
# Verify IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name <username>
```

### State Lock Issues

```bash
# Force unlock Terraform state (use with caution)
cd infrastructure
terraform force-unlock <lock-id>
```

## Cleanup

### Delete Everything

```bash
# Destroy infrastructure
make destroy-infra

# Or manually:
cd infrastructure
terraform destroy

# Clean local artifacts
make clean
rm -rf lambda-packages/
```

### Delete Specific Resources

```bash
# Delete Lambda function
aws lambda delete-function \
  --function-name accounting-copilot-dev-document_upload_handler

# Empty and delete S3 bucket
aws s3 rm s3://accounting-copilot-web-dev/ --recursive
aws s3 rb s3://accounting-copilot-web-dev/
```

## Cost Monitoring

```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost

# Set up budget alert
aws budgets create-budget \
  --account-id <account-id> \
  --budget file://budget.json
```

## Support

- **Documentation:** See DEPLOYMENT.md for detailed guide
- **CI/CD Setup:** See CICD_SETUP.md for pipeline configuration
- **Workflows:** See .github/workflows/README.md for workflow details
- **Issues:** Check CloudWatch Logs and GitHub Actions logs
