# Step Functions Workflow Documentation

## Overview

The `step_functions_workflow.json` file defines the AWS Step Functions state machine for processing financial documents in the AI Accounting Copilot system. This workflow orchestrates the complete document processing pipeline from OCR extraction through classification, validation, reconciliation, and audit logging.

## Workflow States

### 1. ExtractText
- **Type**: Lambda Task
- **Function**: `ai-accounting-copilot-ocr-processor`
- **Purpose**: Extracts text from uploaded document images using Amazon Textract
- **Retry Policy**: 3 attempts with exponential backoff (2s, 4s, 8s)
- **Error Handling**: Catches OCRFailure and routes to NotifyOCRFailure
- **Next State**: ClassifyTransaction (on success)

### 2. ClassifyTransaction
- **Type**: Lambda Task
- **Function**: `ai-accounting-copilot-transaction-classifier`
- **Purpose**: Classifies the transaction using Amazon Bedrock (Claude 3 Haiku)
- **Retry Policy**: 3 attempts with exponential backoff (2s, 4s, 8s)
- **Error Handling**: Catches all errors and routes to NotifyOCRFailure
- **Next State**: ValidateData

### 3. ValidateData
- **Type**: Lambda Task
- **Function**: `ai-accounting-copilot-data-validator`
- **Purpose**: Validates transaction data (duplicate detection, outlier detection, invoice gaps)
- **Retry Policy**: 3 attempts with exponential backoff (2s, 4s, 8s)
- **Next State**: CheckConfidence

### 4. CheckConfidence
- **Type**: Choice State
- **Purpose**: Routes based on classification confidence score
- **Logic**:
  - If confidence >= 0.7: Route to ReconcileReceipts (auto-approve)
  - If confidence < 0.7: Route to FlagForReview (requires human approval)

### 5. FlagForReview
- **Type**: DynamoDB UpdateItem Task
- **Purpose**: Updates transaction status to "pending_review" and sets flagged_for_review flag
- **Retry Policy**: 3 attempts with exponential backoff for throttling errors
- **Next State**: NotifyPendingApproval

### 6. NotifyPendingApproval
- **Type**: SNS Publish Task
- **Purpose**: Sends notification to user about transaction requiring review
- **Topic**: `ai-accounting-copilot-pending-approvals`
- **Message**: Includes transaction ID, confidence score, category, and amount
- **Retry Policy**: 2 attempts with exponential backoff
- **Next State**: ReconcileReceipts

### 7. ReconcileReceipts
- **Type**: Lambda Task
- **Function**: `ai-accounting-copilot-reconciliation-engine`
- **Purpose**: Matches receipts with bank transactions using fuzzy matching
- **Retry Policy**: 3 attempts with exponential backoff (2s, 4s, 8s)
- **Next State**: LogAuditTrail

### 8. LogAuditTrail
- **Type**: Lambda Task
- **Function**: `ai-accounting-copilot-audit-logger`
- **Purpose**: Records complete workflow execution in audit trail
- **Retry Policy**: 2 attempts with exponential backoff
- **End State**: Workflow completes successfully

### 9. NotifyOCRFailure
- **Type**: SNS Publish Task
- **Purpose**: Notifies user when OCR processing fails
- **Topic**: `ai-accounting-copilot-ocr-failures`
- **Message**: Includes document ID and error details
- **Retry Policy**: 2 attempts with exponential backoff
- **End State**: Workflow terminates (failure path)

## Retry Policies

All retry policies use exponential backoff to handle transient failures gracefully:

- **Lambda Functions**: 3 retries, starting at 2 seconds (2s → 4s → 8s)
- **DynamoDB Operations**: 3 retries, starting at 1 second (1s → 2s → 4s)
- **SNS Notifications**: 2 retries, starting at 2 seconds (2s → 4s)

## Error Handling

The workflow implements comprehensive error handling:

1. **OCR Failures**: Caught at ExtractText state, routes to NotifyOCRFailure
2. **Classification Failures**: Caught at ClassifyTransaction, routes to NotifyOCRFailure
3. **Transient Errors**: Automatically retried with exponential backoff
4. **DynamoDB Throttling**: Retried with backoff to handle provisioned throughput limits
5. **SNS Failures**: Retried to ensure notifications are delivered

## Workflow Paths

### Success Path (High Confidence)
```
ExtractText → ClassifyTransaction → ValidateData → CheckConfidence → ReconcileReceipts → LogAuditTrail → End
```

### Review Path (Low Confidence)
```
ExtractText → ClassifyTransaction → ValidateData → CheckConfidence → FlagForReview → NotifyPendingApproval → ReconcileReceipts → LogAuditTrail → End
```

### Failure Path (OCR Error)
```
ExtractText → NotifyOCRFailure → End
```

## Requirements Satisfied

This workflow implementation satisfies the following requirements:

- **Requirement 1.1**: Automatic document capture and OCR processing
- **Requirement 1.4**: OCR failure notification
- **Requirement 2.1**: Automatic transaction classification
- **Requirement 2.3**: Low confidence flagging for review
- **Requirement 3.1**: Data validation (duplicates, outliers, gaps)
- **Requirement 4.1**: Receipt reconciliation with bank transactions

## Integration with Terraform

The workflow definition can be integrated into the existing `infrastructure/step_functions.tf` file by referencing this JSON file:

```hcl
resource "aws_sfn_state_machine" "document_processing" {
  name     = "${var.project_name}-document-processing"
  role_arn = aws_iam_role.step_functions.arn
  
  definition = file("${path.module}/step_functions_workflow.json")
  
  # ... rest of configuration
}
```

Alternatively, the JSON can be used directly in CloudFormation or for testing with the AWS CLI.

## Testing

To test the workflow:

1. **Start Execution**:
```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:REGION:ACCOUNT:stateMachine:ai-accounting-copilot-document-processing \
  --input '{"document_id":"doc_123","s3_bucket":"my-bucket","s3_key":"documents/user123/doc_123.jpg","user_id":"user123"}'
```

2. **Monitor Execution**:
```bash
aws stepfunctions describe-execution \
  --execution-arn EXECUTION_ARN
```

3. **View Execution History**:
```bash
aws stepfunctions get-execution-history \
  --execution-arn EXECUTION_ARN
```

## Monitoring

The workflow includes:

- **CloudWatch Logs**: All execution data logged for debugging
- **X-Ray Tracing**: Enabled for performance monitoring
- **Metrics**: Execution duration, success/failure rates, state transition counts

## Cost Considerations

- **Step Functions**: $25 per 1 million state transitions
- **Estimated Cost**: ~$0.01/month for 100 documents (9 states × 100 executions = 900 transitions)
- **Within AWS Free Tier**: First 4,000 state transitions per month are free

## Notes

- The workflow uses AWS SDK service integrations (Lambda, DynamoDB, SNS) for optimal performance
- All ARNs use CloudFormation pseudo-parameters (${AWS::Region}, ${AWS::AccountId}) for portability
- The workflow is idempotent - failed executions can be safely retried
- State results are stored in separate paths ($.ocr_result, $.classification_result, etc.) to preserve original input
