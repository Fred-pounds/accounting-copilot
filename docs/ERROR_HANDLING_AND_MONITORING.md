# Error Handling and Monitoring

This document describes the comprehensive error handling and monitoring implementation for the AI Accounting Copilot system.

## Overview

The system implements a multi-layered approach to error handling and monitoring:

1. **Comprehensive Error Handling** - Custom exception classes and centralized error handling
2. **CloudWatch Monitoring** - Alarms and dashboards for key metrics
3. **AWS X-Ray Tracing** - Distributed tracing for performance monitoring

## 1. Error Handling

### Custom Exception Classes

All Lambda functions use custom exception classes defined in `src/shared/exceptions.py`:

- **ValidationError** (400) - Client input validation errors
- **NotFoundError** (404) - Resource not found errors
- **AuthenticationError** (401) - Authentication failures
- **AuthorizationError** (403) - Authorization failures
- **ConflictError** (409) - Resource conflict errors
- **OCRFailure** (502) - OCR processing failures
- **ClassificationError** (500) - Transaction classification errors
- **BedrockError** (502) - Bedrock API errors
- **RepositoryError** (500) - DynamoDB repository errors
- **ThrottlingError** (429) - DynamoDB throttling errors

### Error Response Format

All errors return a consistent JSON format:

```json
{
  "error": {
    "code": "ERR_400",
    "message": "Validation error message",
    "details": {
      "field": "additional context"
    },
    "request_id": "abc-123-def",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Handling Decorators

#### Lambda Error Handler

For API Gateway Lambda functions:

```python
from shared.error_handler import lambda_error_handler
from shared.xray_tracing import trace_lambda_handler

@lambda_error_handler
@trace_lambda_handler
def lambda_handler(event, context):
    # Your handler code
    pass
```

Features:
- Automatic try-catch blocks
- Proper HTTP error responses
- CloudWatch logging with appropriate severity levels
- Request ID tracking
- X-Ray tracing integration

#### Step Functions Error Handler

For Step Functions task Lambda functions:

```python
from shared.error_handler import step_function_error_handler
from shared.xray_tracing import trace_lambda_handler

@step_function_error_handler
@trace_lambda_handler
def lambda_handler(event, context):
    # Your handler code
    pass
```

Features:
- Logs errors appropriately
- Preserves exceptions for Step Functions error handling
- X-Ray tracing integration

### CloudWatch Logging

All Lambda functions log to CloudWatch with structured logging:

```python
from shared.logger import get_logger

logger = get_logger(__name__)

# Log levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error message")
```

**Log Severity Guidelines:**

- **DEBUG** - Detailed diagnostic information
- **INFO** - General informational messages (request started, completed)
- **WARNING** - Client errors (400, 404) and expected failures
- **ERROR** - Application errors (500) and unexpected failures
- **CRITICAL** - Unhandled exceptions with full traceback

## 2. CloudWatch Monitoring

### CloudWatch Alarms

The system has the following alarms configured:

#### Lambda Error Rate Alarm
- **Metric**: Lambda Errors
- **Threshold**: > 5% error rate
- **Evaluation**: 2 periods of 5 minutes
- **Action**: Send SNS notification

#### API Gateway 5xx Errors Alarm
- **Metric**: API Gateway 5XXError
- **Threshold**: > 10 errors per minute
- **Evaluation**: 2 periods of 1 minute
- **Action**: Send SNS notification

#### DynamoDB Throttling Alarm
- **Metric**: DynamoDB UserErrors
- **Threshold**: > 0 throttling events
- **Evaluation**: 1 period of 5 minutes
- **Action**: Send SNS notification

#### Textract Failure Rate Alarm
- **Metric**: Textract UserErrorCount
- **Threshold**: > 20% failure rate (> 5 errors)
- **Evaluation**: 2 periods of 5 minutes
- **Action**: Send SNS notification

#### Step Functions Execution Failures Alarm
- **Metric**: Step Functions ExecutionsFailed
- **Threshold**: > 5 failures per hour
- **Evaluation**: 1 period of 1 hour
- **Action**: Send SNS notification

### CloudWatch Dashboard

A comprehensive dashboard displays key metrics:

**Lambda Metrics Widget:**
- Lambda Errors (Sum)
- Lambda Invocations (Sum)
- Average Duration (ms)
- Lambda Throttles (Sum)

**API Gateway Metrics Widget:**
- 5XX Errors (Sum)
- 4XX Errors (Sum)
- Total Requests (Sum)
- Average Latency (ms)

**DynamoDB Metrics Widget:**
- Read Capacity Units (Sum)
- Write Capacity Units (Sum)
- User Errors/Throttles (Sum)
- System Errors (Sum)

**Step Functions Metrics Widget:**
- Executions Started (Sum)
- Executions Succeeded (Sum)
- Executions Failed (Sum)
- Average Execution Time (ms)

**Textract Metrics Widget:**
- Average Response Time (ms)
- User Errors (Sum)
- Server Errors (Sum)
- Successful Requests (Sum)

**Recent Errors Log Widget:**
- Shows last 20 ERROR-level log entries across all Lambda functions

### Accessing the Dashboard

1. Open AWS Console
2. Navigate to CloudWatch
3. Select "Dashboards" from the left menu
4. Open "ai-accounting-copilot-dashboard"

## 3. AWS X-Ray Tracing

### Overview

X-Ray provides distributed tracing across all Lambda functions and AWS services, enabling:
- End-to-end request tracking
- Performance bottleneck identification
- Service dependency mapping
- Error rate analysis

### Configuration

X-Ray is enabled for all Lambda functions via Terraform:

```hcl
resource "aws_lambda_function" "example" {
  # ... other configuration ...
  
  tracing_config {
    mode = "Active"
  }
  
  environment {
    variables = {
      XRAY_ENABLED = "true"
    }
  }
}
```

### Usage in Lambda Functions

#### Basic Tracing

All Lambda handlers are automatically traced:

```python
from shared.xray_tracing import trace_lambda_handler

