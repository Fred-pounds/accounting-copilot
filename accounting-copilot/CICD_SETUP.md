# CI/CD Setup Guide

This guide walks through setting up the complete CI/CD pipeline for the AI Accounting Copilot using GitHub Actions.

## Prerequisites

- GitHub repository with admin access
- AWS account with appropriate permissions
- Terraform Cloud account (optional, for remote state)

## Step 1: Create AWS IAM Users for CI/CD

Create separate IAM users for staging and production deployments:

### Staging IAM User

```bash
aws iam create-user --user-name github-actions-staging

# Attach policies (adjust as needed)
aws iam attach-user-policy \
  --user-name github-actions-staging \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Create access key
aws iam create-access-key --user-name github-actions-staging
```

Save the Access Key ID and Secret Access Key.

### Production IAM User

```bash
aws iam create-user --user-name github-actions-production

# Attach policies (adjust as needed)
aws iam attach-user-policy \
  --user-name github-actions-production \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Create access key
aws iam create-access-key --user-name github-actions-production
```

Save the Access Key ID and Secret Access Key.

## Step 2: Configure GitHub Secrets

### Navigate to Repository Settings

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### Add Staging Secrets

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `AWS_ACCESS_KEY_ID` | AWS access key for staging | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for staging | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `STAGING_API_URL` | API Gateway URL | `https://api-staging.example.com` |
| `STAGING_COGNITO_USER_POOL_ID` | Cognito User Pool ID | `us-east-1_aBcDeFgHi` |
| `STAGING_COGNITO_CLIENT_ID` | Cognito Client ID | `1234567890abcdefghijklmnop` |

### Add Production Secrets

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `AWS_ACCESS_KEY_ID_PROD` | AWS access key for production | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY_PROD` | AWS secret key for production | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `PROD_API_URL` | API Gateway URL | `https://api.example.com` |
| `PROD_COGNITO_USER_POOL_ID` | Cognito User Pool ID | `us-east-1_XyZaBcDeF` |
| `PROD_COGNITO_CLIENT_ID` | Cognito Client ID | `0987654321zyxwvutsrqponm` |

## Step 3: Configure GitHub Environments

### Create Staging Environment

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `staging`
4. Click **Configure environment**
5. No protection rules needed (auto-deploys)
6. Click **Save protection rules**

### Create Production Environment

1. Click **New environment**
2. Name: `production`
3. Click **Configure environment**
4. Enable **Required reviewers**
   - Add team members who can approve deployments
5. (Optional) Enable **Wait timer**: 5 minutes
6. Set **Deployment branches**: Only `main`
7. Click **Save protection rules**

## Step 4: Configure Terraform Backend (Optional)

For team collaboration, use remote state storage:

### Option A: Terraform Cloud

1. Create account at https://app.terraform.io
2. Create organization and workspace
3. Generate API token
4. Add to GitHub secrets as `TF_API_TOKEN`
5. Update `infrastructure/backend.tf`:

```hcl
terraform {
  backend "remote" {
    organization = "your-org"
    workspaces {
      name = "accounting-copilot"
    }
  }
}
```

### Option B: S3 Backend

1. Create S3 bucket for state:
```bash
aws s3 mb s3://accounting-copilot-terraform-state
aws s3api put-bucket-versioning \
  --bucket accounting-copilot-terraform-state \
  --versioning-configuration Status=Enabled
```

