# Lambda Functions Configuration with X-Ray Tracing
# Note: IAM role and policies are defined in iam.tf

# Lambda function: Document Upload Handler
resource "aws_lambda_function" "document_upload_handler" {
  function_name = "${var.project_name}-document-upload-handler"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 512

  # Placeholder for deployment package
  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE      = aws_dynamodb_table.main.name
      DOCUMENTS_BUCKET    = aws_s3_bucket.documents.id
      WORKFLOW_ARN        = aws_sfn_state_machine.document_processing.arn
      XRAY_ENABLED        = "true"
      LOG_LEVEL           = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: OCR Processor
resource "aws_lambda_function" "ocr_processor" {
  function_name = "${var.project_name}-ocr-processor"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 1024

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE      = aws_dynamodb_table.main.name
      SNS_OCR_FAILURES    = aws_sns_topic.ocr_failures.arn
      XRAY_ENABLED        = "true"
      LOG_LEVEL           = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Transaction Classifier
resource "aws_lambda_function" "transaction_classifier" {
  function_name = "${var.project_name}-transaction-classifier"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 10
  memory_size   = 512

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE                      = aws_dynamodb_table.main.name
      BEDROCK_MODEL_ID                    = "anthropic.claude-3-haiku-20240307-v1:0"
      CLASSIFICATION_CONFIDENCE_THRESHOLD = "0.7"
      XRAY_ENABLED                        = "true"
      LOG_LEVEL                           = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Data Validator
resource "aws_lambda_function" "data_validator" {
  function_name = "${var.project_name}-data-validator"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 10
  memory_size   = 512

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE           = aws_dynamodb_table.main.name
      SNS_PENDING_APPROVALS    = aws_sns_topic.pending_approvals.arn
      OUTLIER_STD_DEVIATION    = "3"
      XRAY_ENABLED             = "true"
      LOG_LEVEL                = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Reconciliation Engine
resource "aws_lambda_function" "reconciliation_engine" {
  function_name = "${var.project_name}-reconciliation-engine"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 512

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE                  = aws_dynamodb_table.main.name
      UNMATCHED_TRANSACTIONS_TOPIC_ARN = aws_sns_topic.unmatched_transactions.arn
      XRAY_ENABLED                    = "true"
      LOG_LEVEL                       = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Dashboard API
resource "aws_lambda_function" "dashboard_api" {
  function_name = "${var.project_name}-dashboard-api"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 5
  memory_size   = 256

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.main.name
      XRAY_ENABLED   = "true"
      LOG_LEVEL      = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Financial Assistant
resource "aws_lambda_function" "financial_assistant" {
  function_name = "${var.project_name}-financial-assistant"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 1024

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE   = aws_dynamodb_table.main.name
      BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
      XRAY_ENABLED     = "true"
      LOG_LEVEL        = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Audit Logger
resource "aws_lambda_function" "audit_logger" {
  function_name = "${var.project_name}-audit-logger"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 5
  memory_size   = 256

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.main.name
      XRAY_ENABLED   = "true"
      LOG_LEVEL      = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Transaction API
resource "aws_lambda_function" "transaction_api" {
  function_name = "${var.project_name}-transaction-api"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 10
  memory_size   = 512

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.main.name
      XRAY_ENABLED   = "true"
      LOG_LEVEL      = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Document API
resource "aws_lambda_function" "document_api" {
  function_name = "${var.project_name}-document-api"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 10
  memory_size   = 512

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE   = aws_dynamodb_table.main.name
      DOCUMENTS_BUCKET = aws_s3_bucket.documents.id
      XRAY_ENABLED     = "true"
      LOG_LEVEL        = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Audit Trail API
resource "aws_lambda_function" "audit_trail_api" {
  function_name = "${var.project_name}-audit-trail-api"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 10
  memory_size   = 512

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.main.name
      XRAY_ENABLED   = "true"
      LOG_LEVEL      = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Lambda function: Approval Manager
resource "aws_lambda_function" "approval_manager" {
  function_name = "${var.project_name}-approval-manager"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 10
  memory_size   = 512

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE        = aws_dynamodb_table.main.name
      SNS_PENDING_APPROVALS = aws_sns_topic.pending_approvals.arn
      XRAY_ENABLED          = "true"
      LOG_LEVEL             = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

# Workflow Trigger Lambda (triggered by S3 events)
resource "aws_lambda_function" "workflow_trigger" {
  function_name = "${var.project_name}-workflow-trigger"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = 60
  memory_size   = 256

  s3_bucket = aws_s3_bucket.documents.id
  s3_key    = "lambda-packages/workflow_trigger.zip"

  environment {
    variables = {
      WORKFLOW_ARN = aws_sfn_state_machine.document_processing.arn
      LOG_LEVEL    = var.log_level
    }
  }

  tracing_config {
    mode = "Active"
  }
}

# Permission for S3 to invoke workflow trigger Lambda
resource "aws_lambda_permission" "allow_s3_invoke_workflow_trigger" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.workflow_trigger.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.documents.arn
}
