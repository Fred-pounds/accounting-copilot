# Category Statistics Updater Lambda Function

## Overview

This Lambda function maintains category statistics for transaction outlier detection. It calculates and updates statistical metrics (count, total, average, standard deviation, min, max) for each category per user per month.

## Requirements

- **3.3**: Detect transactions with amounts exceeding 3 standard deviations from category average
- **3.4**: Flag unusual transactions for review

## Trigger Modes

### 1. DynamoDB Streams (Event-Driven)

The function is triggered automatically when transactions are created, updated, or deleted in DynamoDB.

**Event Source**: DynamoDB Streams on the `AccountingCopilot` table
**Filter**: Records with `SK` starting with `TXN#`

**Behavior**:
- Extracts user_id, category, and month from the transaction
- Recalculates statistics for that specific category and month
- Updates the CategoryStats record in DynamoDB

**Example Stream Event**:
```json
{
  "Records": [
    {
      "eventName": "INSERT",
      "dynamodb": {
        "NewImage": {
          "PK": {"S": "USER#user123"},
          "SK": {"S": "TXN#txn_abc123"},
          "category": {"S": "Office Supplies"},
          "date": {"S": "2024-01-15"},
          "amount": {"N": "45.99"}
        }
      }
    }
  ]
}
```

### 2. EventBridge Scheduled Job (Daily Recalculation)

The function runs as a scheduled job (daily) to recalculate all statistics for all users, ensuring data consistency.

**Event Source**: EventBridge rule (cron expression: `cron(0 2 * * ? *)` - runs at 2 AM UTC daily)

**Behavior**:
- Queries all user profiles
- For each user, finds all unique (category, month) combinations
- Recalculates statistics for each combination
- Updates all CategoryStats records

**Example Scheduled Event**:
```json
{
  "source": "aws.events",
  "detail-type": "Scheduled Event",
  "time": "2024-01-15T02:00:00Z"
}
```

## Statistics Calculated

For each category per user per month:

- **transaction_count**: Number of transactions in the category
- **total_amount**: Sum of all transaction amounts
- **average_amount**: Mean of transaction amounts
- **std_deviation**: Standard deviation of amounts (requires ≥2 transactions)
- **min_amount**: Minimum transaction amount
- **max_amount**: Maximum transaction amount
- **updated_at**: Timestamp of last update

## DynamoDB Schema

**CategoryStats Record**:
```json
{
  "PK": "USER#user123",
  "SK": "STATS#Office Supplies#2024-01",
  "entity_type": "category_stats",
  "category": "Office Supplies",
  "month": "2024-01",
  "transaction_count": 15,
  "total_amount": 450.00,
  "average_amount": 30.00,
  "std_deviation": 12.50,
  "min_amount": 10.00,
  "max_amount": 75.00,
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Usage by Data Validator

The Data Validator Lambda function uses these statistics to detect outliers:

```python
# Get category statistics
stats = table.get_item(
    Key={
        'PK': f"USER#{user_id}",
        'SK': f"STATS#{category}#{month}"
    }
)

# Calculate z-score
if stats['transaction_count'] >= 10:
    z_score = abs((amount - stats['average_amount']) / stats['std_deviation'])
    is_outlier = z_score > 3.0  # More than 3 standard deviations
