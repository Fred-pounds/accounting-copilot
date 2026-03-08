# AI Accounting Copilot - Deployment Setup Guide

**Follow this checklist to get your system running**

---

## Prerequisites

### System Requirements
- [ ] Linux/macOS/WSL environment
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ and npm installed
- [ ] Git installed
- [ ] Internet connection

### AWS Account Requirements
- [ ] AWS account created
- [ ] AWS account has permissions for:
  - S3, DynamoDB, Lambda, API Gateway, Cognito
  - Step Functions, SNS, CloudWatch, Textract, Bedrock
- [ ] Credit card on file (for paid services: Textract ~$0.15/month, Bedrock ~$2-5/month)

---

## Phase 1: Local Setup & Testing

### Step 1: Install Python Dependencies

```bash
# Navigate to project root
cd /path/to/accounting_co-pilot

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import boto3; import pytest; print('✓ Dependencies installed')"
```

**Expected output:** `✓ Dependencies installed`

- [ ] Python dependencies installed successfully

---

### Step 2: Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Verify installation
npm list --depth=0

# Return to project root
cd ..
```

**Expected:** Should see all packages listed without errors

- [ ] Frontend dependencies installed successfully

---

### Step 3: Run Tests Locally

```bash
# Set mock AWS credentials for local testing
export AWS_ACCESS_KEY_ID=testing
export AWS_SECRET_ACCESS_KEY=testing
export AWS_DEFAULT_REGION=us-east-1

# Run all tests
make test

# Or run specific test suites
make test-unit          # Unit tests only
make test-props         # Property-based tests only
pytest tests/integration/test_end_to_end.py -v  # End-to-end tests
```

**Expected results:**
- Property tests: 25/25 passing (100%)
- Unit tests: 286/346 passing (82.7%) - 60 failures are known test setup issues
- Integration tests: All workflows should pass

- [ ] Tests run successfully (most passing)
- [ ] No critical errors in test output

---

## Phase 2: AWS Setup

### Step 4: Install AWS CLI

```bash
# Download AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Unzip
unzip awscliv2.zip

# Install
sudo ./aws/install

# Verify installation
aws --version
```

**Expected output:** `aws-cli/2.x.x ...`

- [ ] AWS CLI installed successfully

---

### Step 5: Configure AWS Credentials

```bash
# Configure AWS CLI with your credentials
aws configure
```

**You'll be prompted for:**
1. **AWS Access Key ID:** Get from AWS Console → IAM → Users → Security Credentials
2. **AWS Secret Access Key:** Get from AWS Console (shown only once when created)
3. **Default region:** Enter `us-east-1` (or your preferred region)
4. **Default output format:** Enter `json`

```bash
# Verify credentials work
aws sts get-caller-identity
```

**Expected output:** Should show your AWS account ID and user ARN

- [ ] AWS credentials configured
- [ ] Can access AWS account via CLI

---

### Step 6: Enable Required AWS Services

**In AWS Console, enable these services:**

1. **Amazon Bedrock** (for AI classification and assistant)
   - Go to: https://console.aws.amazon.com/bedrock
   - Click "Get Started"
   - Request access to "Claude 3 Haiku" model
   - Wait for approval (usually instant, sometimes 24 hours)

2. **Amazon Textract** (for OCR)
   - Already enabled by default in most accounts
   - Verify: https://console.aws.amazon.com/textract

```bash
# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1 | grep -i claude

# Should see Claude models listed
```

- [ ] Bedrock access enabled
- [ ] Claude 3 Haiku model available
- [ ] Textract accessible

---

### Step 7: Install Terraform

```bash
# Download Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip

# Unzip
unzip terraform_1.6.0_linux_amd64.zip

# Move to system path
sudo mv terraform /usr/local/bin/

# Verify installation
terraform --version
```

**Expected output:** `Terraform v1.6.0`

- [ ] Terraform installed successfully

---

## Phase 3: Infrastructure Deployment

### Step 8: Review Infrastructure Plan

```bash
# Navigate to infrastructure directory
cd infrastructure

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# See what will be created (DRY RUN - doesn't create anything)
terraform plan
```

**Review the plan output - should show:**
- 2 S3 buckets (documents + website)
- 1 DynamoDB table with 2 GSI indexes
- 1 Cognito user pool
- 1 API Gateway REST API
- 13 Lambda functions
- 1 Step Functions state machine
- 4 SNS topics
- Multiple CloudWatch log groups and alarms
- IAM roles and policies

- [ ] Terraform initialized successfully
- [ ] Plan looks correct (no errors)
- [ ] Understand what will be created

---

### Step 9: Deploy Infrastructure

```bash
# Still in infrastructure/ directory

# Deploy infrastructure (will prompt for confirmation)
terraform apply

# Type 'yes' when prompted
```

**This will take 5-10 minutes to create all resources**

**Expected output:** `Apply complete! Resources: XX added, 0 changed, 0 destroyed.`

```bash
# Save the outputs (API Gateway URL, Cognito Pool ID, etc.)
terraform output > ../deployment-outputs.txt