2. Create DynamoDB table for locking:
```bash
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

3. Update `infrastructure/backend.tf`:
```hcl
terraform {
  backend "s3" {
    bucket         = "accounting-copilot-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
```

## Step 5: Initial Infrastructure Deployment

Before enabling CI/CD, deploy infrastructure manually:

```bash
# Deploy staging
export ENVIRONMENT=staging
./scripts/deploy-infrastructure.sh

# Get outputs for GitHub secrets
cd infrastructure
terraform output api_gateway_url
terraform output cognito_user_pool_id
terraform output cognito_client_id
cd ..

# Update GitHub secrets with these values
```

Repeat for production environment.

## Step 6: Test the CI/CD Pipeline

### Test Workflow

1. Create a feature branch:
```bash
git checkout -b test-cicd
```

2. Make a small change (e.g., update README)

3. Push and create PR:
```bash
git add .
git commit -m "Test CI/CD pipeline"
git push origin test-cicd
```

4. Create Pull Request on GitHub
5. Verify that "Run Tests" workflow executes
6. Check that all tests pass

### Test Staging Deployment

1. Merge PR to `main` branch
2. Go to **Actions** tab
3. Verify "Deploy to Staging" workflow starts automatically
4. Monitor deployment progress
5. Check staging environment after deployment

### Test Production Deployment

1. Go to **Actions** tab
2. Select "Deploy to Production" workflow
3. Click **Run workflow**
4. Type "deploy" in confirmation field
5. Click **Run workflow**
6. Wait for approval (if configured)
7. Approve deployment
8. Monitor deployment progress
9. Verify production environment

## Step 7: Configure Notifications (Optional)

### Slack Notifications

1. Create Slack webhook URL
2. Add to GitHub secrets as `SLACK_WEBHOOK_URL`
3. Add notification step to workflows:

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Email Notifications

GitHub automatically sends email notifications for workflow failures to repository admins.

## Step 8: Set Up Monitoring

### CloudWatch Alarms

Alarms are created by Terraform. Subscribe to SNS topics:

```bash
# Get SNS topic ARNs
cd infrastructure
terraform output sns_topic_arns

# Subscribe to topics
aws sns subscribe \
  --topic-arn <TOPIC_ARN> \
  --protocol email \
  --notification-endpoint devops@example.com
```

### GitHub Actions Monitoring

- Enable workflow notifications in GitHub settings
- Monitor workflow runs in Actions tab
- Set up status badges in README

## Verification Checklist

- [ ] AWS IAM users created for staging and production
- [ ] GitHub secrets configured for both environments
- [ ] GitHub environments created with protection rules
- [ ] Terraform backend configured (if using remote state)
- [ ] Initial infrastructure deployed manually
- [ ] Test workflow runs successfully on PR
- [ ] Staging deployment works on merge to main
- [ ] Production deployment requires manual approval
- [ ] CloudWatch alarms configured and subscribed
- [ ] Team members can approve production deployments
- [ ] Rollback procedure documented and tested

## Troubleshooting

### Workflow Permission Errors

If workflows fail with permission errors:

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select "Read and write permissions"
3. Enable "Allow GitHub Actions to create and approve pull requests"
4. Click **Save**

### Terraform State Lock Issues

If Terraform state is locked:

```bash
# List locks
aws dynamodb scan --table-name terraform-state-lock

# Force unlock (use with caution)
cd infrastructure
terraform force-unlock <LOCK_ID>
```

### AWS Credentials Issues

Verify credentials work:

```bash
# Test staging credentials
export AWS_ACCESS_KEY_ID=<staging-key>
export AWS_SECRET_ACCESS_KEY=<staging-secret>
aws sts get-caller-identity

# Test production credentials
export AWS_ACCESS_KEY_ID=<production-key>
export AWS_SECRET_ACCESS_KEY=<production-secret>
aws sts get-caller-identity
```

## Security Best Practices

1. **Rotate AWS access keys** every 90 days
2. **Use least privilege** IAM policies
3. **Enable MFA** for production approvers
4. **Audit workflow runs** regularly
5. **Keep secrets secure** - never log or expose them
6. **Use branch protection** rules on main branch
7. **Require code review** before merging to main
8. **Enable vulnerability scanning** in GitHub
9. **Monitor AWS CloudTrail** for API activity
10. **Set up AWS Budgets** to prevent cost overruns

## Maintenance

### Regular Tasks

- **Weekly:** Review workflow runs and fix failures
- **Monthly:** Rotate AWS access keys
- **Quarterly:** Review and update IAM policies
- **Annually:** Audit all secrets and credentials

### Updating Workflows

1. Create feature branch
2. Update workflow files in `.github/workflows/`
3. Test changes in feature branch
4. Create PR and get review
5. Merge to main

## Support

For issues with CI/CD setup:
- Check `.github/workflows/README.md` for workflow documentation
- Review GitHub Actions logs for error details
- Consult AWS CloudWatch logs for deployment issues
- Contact DevOps team for assistance

## Next Steps

After CI/CD is set up:

1. Configure custom domain for API Gateway
2. Set up CloudFront distribution for frontend
3. Enable AWS WAF for security
4. Configure automated backups
5. Set up disaster recovery procedures
6. Document runbooks for common issues
7. Train team on deployment procedures