@trace_lambda_handler
def lambda_handler(event, context):
    # Automatically traced
    pass
```

#### Custom Subsegments

Trace specific operations:

```python
from shared.xray_tracing import trace_subsegment

with trace_subsegment('database_query', {'table': 'transactions'}):
    result = table.query(...)
```

#### Function Tracing

Trace specific functions:

```python
from shared.xray_tracing import trace_function

@trace_function('process_transaction')
def process_transaction(transaction_id):
    # Function execution is traced
    pass
```

#### Annotations and Metadata

Add searchable annotations and metadata:

```python
from shared.xray_tracing import add_annotation, add_metadata

# Annotations (indexed, searchable)
add_annotation('user_id', user_id)
add_annotation('transaction_id', transaction_id)

# Metadata (not indexed, any JSON data)
add_metadata('request_details', {
    'amount': 100.50,
    'category': 'Office Supplies'
})
```

### Automatic AWS Service Tracing

The X-Ray SDK automatically traces calls to:
- DynamoDB
- S3
- Textract
- Bedrock
- SNS
- Step Functions

### Viewing Traces

1. Open AWS Console
2. Navigate to X-Ray
3. Select "Traces" from the left menu
4. Use filters to find specific traces:
   - Filter by annotation: `user_id = "abc123"`
   - Filter by HTTP status: `http.status = 500`
   - Filter by error: `error = true`

### Service Map

The X-Ray service map shows:
- All services and their dependencies
- Request rates between services
- Error rates for each service
- Average latency for each service

Access via: AWS Console → X-Ray → Service map

## 4. Error Notification Flow

### SNS Topics

The system uses SNS topics for error notifications:

1. **pending-approvals** - General alerts and alarms
2. **ocr-failures** - OCR processing failures
3. **unmatched-transactions** - Unreconciled transactions

### Notification Triggers

**OCR Failures:**
- Textract API errors
- Document parsing failures
- Invalid document formats

**Validation Issues:**
- Duplicate transactions detected
- Outlier amounts detected
- Missing invoice numbers

**Reconciliation Issues:**
- Unmatched transactions > 7 days old

## 5. Best Practices

### For Developers

1. **Always use custom exceptions** - Don't raise generic `Exception`
2. **Log with appropriate severity** - Use correct log levels
3. **Add context to errors** - Include relevant details in error messages
4. **Use X-Ray subsegments** - Trace key operations for performance insights
5. **Test error paths** - Ensure error handling works correctly

### For Operations

1. **Monitor CloudWatch alarms** - Set up email/SMS notifications
2. **Review dashboard daily** - Check for anomalies
3. **Investigate X-Ray traces** - When errors occur, check traces for root cause
4. **Set up log insights queries** - Create saved queries for common issues
5. **Review error trends** - Look for patterns in error rates

### Example Log Insights Queries

**Find all errors in the last hour:**
```
fields @timestamp, @message, @logStream
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

**Find slow Lambda invocations:**
```
fields @timestamp, @duration, @requestId
| filter @duration > 5000
| sort @duration desc
| limit 20
```

**Count errors by Lambda function:**
```
fields @logStream
| filter @message like /ERROR/
| stats count() by @logStream
| sort count() desc
```

## 6. Troubleshooting

### High Error Rate

1. Check CloudWatch dashboard for affected services
2. Review X-Ray service map for failing dependencies
3. Check recent deployments or configuration changes
4. Review CloudWatch Logs for error details

### Performance Issues

1. Check X-Ray traces for slow operations
2. Review DynamoDB throttling metrics
3. Check Lambda memory and timeout settings
4. Review Textract/Bedrock API latency

### Missing Traces

1. Verify X-Ray is enabled: `XRAY_ENABLED=true`
2. Check IAM permissions for X-Ray write access
3. Verify X-Ray SDK is installed: `aws-xray-sdk>=2.12.0`
4. Check Lambda execution role has `AWSXRayDaemonWriteAccess` policy

## 7. Maintenance

### Log Retention

- Lambda logs: 30 days (90 days for audit logs)
- X-Ray traces: 30 days (AWS default)

### Alarm Tuning

Review and adjust alarm thresholds quarterly based on:
- Actual error rates
- False positive rate
- System growth and usage patterns

### Dashboard Updates

Update dashboard widgets when:
- New Lambda functions are added
- New metrics become relevant
- Business requirements change
