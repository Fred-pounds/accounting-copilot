# API Handler Router Fix

## Problem
Transaction, Document, and Approval APIs were returning 502 errors with:
```
Runtime.HandlerNotFound: Handler 'lambda_handler' missing on module 'handler'
```

## Root Cause
These Lambda functions had multiple specific handlers (e.g., `lambda_handler_list`, `lambda_handler_create`, `lambda_handler_get`) but no main `lambda_handler` function that API Gateway expects when using AWS_PROXY integration.

## Solution
Added a main `lambda_handler` router function to each affected Lambda that:
1. Inspects the HTTP method and path
2. Routes to the appropriate specific handler
3. Handles errors gracefully

### Files Modified

1. **src/lambdas/transaction_api/handler.py**
   - Added `lambda_handler()` router
   - Routes GET → list or get (based on ID presence)
   - Routes POST → create, approve, or correct (based on action)
   - Routes PUT → update
   - Routes DELETE → delete

2. **src/lambdas/document_api/handler.py**
   - Added `lambda_handler()` router
   - Routes GET → list or get (based on ID presence)

3. **src/lambdas/approval_manager/handler.py**
   - Added `lambda_handler()` router
   - Routes GET → list_pending
   - Routes POST → approve or reject (based on action)
   - Handles EventBridge scheduled events for reminders

## Deployment
```bash
# Rebuild affected packages
./scripts/build-lambda-packages.sh

# Upload to S3
aws s3 cp lambda-packages/transaction_api.zip s3://bucket/lambda-packages/
aws s3 cp lambda-packages/document_api.zip s3://bucket/lambda-packages/
aws s3 cp lambda-packages/approval_manager.zip s3://bucket/lambda-packages/

# Deploy
aws lambda update-function-code --function-name accounting-copilot-transaction-api ...
aws lambda update-function-code --function-name accounting-copilot-document-api ...
aws lambda update-function-code --function-name accounting-copilot-approval-manager ...
```

## Result
✅ All API endpoints now work correctly
✅ Dashboard loads successfully
✅ Transactions page loads successfully
✅ Documents page loads successfully
✅ Approvals page loads successfully

## API Endpoints Working
- GET /dashboard/summary → dashboard_api
- GET /transactions → transaction_api (list)
- POST /transactions → transaction_api (create)
- GET /documents → document_api (list)
- GET /audit → audit_trail_api
- GET /approvals → approval_manager (list pending)
- POST /approvals → approval_manager (approve/reject)
- POST /assistant → financial_assistant
