# CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing and deployment of the AI Accounting Copilot.

## Workflows

### 1. Test Workflow (`test.yml`)

**Trigger:** Push or Pull Request to `main` or `develop` branches

**Purpose:** Run automated tests for both backend and frontend

**Jobs:**
- `test-backend`: Runs Python unit tests, property-based tests, and integration tests
- `test-frontend`: Runs frontend linting, type checking, tests, and build

**Status:** Runs on every push and PR to ensure code quality

### 2. Deploy to Staging (`deploy-staging.yml`)

**Trigger:** Push to `main` branch or manual workflow dispatch

**Purpose:** Automatically deploy to staging environment when code is merged to main

**Jobs:**
1. `deploy-infrastructure`: Deploy/update AWS infrastructure using Terraform
2. `deploy-backend`: Build and deploy Lambda functions
3. `deploy-frontend`: Build and deploy React frontend to S3/CloudFront
4. `notify`: Send deployment status notification

**Environment:** `staging`

### 3. Deploy to Production (`deploy-production.yml`)

**Trigger:** Manual workflow dispatch with confirmation

**Purpose:** Deploy to production environment with manual approval

**Jobs:**
1. `validate-input`: Verify deployment confirmation
2. `deploy-infrastructure`: Deploy/update AWS infrastructure using Terraform
3. `deploy-backend`: Build and deploy Lambda functions
4. `deploy-frontend`: Build and deploy React frontend to S3/CloudFront
5. `smoke-tests`: Run basic smoke tests against production
6. `notify`: Send deployment status notification

**Environment:** `production`

**Manual Approval:** Requires typing "deploy" to confirm

## Setup Instructions

### 1. Configure GitHub Secrets

Navigate to your repository → Settings → Secrets and variables → Actions

#### Required Secrets for Staging:

```
AWS_ACCESS_KEY_ID              # AWS access key for staging
AWS_SECRET_ACCESS_KEY          # AWS secret key for staging
STAGING_API_URL                # API Gateway URL for staging
STAGING_COGNITO_USER_POOL_ID   # Cognito User Pool ID for staging
STAGING_COGNITO_CLIENT_ID      # Cognito Client ID for staging
```

#### Required Secrets for Production:

```
AWS_ACCESS_KEY_ID_PROD         # AWS access key for production
AWS_SECRET_ACCESS_KEY_PROD     # AWS secret key for production
PROD_API_URL                   # API Gateway URL for production
PROD_COGNITO_USER_POOL_ID      # Cognito User Pool ID for production
PROD_COGNITO_CLIENT_ID         # Cognito Client ID for production
```

### 2. Configure GitHub Environments

Create two environments in your repository settings:

#### Staging Environment
- Name: `staging`
- No protection rules needed (auto-deploys on merge to main)

#### Production Environment
- Name: `production`
- Protection rules:
  - Required reviewers: Add team members who can approve production deployments
  - Wait timer: Optional (e.g., 5 minutes)
  - Deployment branches: Only `main` branch

### 3. AWS IAM Permissions

The AWS credentials need the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "dynamodb:*",
        "lambda:*",
        "apigateway:*",
        "cognito-idp:*",
        "states:*",
        "sns:*",
        "cloudwatch:*",
        "logs:*",
        "iam:*",
        "cloudfront:*",
        "textract:*",
        "bedrock:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Note:** In production, use more restrictive policies following the principle of least privilege.

## Usage

### Running Tests

Tests run automatically on every push and pull request. To manually trigger:

1. Go to Actions tab
2. Select "Run Tests" workflow
3. Click "Run workflow"

### Deploying to Staging

**Automatic:** Merge a pull request to `main` branch

**Manual:**
1. Go to Actions tab
2. Select "Deploy to Staging" workflow
3. Click "Run workflow"
4. Select branch (usually `main`)
5. Click "Run workflow"

### Deploying to Production

**Manual only:**
1. Go to Actions tab
2. Select "Deploy to Production" workflow
3. Click "Run workflow"
4. Type "deploy" in the confirmation field
5. Click "Run workflow"
6. Wait for approval from designated reviewers (if configured)
7. Approve the deployment in the environment protection rules

## Workflow Diagram

```
┌─────────────────┐
│  Push to main   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Run Tests     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Deploy Staging  │
│  (Automatic)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Manual Approval │
│  for Production │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Deploy Production│
│   (Manual)      │
└─────────────────┘
```

## Troubleshooting

### Workflow Fails at Terraform Step

**Issue:** Terraform state conflicts or missing backend configuration

**Solution:**
1. Ensure Terraform backend is configured in `infrastructure/backend.tf`
2. Check AWS credentials have sufficient permissions
3. Verify Terraform state is not locked

### Lambda Deployment Fails

**Issue:** Lambda function not found or package too large

**Solution:**
1. Ensure infrastructure is deployed first (creates Lambda functions)
2. Check Lambda package size (must be < 50 MB compressed)
3. Verify function names match the naming convention: `accounting-copilot-{environment}-{function-name}`

### Frontend Deployment Fails

**Issue:** S3 bucket not found or CloudFront invalidation fails

**Solution:**
1. Ensure infrastructure is deployed first (creates S3 bucket)
2. Check S3 bucket name matches the environment
3. Verify CloudFront distribution ID is correct (optional)

### Secrets Not Available

**Issue:** Workflow can't access secrets

**Solution:**
1. Verify secrets are created in repository settings
2. Check secret names match exactly (case-sensitive)
3. Ensure workflow has permission to access secrets

## Best Practices

1. **Always test locally** before pushing to main
2. **Use pull requests** for code review before merging to main
3. **Monitor staging** deployments before deploying to production
4. **Keep secrets secure** - never commit them to the repository
5. **Review logs** after each deployment to ensure success
6. **Use semantic versioning** for releases
7. **Tag production deployments** for easy rollback
8. **Document changes** in commit messages and PR descriptions

## Rollback Procedure

If a production deployment fails or causes issues:

1. **Immediate:** Revert the CloudFront cache
   ```bash
   aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
   ```

2. **Backend:** Redeploy previous Lambda version
   ```bash
   aws lambda update-function-code \
     --function-name <function-name> \
     --s3-bucket <backup-bucket> \
     --s3-key <previous-version>.zip
   ```

3. **Infrastructure:** Revert Terraform changes
   ```bash
   cd infrastructure
   git checkout <previous-commit>
   terraform apply
   ```

4. **Full Rollback:** Trigger production deployment workflow with previous commit

## Monitoring

After deployment, monitor:

- CloudWatch Logs for Lambda errors
- CloudWatch Metrics for API Gateway latency
- CloudWatch Alarms for threshold breaches
- Application logs for user-facing errors

## Support

For issues with CI/CD workflows:
1. Check workflow logs in GitHub Actions
2. Review AWS CloudWatch logs
3. Consult DEPLOYMENT.md for manual deployment steps
4. Contact DevOps team for assistance
