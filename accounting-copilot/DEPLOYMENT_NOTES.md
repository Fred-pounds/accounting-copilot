# Deployment Notes

## Important: Environment Variables

The Lambda functions require environment variables that are currently managed outside of Terraform. After any `terraform apply` that modifies Lambda functions, you must re-run:

```bash
./scripts/update-lambda-env-vars.sh
```

This sets the required environment variables:
- DYNAMODB_TABLE
- DOCUMENTS_BUCKET
- WEBSITE_BUCKET
- COGNITO_USER_POOL_ID
- COGNITO_CLIENT_ID
- WORKFLOW_ARN
- SNS_PENDING_APPROVALS
- SNS_OCR_FAILURES
- SNS_UNMATCHED_TRANSACTIONS
- SNS_APPROVAL_REMINDERS
- XRAY_ENABLED
- LOG_LEVEL

## Recommended: Add to Terraform

For production, add these environment variables to `infrastructure/lambda.tf` so they persist across Terraform applies.

## Current Deployment Status

✅ All 12 Lambda functions deployed
✅ API Gateway configured with all routes including `/documents/upload`
✅ Frontend deployed with document upload support
✅ Environment variables configured

## Working Features

- Dashboard (shows summary data)
- Transactions (list/create/approve)
- Documents (list/upload)
- Document Upload (with S3 pre-signed URLs)
- Approvals (list/approve/reject)
- Audit Trail
- Assistant (AI chat)

## Test Credentials

- Email: testuser@example.com
- Password: TestPass123!

## URLs

- Frontend: http://accounting-copilot-web-280250685594.s3-website-eu-west-1.amazonaws.com
- API Gateway: https://l91194lhci.execute-api.eu-west-1.amazonaws.com/dev