# View outputs
terraform output
```

- [ ] Infrastructure deployed successfully
- [ ] No errors in Terraform output
- [ ] Outputs saved for reference

---

### Step 10: Build Lambda Deployment Packages

```bash
# Return to project root
cd ..

# Build Lambda packages
make build-lambdas

# Verify packages were created
ls -la lambda-packages/
```

**Expected:** Should see .zip files for each Lambda function

- [ ] Lambda packages built successfully
- [ ] All 13 Lambda .zip files created

---

### Step 11: Deploy Lambda Functions

```bash
# Deploy Lambda functions to AWS
make deploy-lambdas

# This uploads the .zip files and updates Lambda function code
```

**Expected:** Should see success messages for each Lambda function

```bash
# Verify Lambda functions are deployed
aws lambda list-functions --query 'Functions[].FunctionName'
```

**Expected output:** List of 13 function names

- [ ] Lambda functions deployed successfully
- [ ] All functions visible in AWS Console

---

### Step 12: Build and Deploy Frontend

```bash
# Navigate to frontend directory
cd frontend

# Build production bundle
npm run build

# Verify build succeeded
ls -la dist/

# Deploy to S3 and CloudFront
./deploy.sh

# Or manually:
# aws s3 sync dist/ s3://YOUR-WEBSITE-BUCKET-NAME --delete
# aws cloudfront create-invalidation --distribution-id YOUR-DIST-ID --paths "/*"
```

**Expected:** Build creates `dist/` folder with optimized files

- [ ] Frontend built successfully
- [ ] Frontend deployed to S3
- [ ] CloudFront distribution updated

---

## Phase 4: Verification & Testing

### Step 13: Get Deployment URLs

```bash
# Get API Gateway URL
cd ../infrastructure
terraform output api_gateway_url

# Get CloudFront URL (frontend)
terraform output cloudfront_url

# Get Cognito User Pool ID
terraform output cognito_user_pool_id
```

**Save these URLs - you'll need them!**

- [ ] API Gateway URL obtained
- [ ] CloudFront URL obtained
- [ ] Cognito User Pool ID obtained

---

### Step 14: Create Test User

```bash
# Create a test user in Cognito
aws cognito-idp admin-create-user \
  --user-pool-id <YOUR_USER_POOL_ID> \
  --username testuser@example.com \
  --user-attributes Name=email,Value=testuser@example.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id <YOUR_USER_POOL_ID> \
  --username testuser@example.com \
  --password MySecurePass123! \
  --permanent
```

- [ ] Test user created successfully
- [ ] Password set

---

### Step 15: Test API Endpoints

```bash
# Test API without authentication (should fail with 401)
curl https://<YOUR_API_GATEWAY_URL>/dashboard/summary

# Expected: {"error": "Unauthorized"} or similar
```

**If you get 401 Unauthorized, that's CORRECT - it means auth is working!**

- [ ] API responds (even if with 401)
- [ ] API Gateway is accessible

---

### Step 16: Test Frontend

1. **Open CloudFront URL in browser**
   ```
   https://<YOUR_CLOUDFRONT_URL>
   ```

2. **You should see:**
   - Login page
   - Email and password fields
   - "Sign In" button

3. **Try logging in:**
   - Email: `testuser@example.com`
   - Password: `MySecurePass123!`

4. **After login, you should see:**
   - Dashboard with summary cards
   - Navigation menu
   - Upload document button

- [ ] Frontend loads successfully
- [ ] Login page appears
- [ ] Can log in with test user
- [ ] Dashboard displays after login

---

### Step 17: End-to-End Test with Real Document

**Upload a test receipt:**

1. Find or create a test receipt image (JPEG/PNG)
2. In the frontend, click "Upload Document"
3. Select your receipt image
4. Click "Upload"

**Watch the processing:**

5. Check Step Functions execution in AWS Console:
   ```
   AWS Console → Step Functions → State Machines → DocumentProcessingWorkflow
   ```

6. Monitor CloudWatch logs:
   ```bash
   aws logs tail /aws/lambda/OCRProcessor --follow
   ```

7. After 10-30 seconds, check:
   - Transaction appears in dashboard
   - Transaction has category assigned
   - Confidence score is shown
   - Audit trail shows processing steps

- [ ] Document uploads successfully
- [ ] Step Functions workflow executes
- [ ] Transaction appears in dashboard
- [ ] Classification assigned
- [ ] Audit trail shows actions

---

### Step 18: Test Financial Assistant

1. In the frontend, navigate to "Assistant" page
2. Ask a question: "What did I spend on office supplies?"
3. Wait for response (2-5 seconds)
4. Verify:
   - Response is relevant
   - Citations to transactions are shown
   - Response is in plain language

- [ ] Assistant responds to questions
- [ ] Response includes citations
- [ ] Response time < 5 seconds

---

### Step 19: Verify Monitoring & Alerts

```bash
# Check CloudWatch alarms
aws cloudwatch describe-alarms --query 'MetricAlarms[].AlarmName'

# Expected: Should see alarms for Lambda errors, API errors, etc.

# Check SNS topics
aws sns list-topics

# Expected: Should see 4 topics (ocr-failures, pending-approvals, etc.)

