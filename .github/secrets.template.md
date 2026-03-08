# GitHub Secrets Template

This file lists all required GitHub secrets for CI/CD workflows.

## How to Add Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter the name and value
5. Click **Add secret**

## Required Secrets

### Staging Environment

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `AWS_ACCESS_KEY_ID` | AWS access key for staging | Create IAM user in AWS Console → Security credentials → Create access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for staging | Shown once when creating access key - save it securely |
| `STAGING_API_URL` | API Gateway URL for staging | Run `terraform output api_gateway_url` after deploying infrastructure |
| `STAGING_COGNITO_USER_POOL_ID` | Cognito User Pool ID | Run `terraform output cognito_user_pool_id` |
| `STAGING_COGNITO_CLIENT_ID` | Cognito Client ID | Run `terraform output cognito_client_id` |

### Production Environment

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `AWS_ACCESS_KEY_ID_PROD` | AWS access key for production | Create separate IAM user for production |
| `AWS_SECRET_ACCESS_KEY_PROD` | AWS secret key for production | From production IAM user access key |
| `PROD_API_URL` | API Gateway URL for production | Run `terraform output api_gateway_url` in production |
| `PROD_COGNITO_USER_POOL_ID` | Cognito User Pool ID | Run `terraform output cognito_user_pool_id` in production |
| `PROD_COGNITO_CLIENT_ID` | Cognito Client ID | Run `terraform output cognito_client_id` in production |

## Optional Secrets

| Secret Name | Description | Required For |
|------------|-------------|--------------|
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | Slack notifications |
| `TF_API_TOKEN` | Terraform Cloud API token | Remote Terraform state |
| `CODECOV_TOKEN` | Codecov token for coverage reports | Code coverage tracking |

## Getting Terraform Outputs

After deploying infrastructure, get the required values:

```bash
# Navigate to infrastructure directory
cd infrastructure

# Get all outputs
terraform output

# Get specific output
terraform output api_gateway_url
terraform output cognito_user_pool_id
terraform output cognito_client_id
terraform output website_bucket_name
terraform output cloudfront_distribution_id
```

## Creating IAM Users

### Staging IAM User

```bash
# Create user
aws iam create-user --user-name github-actions-staging

# Attach policy (adjust as needed)
aws iam attach-user-policy \
  --user-name github-actions-staging \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Create access key
aws iam create-access-key --user-name github-actions-staging
```

### Production IAM User

```bash
# Create user
aws iam create-user --user-name github-actions-production

# Attach policy (adjust as needed)
aws iam attach-user-policy \
  --user-name github-actions-production \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Create access key
aws iam create-access-key --user-name github-actions-production
```

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Use separate credentials** for staging and production
3. **Rotate access keys** every 90 days
4. **Use least privilege** IAM policies
5. **Enable MFA** for production IAM users
6. **Audit secret access** regularly
7. **Delete unused secrets** immediately

## Verification

After adding secrets, verify they work:

1. Go to **Actions** tab
2. Select **Run Tests** workflow
3. Click **Run workflow**
4. Check if workflow completes successfully

If workflow fails with authentication errors, verify:
- Secret names match exactly (case-sensitive)
- Secret values are correct (no extra spaces)
- IAM user has required permissions
- AWS credentials are valid

## Troubleshooting

### Secret Not Found

**Error:** `Secret AWS_ACCESS_KEY_ID not found`

**Solution:**
1. Verify secret name matches exactly
2. Check secret is in repository secrets (not environment secrets)
3. Ensure workflow has permission to access secrets

### Invalid Credentials

**Error:** `The security token included in the request is invalid`

**Solution:**
1. Verify access key and secret key are correct
2. Check IAM user exists and is active
3. Ensure credentials haven't been rotated
4. Test credentials locally:
   ```bash
   export AWS_ACCESS_KEY_ID=<key>
   export AWS_SECRET_ACCESS_KEY=<secret>
   aws sts get-caller-identity
   ```

### Permission Denied

**Error:** `User is not authorized to perform: lambda:UpdateFunctionCode`

**Solution:**
1. Check IAM user policies
2. Attach required permissions
3. Use PowerUserAccess or create custom policy

## Support

For issues with secrets:
- Check GitHub Actions logs for specific error messages
- Verify IAM permissions in AWS Console
- Test credentials locally before adding to GitHub
- Contact DevOps team for assistance
