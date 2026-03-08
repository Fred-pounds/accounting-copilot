# CloudWatch Log Groups and Alarms

# Log groups for Lambda functions
resource "aws_cloudwatch_log_group" "document_upload_handler" {
  name              = "/aws/lambda/${var.project_name}-document-upload-handler"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "ocr_processor" {
  name              = "/aws/lambda/${var.project_name}-ocr-processor"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "transaction_classifier" {
  name              = "/aws/lambda/${var.project_name}-transaction-classifier"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "data_validator" {
  name              = "/aws/lambda/${var.project_name}-data-validator"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "reconciliation_engine" {
  name              = "/aws/lambda/${var.project_name}-reconciliation-engine"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "dashboard_api" {
  name              = "/aws/lambda/${var.project_name}-dashboard-api"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "financial_assistant" {
  name              = "/aws/lambda/${var.project_name}-financial-assistant"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "audit_logger" {
  name              = "/aws/lambda/${var.project_name}-audit-logger"
  retention_in_days = 90 # Longer retention for audit logs

  tags = local.common_tags
}

# Log group for Step Functions
resource "aws_cloudwatch_log_group" "step_functions" {
  name              = "/aws/vendedlogs/states/${var.project_name}-document-processing"
  retention_in_days = 30

  tags = local.common_tags
}

# CloudWatch Alarms

# Lambda error rate alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.project_name}-lambda-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda error rate exceeds 5%"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.pending_approvals.arn]

  tags = local.common_tags
}

# API Gateway 5xx errors alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  alarm_name          = "${var.project_name}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "API Gateway 5xx errors exceed 10 per minute"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = "${var.project_name}-api"
  }

  alarm_actions = [aws_sns_topic.pending_approvals.arn]

  tags = local.common_tags
}

# DynamoDB throttling alarm
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  alarm_name          = "${var.project_name}-dynamodb-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UserErrors"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "DynamoDB throttling detected"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = aws_dynamodb_table.main.name
  }

  alarm_actions = [aws_sns_topic.pending_approvals.arn]

  tags = local.common_tags
}

# Step Functions execution failures alarm
resource "aws_cloudwatch_metric_alarm" "step_functions_failures" {
  alarm_name          = "${var.project_name}-step-functions-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 3600
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Step Functions execution failures exceed 5 per hour"
  treat_missing_data  = "notBreaching"

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.document_processing.arn
  }

  alarm_actions = [aws_sns_topic.pending_approvals.arn]

  tags = local.common_tags
}

# Textract failure rate alarm
resource "aws_cloudwatch_metric_alarm" "textract_failures" {
  alarm_name          = "${var.project_name}-textract-failure-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UserErrorCount"
  namespace           = "AWS/Textract"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Textract failure rate exceeds 20%"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.pending_approvals.arn]

  tags = local.common_tags
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", { stat = "Sum", label = "Lambda Errors" }],
            [".", "Invocations", { stat = "Sum", label = "Lambda Invocations" }],
            [".", "Duration", { stat = "Average", label = "Avg Duration (ms)" }],
            [".", "Throttles", { stat = "Sum", label = "Lambda Throttles" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Lambda Metrics"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApiGateway", "5XXError", { stat = "Sum", label = "5XX Errors" }],
            [".", "4XXError", { stat = "Sum", label = "4XX Errors" }],
            [".", "Count", { stat = "Sum", label = "Total Requests" }],
            [".", "Latency", { stat = "Average", label = "Avg Latency (ms)" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "API Gateway Metrics"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", { stat = "Sum", label = "Read Capacity" }],
            [".", "ConsumedWriteCapacityUnits", { stat = "Sum", label = "Write Capacity" }],
            [".", "UserErrors", { stat = "Sum", label = "User Errors (Throttles)" }],
            [".", "SystemErrors", { stat = "Sum", label = "System Errors" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "DynamoDB Metrics"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/States", "ExecutionsStarted", { stat = "Sum", label = "Executions Started" }],
            [".", "ExecutionsSucceeded", { stat = "Sum", label = "Executions Succeeded" }],
            [".", "ExecutionsFailed", { stat = "Sum", label = "Executions Failed" }],
            [".", "ExecutionTime", { stat = "Average", label = "Avg Execution Time (ms)" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Step Functions Metrics"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Textract", "ResponseTime", { stat = "Average", label = "Avg Response Time (ms)" }],
            [".", "UserErrorCount", { stat = "Sum", label = "User Errors" }],
            [".", "ServerErrorCount", { stat = "Sum", label = "Server Errors" }],
            [".", "SuccessfulRequestCount", { stat = "Sum", label = "Successful Requests" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Textract Metrics"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      {
        type = "log"
        properties = {
          query   = "SOURCE '/aws/lambda/${var.project_name}-document-upload-handler' | SOURCE '/aws/lambda/${var.project_name}-ocr-processor' | SOURCE '/aws/lambda/${var.project_name}-transaction-classifier' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20"
          region  = var.aws_region
          title   = "Recent Errors"
          stacked = false
        }
      }
    ]
  })

  depends_on = [
    aws_cloudwatch_log_group.document_upload_handler,
    aws_cloudwatch_log_group.ocr_processor,
    aws_cloudwatch_log_group.transaction_classifier,
    aws_cloudwatch_log_group.data_validator,
    aws_cloudwatch_log_group.reconciliation_engine,
    aws_cloudwatch_log_group.dashboard_api,
    aws_cloudwatch_log_group.financial_assistant,
    aws_cloudwatch_log_group.audit_logger
  ]
}