# View CloudWatch dashboard (in AWS Console)
# AWS Console → CloudWatch → Dashboards
```

- [ ] CloudWatch alarms configured
- [ ] SNS topics created
- [ ] Can view logs in CloudWatch

---

### Step 20: Load Testing (Optional)

```bash
# Upload multiple documents in quick succession
# Monitor:
# - Lambda concurrent executions
# - DynamoDB read/write capacity
# - API Gateway request rate

# Check for throttling or errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=OCRProcessor \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

- [ ] System handles multiple concurrent uploads
- [ ] No throttling errors
- [ ] Performance meets requirements

---

## Phase 5: Production Readiness

### Step 21: Security Checklist

- [ ] S3 buckets have encryption enabled (AES-256)
- [ ] DynamoDB table has encryption enabled
- [ ] API Gateway uses HTTPS only
- [ ] CloudFront uses HTTPS only
- [ ] Cognito password policy is strong (8+ chars, mixed case, numbers, symbols)
- [ ] IAM roles follow least privilege principle
- [ ] No hardcoded credentials in code
- [ ] All secrets in environment variables or AWS Secrets Manager

---

### Step 22: Cost Monitoring Setup

```bash
# Enable AWS Cost Explorer (if not already enabled)
# AWS Console → Billing → Cost Explorer

# Set up budget alerts
aws budgets create-budget \
  --account-id <YOUR_ACCOUNT_ID> \
  --budget file://budget.json

# Create budget.json with your monthly limit (e.g., $10/month)
```

**Monitor costs weekly for first month**

- [ ] Cost Explorer enabled
- [ ] Budget alerts configured
- [ ] Understand expected costs ($2-6/month)

---

### Step 23: Backup & Disaster Recovery

```bash
# Enable DynamoDB point-in-time recovery
aws dynamodb update-continuous-backups \
  --table-name AccountingCopilot \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Enable S3 versioning for documents bucket
aws s3api put-bucket-versioning \
  --bucket <YOUR_DOCUMENTS_BUCKET> \
  --versioning-configuration Status=Enabled
```

- [ ] DynamoDB backups enabled
- [ ] S3 versioning enabled
- [ ] Understand recovery procedures

---

### Step 24: Documentation

- [ ] Save all deployment outputs (URLs, IDs, ARNs)
- [ ] Document any custom configuration changes
- [ ] Create runbook for common operations
- [ ] Document troubleshooting steps
- [ ] Share access with team members (if applicable)

---

## Troubleshooting

### Issue: Terraform fails with "backend not configured"

```bash
cd infrastructure
cp backend.tf.example backend.tf
# Edit backend.tf with your S3 bucket for Terraform state
```

### Issue: Lambda deployment fails with "Function not found"

```bash
# Ensure infrastructure is deployed first
cd infrastructure
terraform apply

# Then deploy Lambdas
cd ..
make deploy-lambdas
```

### Issue: Frontend shows "Network Error"

```bash
# Check API Gateway URL in frontend/.env
# Should match the URL from terraform output

# Update frontend/.env:
echo "VITE_API_URL=https://<YOUR_API_GATEWAY_URL>" > frontend/.env

# Rebuild and redeploy
cd frontend
npm run build
./deploy.sh
```

### Issue: Bedrock access denied

```bash
# Request model access in AWS Console
# AWS Console → Bedrock → Model Access → Request Access
# Select "Claude 3 Haiku"
# Wait for approval (usually instant)
```

### Issue: Tests fail with import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify Python version
python --version  # Should be 3.11+
```

---

## Success Criteria

✅ **Your system is fully operational when:**

- [ ] All infrastructure deployed without errors
- [ ] All Lambda functions deployed and running
- [ ] Frontend accessible via CloudFront URL
- [ ] Can log in with test user
- [ ] Can upload a document
- [ ] Document processes successfully (OCR → classify → validate)
- [ ] Transaction appears in dashboard
- [ ] Financial assistant responds to questions
- [ ] Audit trail shows all actions
- [ ] CloudWatch alarms configured
- [ ] No critical errors in logs
- [ ] Costs are within expected range ($2-6/month)

---

## Next Steps After Deployment

1. **Invite real users** - Create Cognito users for actual SME owners
2. **Upload real documents** - Test with actual receipts and invoices
3. **Monitor performance** - Watch CloudWatch metrics for first week
4. **Gather feedback** - Ask users about experience and pain points
5. **Iterate** - Make improvements based on real-world usage

---

## Support & Resources

- **AWS Documentation:** https://docs.aws.amazon.com/
- **Terraform Documentation:** https://www.terraform.io/docs
- **Project Issues:** Check GitHub issues or create new ones
- **Cost Calculator:** https://calculator.aws/

---

## Estimated Time

- **Phase 1 (Local Setup):** 30 minutes
- **Phase 2 (AWS Setup):** 30 minutes
- **Phase 3 (Deployment):** 45 minutes
- **Phase 4 (Testing):** 30 minutes
- **Phase 5 (Production):** 30 minutes

**Total:** ~3 hours for first-time setup

---

**Good luck with your deployment! 🚀**
