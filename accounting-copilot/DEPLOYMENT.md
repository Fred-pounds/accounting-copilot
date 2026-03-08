# Deployment Guide

This guide walks through deploying the AI Accounting Copilot infrastructure and application.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Terraform** >= 1.0 installed
4. **Python** 3.11 installed
5. **Make** (optional, for using Makefile commands)

## Step 1: Configure AWS Credentials

```bash
aws configure
```

Ensure your AWS credentials have permissions for:
- S3
- DynamoDB
- Lambda
- API Gateway
- Cognito
- Step Functions
- SNS
- CloudWatch
- IAM
- Textract
- Bedrock

## Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or using Make:
```bash
make install
```

## Step 3: Configure Terraform Variables

Create `infrastructure/terraform.tfvars`:

```hcl
aws_region   = "us-east-1"
environment  = "dev"
project_name = "accounting-copilot"

# Optional overrides
# lambda_runtime = "python3.11"
# lambda_timeout = 30
# api_rate_limit = 100
```

## Step 4: Deploy Infrastructure

```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

Or using Make:
```bash
make deploy-infra
```

This will create:
- S3 buckets (documents, website)
- DynamoDB table
- Cognito user pool
- API Gateway
- IAM roles and policies
- SNS topics
- CloudWatch log groups and alarms
- Step Functions state machine

**Note:** Lambda functions are created by Terraform but need code deployment (next step).

## Step 5: Deploy Lambda Functions

After infrastructure is deployed, deploy Lambda function code:

```bash
chmod +x scripts/deploy-lambdas.sh
./scripts/deploy-lambdas.sh
```

This script:
1. Packages each Lambda function with dependencies
2. Creates deployment packages
3. Uploads to AWS Lambda

## Step 6: Enable Bedrock Model Access

The application uses Amazon Bedrock with Claude 3 Haiku. You need to enable model access:

1. Go to AWS Console → Bedrock → Model access
2. Request access to "Claude 3 Haiku" model
3. Wait for approval (usually instant)

## Step 7: Configure SNS Email Subscriptions (Optional)

To receive email notifications:

```bash
# Get SNS topic ARNs from Terraform output
terraform output sns_topic_arns

# Subscribe to topics
aws sns subscribe \
  --topic-arn <TOPIC_ARN> \
  --protocol email \
  --notification-endpoint your-email@example.com

# Confirm subscription via email
```

## Step 8: Verify Deployment

Check that all resources are created:

```bash
# Get outputs
cd infrastructure
terraform output

# Test API Gateway
curl -X GET <API_GATEWAY_URL>/health

# Check Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `accounting-copilot`)].FunctionName'
```

## Step 9: Create Test User

Create a test user in Cognito:

```bash
# Get user pool ID
USER_POOL_ID=$(cd infrastructure && terraform output -raw cognito_user_pool_id)

# Create user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username test@example.com \
  --user-attributes Name=email,Value=test@example.com \
  --temporary-password TempPass123!

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username test@example.com \
  --password YourPassword123! \
  --permanent
```

## Step 10: Deploy Frontend (Optional)

If you have a frontend application:

```bash
# Build frontend
cd frontend
npm install
npm run build

# Get website bucket name
WEBSITE_BUCKET=$(cd ../infrastructure && terraform output -raw website_bucket_name)

# Deploy to S3
aws s3 sync dist/ s3://$WEBSITE_BUCKET/

# Get website URL
cd ../infrastructure
terraform output website_url
```

## Monitoring

### CloudWatch Dashboards

Access CloudWatch dashboards to monitor:
- Lambda invocations and errors
- API Gateway requests and latency
- DynamoDB read/write capacity
- Step Functions executions

### CloudWatch Alarms

Alarms are configured for:
- Lambda error rate > 5%
- API Gateway 5xx errors > 10/min
- DynamoDB throttling
- Step Functions failures > 5/hour

Alarms send notifications to the pending-approvals SNS topic.

### Logs

View logs in CloudWatch Logs:
```bash
aws logs tail /aws/lambda/accounting-copilot-document-upload-handler --follow
```

## Cost Monitoring

Set up AWS Budgets to track costs:

```bash
aws budgets create-budget \
  --account-id <ACCOUNT_ID> \
  --budget file://budget.json
```

Expected monthly costs: $2-6 for typical SME usage (100-200 documents/month)

## Updating the Application

### Update Infrastructure

```bash
cd infrastructure
terraform plan
terraform apply
```

### Update Lambda Functions

```bash
./scripts/deploy-lambdas.sh
```

### Update Individual Lambda

```bash
cd lambda-packages
zip -r function-name.zip .
aws lambda update-function-code \
  --function-name accounting-copilot-function-name \
  --zip-file fileb://function-name.zip
```

## Troubleshooting

### Lambda Function Errors

Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/accounting-copilot-<function-name> --follow
```

### API Gateway 403 Errors

- Verify Cognito token is valid
- Check API Gateway authorizer configuration
- Ensure CORS is properly configured

### Textract Failures

- Verify document format (JPEG, PNG, PDF)
- Check document size (< 10 MB)
- Ensure Textract service is available in your region

### Bedrock Errors

- Verify model access is enabled
- Check IAM permissions for Bedrock
- Ensure region supports Bedrock

## Cleanup

To destroy all resources:

```bash
cd infrastructure
terraform destroy
```

Or using Make:
```bash
make destroy-infra
```

**Warning:** This will delete all data including documents and transactions. Ensure you have backups if needed.

## Security Best Practices

1. **Enable MFA** for Cognito users in production
2. **Restrict S3 bucket access** to specific CloudFront distributions
3. **Use AWS Secrets Manager** for sensitive configuration
4. **Enable AWS CloudTrail** for audit logging
5. **Implement least privilege** IAM policies
6. **Enable VPC endpoints** for private AWS service access
7. **Use AWS WAF** with API Gateway in production

## Production Checklist

- [ ] Configure custom domain for API Gateway
- [ ] Set up CloudFront distribution for website
- [ ] Enable MFA for Cognito
- [ ] Configure backup strategy for DynamoDB
- [ ] Set up AWS Budgets and cost alerts
- [ ] Enable AWS CloudTrail
- [ ] Configure AWS WAF rules
- [ ] Set up monitoring dashboards
- [ ] Document runbooks for common issues
- [ ] Configure SNS email subscriptions
- [ ] Test disaster recovery procedures
- [ ] Review and tighten IAM policies
- [ ] Enable S3 versioning for critical buckets
- [ ] Configure log retention policies
- [ ] Set up automated testing pipeline

## Support

For issues or questions:
- Check CloudWatch Logs for error details
- Review Terraform state for resource configuration
- Consult AWS documentation for service-specific issues
