# GitHub Actions Setup Guide

Follow these steps to configure auto-deployment for the AI Accounting Copilot.

## Step 1: Configure GitHub Secrets

### Navigate to Repository Settings
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### Add Staging Secrets

Click "New repository secret" for each:

| Secret Name | Value | How to Get |
|------------|-------|------------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | From AWS IAM user for staging |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | From AWS IAM user for staging |

### Add Production Secrets

Click "New repository secret" for each:

| Secret Name | Value | How to Get |
|------------|-------|------------|
| `AWS_ACCESS_KEY_ID_PROD` | Your AWS access key | From AWS IAM user for production |
| `AWS_SECRET_ACCESS_KEY_PROD` | Your AWS secret key | From AWS IAM user for production |

## Step 2: Create AWS IAM Users (if not already created)

### For Staging

```bash
# Create IAM user
aws iam create-user --user-name github-actions-staging

# Attach required policies
aws iam attach-user-policy \
  --user-name github-actions-staging \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Create access key
aws iam create-access-key --user-name github-actions-staging
```

Save the `AccessKeyId` and `SecretAccessKey` from the output.

### For Production

```bash
# Create IAM user
aws iam create-user --user-name github-actions-production

# Attach required policies
aws iam attach-user-policy \
  --user-name github-actions-production \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Create access key
aws iam create-access-key --user-name github-actions-production
```

Save the `AccessKeyId` and `SecretAccessKey` from the output.

## Step 3: Configure GitHub Environments

### Create Staging Environment

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `staging`
4. Click **Configure environment**
5. No protection rules needed (auto-deploys on merge to main)
6. Click **Save protection rules**

### Create Production Environment

1. Click **New environment**
2. Name: `production`
3. Click **Configure environment**
4. **Enable "Required reviewers"**
   - Add yourself and/or team members who can approve deployments
   - At least 1 reviewer required
5. (Optional) Enable **Wait timer**: 5 minutes
6. Set **Deployment branches**: Select "Selected branches" → Add `main`
7. Click **Save protection rules**

## Step 4: Enable GitHub Actions Permissions

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions":
   - Select **"Read and write permissions"**
   - Check **"Allow GitHub Actions to create and approve pull requests"**
3. Click **Save**

## Step 5: Test the Setup

### Test 1: Run Tests Workflow

1. Create a new branch:
   ```bash
   git checkout -b test-cicd
   ```

2. Make a small change (e.g., update README)

3. Push and create PR:
   ```bash
   git add .
   git commit -m "Test CI/CD setup"
   git push origin test-cicd
   ```

4. Go to GitHub and create a Pull Request
5. Verify "Run Tests" workflow executes automatically
6. Check that all tests pass

### Test 2: Deploy to Staging

1. Merge the PR to `main`
2. Go to **Actions** tab
3. Verify "Deploy to Staging" workflow starts automatically
4. Monitor the deployment progress
5. Check the deployment summary when complete

### Test 3: Deploy to Production

1. Go to **Actions** tab
2. Click on "Deploy to Production" workflow
3. Click **Run workflow** button
4. Type `deploy` in the confirmation field
5. Click **Run workflow**
6. If you configured reviewers, approve the deployment when prompted
7. Monitor the deployment progress
8. Verify production environment after deployment

## Step 6: Configure Terraform Backend (Optional but Recommended)

For team collaboration, use remote state storage:

### Option A: S3 Backend (Recommended)

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

4. Initialize the backend:
```bash
cd infrastructure
terraform init -migrate-state
```

## Verification Checklist

- [ ] AWS IAM users created for staging and production
- [ ] GitHub secrets configured (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc.)
- [ ] GitHub environments created (`staging` and `production`)
- [ ] Production environment has required reviewers configured
- [ ] GitHub Actions permissions set to "Read and write"
- [ ] Test workflow runs successfully on PR
- [ ] Staging deployment works automatically on merge to main
- [ ] Production deployment requires manual trigger and confirmation
- [ ] Terraform backend configured (optional)

## What Happens After Setup

### On Every Pull Request
- Tests run automatically
- Linting and security scans execute
- You get feedback before merging

### On Merge to Main
- Staging deployment starts automatically
- Infrastructure is updated via Terraform
- Lambda functions are built and deployed
- Frontend is built and deployed to S3
- You get a deployment summary

### For Production Deployment
- Must be triggered manually
- Requires typing "deploy" to confirm
- Requires approval from designated reviewers (if configured)
- Same deployment steps as staging
- Extra safety checks before going live

## Troubleshooting

### "Resource not accessible by integration" Error
- Go to Settings → Actions → General
- Enable "Read and write permissions"
- Save and retry

### AWS Credentials Error
- Verify secrets are correctly named
- Check that IAM users have required permissions
- Test credentials locally:
  ```bash
  export AWS_ACCESS_KEY_ID=your-key
  export AWS_SECRET_ACCESS_KEY=your-secret
  aws sts get-caller-identity
  ```

### Terraform State Lock Error
- Wait for current operation to complete
- Or force unlock (use with caution):
  ```bash
  cd infrastructure
  terraform force-unlock <LOCK_ID>
  ```

### Lambda Build Fails
- Check Python version (should be 3.12)
- Verify requirements-lambda.txt exists
- Test build locally:
  ```bash
  ./scripts/build-lambda-packages.sh
  ```

## Next Steps

After setup is complete:

1. Configure CloudWatch alarms and subscribe to SNS topics
2. Set up custom domain for API Gateway
3. Configure CloudFront distribution for frontend
4. Enable AWS WAF for security
5. Set up automated backups
6. Document runbooks for common issues
7. Train team on deployment procedures

## Support

For issues with setup:
- Check workflow logs in Actions tab
- Review AWS CloudWatch logs
- Consult `.github/workflows/README.md`
- Contact DevOps team

## Security Reminders

- Never commit AWS credentials to the repository
- Rotate access keys every 90 days
- Use least privilege IAM policies
- Enable MFA for production approvers
- Monitor AWS CloudTrail for API activity
- Review workflow runs regularly
