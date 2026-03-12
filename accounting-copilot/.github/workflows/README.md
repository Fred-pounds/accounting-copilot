# GitHub Actions Workflows

This directory contains the CI/CD workflows for the AI Accounting Copilot project.

## Workflows

### 1. Run Tests (`test.yml`)

**Trigger:** Pull requests and pushes to `main` or `develop` branches

**Purpose:** Runs automated tests to ensure code quality

**Jobs:**
- `test-backend`: Runs Python linting, type checking, and unit/property tests
- `test-frontend`: Runs frontend linting, tests, and build verification
- `security-scan`: Scans for security vulnerabilities using Trivy

### 2. Deploy to Staging (`deploy-staging.yml`)

**Trigger:** Automatic on push to `main` branch, or manual via workflow dispatch

**Purpose:** Deploys the application to the staging environment

**Jobs:**
1. `deploy-infrastructure`: Deploys AWS infrastructure using Terraform
2. `build-lambdas`: Builds Lambda function packages
3. `deploy-lambdas`: Deploys Lambda functions to AWS
4. `deploy-frontend`: Builds and deploys frontend to S3/CloudFront
5. `notify`: Sends deployment status summary

**Environment:** `staging`

### 3. Deploy to Production (`deploy-production.yml`)

**Trigger:** Manual only via workflow dispatch (requires typing "deploy" to confirm)

**Purpose:** Deploys the application to the production environment

**Jobs:**
1. `validate-input`: Validates deployment confirmation
2. `deploy-infrastructure`: Deploys AWS infrastructure using Terraform
3. `build-lambdas`: Builds Lambda function packages
4. `deploy-lambdas`: Deploys Lambda functions to AWS
5. `deploy-frontend`: Builds and deploys frontend to S3/CloudFront
6. `notify`: Sends deployment status summary

**Environment:** `production` (requires manual approval if configured)

## Setup Requirements

### GitHub Secrets

Configure these secrets in your GitHub repository:

#### Staging Secrets
- `AWS_ACCESS_KEY_ID`: AWS access key for staging environment
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for staging environment

#### Production Secrets
- `AWS_ACCESS_KEY_ID_PROD`: AWS access key for production environment
- `AWS_SECRET_ACCESS_KEY_PROD`: AWS secret key for production environment

### GitHub Environments

Create two environments in your repository settings:

#### Staging Environment
- Name: `staging`
- Protection rules: None (auto-deploys)

#### Production Environment
- Name: `production`
- Protection rules:
  - Required reviewers: Add team members who can approve deployments
  - Wait timer: 5 minutes (optional)
  - Deployment branches: Only `main`

## Deployment Flow

### Staging Deployment (Automatic)
```
Push to main → Run Tests → Deploy Infrastructure → Build Lambdas → Deploy Lambdas & Frontend → Notify
```

### Production Deployment (Manual)
```
Manual Trigger → Confirm "deploy" → Approval (if configured) → Deploy Infrastructure → Build Lambdas → Deploy Lambdas & Frontend → Notify
```

## How to Use

### Running Tests
Tests run automatically on every pull request and push. No manual action needed.

### Deploying to Staging
1. Merge your PR to the `main` branch
2. Deployment starts automatically
3. Monitor progress in the Actions tab

### Deploying to Production
1. Go to Actions tab in GitHub
2. Select "Deploy to Production" workflow
3. Click "Run workflow"
4. Type "deploy" in the confirmation field
5. Click "Run workflow"
6. Wait for approval (if configured)
7. Monitor deployment progress

## Monitoring

- View workflow runs in the **Actions** tab
- Check deployment summaries in the workflow run details
- Monitor AWS resources in CloudWatch
- Review logs for any errors or warnings

## Troubleshooting

### Workflow Fails with Permission Error
- Verify GitHub secrets are correctly configured
- Check AWS IAM user permissions
- Ensure GitHub Actions has read/write permissions in repository settings

### Terraform State Lock
- If Terraform state is locked, wait for the lock to expire
- Or manually unlock using `terraform force-unlock` (use with caution)

### Lambda Deployment Fails
- Check that Lambda packages were built successfully
- Verify AWS Lambda function names match Terraform outputs
- Review CloudWatch logs for Lambda errors

### Frontend Deployment Fails
- Ensure S3 bucket exists and is accessible
- Verify CloudFront distribution is configured
- Check that environment variables are correctly set

## Security Best Practices

1. Rotate AWS access keys every 90 days
2. Use least privilege IAM policies
3. Enable branch protection on `main` branch
4. Require code review before merging
5. Monitor workflow runs for suspicious activity
6. Keep secrets secure and never log them
7. Enable vulnerability scanning
8. Review and audit deployments regularly

## Maintenance

- Review workflow runs weekly
- Update GitHub Actions versions quarterly
- Test workflows after any changes
- Document any custom modifications
- Keep this README up to date
