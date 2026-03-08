# Deployment Scripts

This directory contains deployment automation scripts for the AI Accounting Copilot.

## Scripts Overview

### 1. `validate-deployment-setup.sh`

Validates that all prerequisites are met for deployment.

**Usage:**
```bash
./scripts/validate-deployment-setup.sh
# or
make validate-setup
```

**Checks:**
- Required tools (Terraform, AWS CLI, Python, Node.js, npm)
- AWS credentials configuration
- Deployment scripts existence and permissions
- Infrastructure files
- Python dependencies
- Frontend setup
- GitHub Actions workflows

**Exit Codes:**
- `0`: All checks passed or only warnings
- `1`: One or more errors found

### 2. `build-lambda-packages.sh`

Builds deployment packages for all Lambda functions.

**Usage:**
```bash
./scripts/build-lambda-packages.sh
# or
make build-lambdas
```

**What it does:**
1. Creates `lambda-packages/` directory
2. For each Lambda function:
   - Copies shared code
   - Copies function-specific code
   - Installs dependencies
   - Creates zip file
3. Reports package sizes

**Output:**
- `lambda-packages/*.zip` - Deployment packages

**Functions packaged:**
- document_upload_handler
- ocr_processor
- transaction_classifier
- data_validator
- reconciliation_engine
- dashboard_api
- financial_assistant
- audit_logger

### 3. `deploy-infrastructure.sh`

Deploys AWS infrastructure using Terraform.

**Usage:**
```bash
./scripts/deploy-infrastructure.sh
# or
make deploy-infra
```

**Environment Variables:**
- `ENVIRONMENT`: Deployment environment (default: dev)
- `AWS_REGION`: AWS region (default: us-east-1)

**What it does:**
1. Validates prerequisites (Terraform, AWS CLI)
2. Verifies AWS credentials
3. Initializes Terraform
4. Validates Terraform configuration
5. Creates deployment plan
6. Asks for confirmation
7. Applies infrastructure changes
8. Saves outputs to `terraform-outputs.json`

**Output:**
- `terraform-outputs.json` - Terraform outputs for CI/CD

### 4. `deploy-lambdas.sh`

Deploys Lambda function packages to AWS.

**Usage:**
```bash
./scripts/deploy-lambdas.sh
# or
make deploy-lambdas
```

**Environment Variables:**
- `ENVIRONMENT`: Deployment environment (default: dev)
- `AWS_REGION`: AWS region (default: us-east-1)

**Prerequisites:**
- Lambda packages must be built first
- Lambda functions must exist in AWS (created by Terraform)

**What it does:**
1. Validates AWS CLI is installed
2. Checks lambda-packages directory exists
3. For each function:
   - Uploads zip file to AWS Lambda
   - Reports success or failure
4. Provides deployment summary

**Function naming convention:**
`accounting-copilot-{environment}-{function-name}`

### 5. `deploy-all.sh`

Master deployment script that orchestrates complete deployment.

**Usage:**
```bash
./scripts/deploy-all.sh
# or
make deploy-all
```

**Environment Variables:**
- `ENVIRONMENT`: Deployment environment (default: dev)
- `AWS_REGION`: AWS region (default: us-east-1)

**What it does:**
1. Deploys infrastructure (Terraform)
2. Builds Lambda packages
3. Deploys Lambda functions
4. Deploys frontend (React app)

**Steps:**
```
Step 1/4: Deploying infrastructure...
Step 2/4: Building Lambda packages...
Step 3/4: Deploying Lambda functions...
Step 4/4: Deploying frontend...
```

**Post-deployment:**
- Displays next steps
- References DEPLOYMENT.md for details

## Frontend Deployment

The frontend deployment script is located at `frontend/deploy.sh`.

**Usage:**
```bash
cd frontend
./deploy.sh
# or from root:
make deploy-frontend
```

**Environment Variables:**
- `ENVIRONMENT`: Deployment environment (default: dev)
- `S3_BUCKET`: S3 bucket name
- `CLOUDFRONT_DIST_ID`: CloudFront distribution ID (optional)
- `AWS_REGION`: AWS region (default: us-east-1)

**What it does:**
1. Validates prerequisites
2. Installs npm dependencies
3. Runs type checking and linting
4. Builds React application
5. Uploads to S3 with proper cache headers
6. Invalidates CloudFront cache (if configured)

## Common Workflows

### First-Time Deployment

```bash
# 1. Validate setup
make validate-setup

# 2. Deploy everything
make deploy-all

# 3. Configure post-deployment
# - Enable Bedrock model access
# - Subscribe to SNS topics
# - Create test user in Cognito
```

### Update Lambda Functions

```bash
# Build and deploy
make build-lambdas
make deploy-lambdas
```

### Update Frontend

```bash
make deploy-frontend
```

### Update Infrastructure

```bash
make deploy-infra
```

### Complete Update

```bash
make deploy-all
```

## Environment Configuration

### Development

```bash
export ENVIRONMENT=dev
export AWS_REGION=us-east-1
```

### Staging

```bash
export ENVIRONMENT=staging
export AWS_REGION=us-east-1
```

### Production

```bash
export ENVIRONMENT=production
export AWS_REGION=us-east-1
```

## Troubleshooting

### Script Permission Denied

```bash
chmod +x scripts/*.sh
chmod +x frontend/deploy.sh
```

### AWS Credentials Not Found

```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1
```

### Terraform State Lock

```bash
cd infrastructure
terraform force-unlock <lock-id>
```

### Lambda Package Too Large

Lambda packages must be < 50 MB compressed. If too large:
1. Remove unnecessary dependencies
2. Use Lambda layers for common dependencies
3. Optimize package size

### S3 Bucket Not Found

Ensure infrastructure is deployed first:
```bash
make deploy-infra
```

## Best Practices

1. **Always validate** before deploying:
   ```bash
   make validate-setup
   ```

2. **Test in dev** before staging/production:
   ```bash
   export ENVIRONMENT=dev
   make deploy-all
   ```

3. **Review Terraform plan** before applying:
   ```bash
   cd infrastructure
   terraform plan
   ```

4. **Use version control** for infrastructure changes:
   ```bash
   git add infrastructure/
   git commit -m "Update infrastructure"
   ```

5. **Monitor deployments** in CloudWatch:
   ```bash
   aws logs tail /aws/lambda/accounting-copilot-dev-document_upload_handler --follow
   ```

6. **Keep secrets secure** - never commit credentials

7. **Document changes** in commit messages

8. **Test rollback procedures** before production deployment

## CI/CD Integration

These scripts are used by GitHub Actions workflows:

- **test.yml**: Runs tests on every push
- **deploy-staging.yml**: Deploys to staging on merge to main
- **deploy-production.yml**: Manual production deployment
- **code-quality.yml**: Code quality checks on PRs

See `.github/workflows/README.md` for CI/CD documentation.

## Support

For issues with deployment scripts:
- Check script output for error messages
- Review AWS CloudWatch logs
- Consult DEPLOYMENT.md for detailed instructions
- See DEPLOYMENT_QUICK_REFERENCE.md for common commands
- Check CICD_SETUP.md for CI/CD configuration

## Related Documentation

- `DEPLOYMENT.md` - Comprehensive deployment guide
- `DEPLOYMENT_QUICK_REFERENCE.md` - Quick command reference
- `CICD_SETUP.md` - CI/CD pipeline setup
- `.github/workflows/README.md` - GitHub Actions workflows
- `TASK_25_IMPLEMENTATION_SUMMARY.md` - Implementation details