```

## Configuration

**Environment Variables**:
- `DYNAMODB_TABLE`: Name of the DynamoDB table (default: `AccountingCopilot`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

**Lambda Configuration**:
- **Runtime**: Python 3.11
- **Memory**: 512 MB
- **Timeout**: 60 seconds (stream), 300 seconds (scheduled)
- **Concurrency**: Reserved concurrency recommended for scheduled job

## IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/AccountingCopilot",
        "arn:aws:dynamodb:*:*:table/AccountingCopilot/index/GSI1",
        "arn:aws:dynamodb:*:*:table/AccountingCopilot/index/GSI2"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetRecords",
        "dynamodb:GetShardIterator",
        "dynamodb:DescribeStream",
        "dynamodb:ListStreams"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/AccountingCopilot/stream/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Deployment

### DynamoDB Streams Setup

1. Enable DynamoDB Streams on the `AccountingCopilot` table:
   - Stream view type: `NEW_AND_OLD_IMAGES`

2. Create event source mapping:
```bash
aws lambda create-event-source-mapping \
  --function-name category-stats-updater \
  --event-source-arn arn:aws:dynamodb:REGION:ACCOUNT:table/AccountingCopilot/stream/STREAM_ID \
  --starting-position LATEST \
  --batch-size 100 \
  --maximum-batching-window-in-seconds 5
```

### EventBridge Scheduled Job Setup

1. Create EventBridge rule:
```bash
aws events put-rule \
  --name category-stats-daily-recalculation \
  --schedule-expression "cron(0 2 * * ? *)" \
  --description "Daily recalculation of category statistics"
```

2. Add Lambda as target:
```bash
aws events put-targets \
  --rule category-stats-daily-recalculation \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:category-stats-updater"
```

3. Grant EventBridge permission to invoke Lambda:
```bash
aws lambda add-permission \
  --function-name category-stats-updater \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:REGION:ACCOUNT:rule/category-stats-daily-recalculation
```

## Testing

### Test Stream Event

```python
import json

# Simulate DynamoDB Stream event
event = {
    "Records": [
        {
            "eventName": "INSERT",
            "dynamodb": {
                "NewImage": {
                    "PK": {"S": "USER#test_user"},
                    "SK": {"S": "TXN#txn_test123"},
                    "category": {"S": "Office Supplies"},
                    "date": {"S": "2024-01-15"},
                    "amount": {"N": "45.99"}
                }
            }
        }
    ]
}

# Invoke Lambda
response = lambda_client.invoke(
    FunctionName='category-stats-updater',
    InvocationType='Event',
    Payload=json.dumps(event)
)
```

### Test Scheduled Event

```python
# Simulate EventBridge scheduled event
event = {
    "source": "aws.events",
    "detail-type": "Scheduled Event",
    "time": "2024-01-15T02:00:00Z"
}

# Invoke Lambda
response = lambda_client.invoke(
    FunctionName='category-stats-updater',
    InvocationType='RequestResponse',
    Payload=json.dumps(event)
)
```

## Monitoring

**CloudWatch Metrics**:
- `Invocations`: Number of times function is invoked
- `Duration`: Execution time
- `Errors`: Number of failed invocations
- `IteratorAge`: Age of last record processed (for streams)

**CloudWatch Logs**:
- Log group: `/aws/lambda/category-stats-updater`
- Log statistics calculations and updates
- Log errors and warnings

**Custom Metrics** (optional):
- Number of categories processed
- Number of statistics updated
- Processing time per category

## Error Handling

The function includes comprehensive error handling:

1. **Stream Processing Errors**: Logged but don't fail the entire batch
2. **Calculation Errors**: Logged and skipped, statistics remain unchanged
3. **DynamoDB Errors**: Retried automatically by Lambda
4. **Scheduled Job Errors**: Logged with user_id for troubleshooting

## Performance Considerations

- **Batch Processing**: Stream events are processed in batches (up to 100 records)
- **Pagination**: Handles large result sets with DynamoDB pagination
- **Efficient Queries**: Uses GSI1 for category-based queries
- **Incremental Updates**: Stream handler only updates affected categories
- **Full Recalculation**: Scheduled job ensures eventual consistency

## Future Enhancements

1. **Parallel Processing**: Use Step Functions for parallel user processing in scheduled job
2. **Incremental Statistics**: Update statistics incrementally without full recalculation
3. **Historical Trends**: Track statistics changes over time
4. **Alerting**: Send notifications when statistics change significantly
5. **Caching**: Cache frequently accessed statistics in ElastiCache
