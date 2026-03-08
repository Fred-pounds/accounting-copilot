# Step Functions State Machine for Document Processing

resource "aws_sfn_state_machine" "document_processing" {
  name     = "${var.project_name}-document-processing"
  role_arn = aws_iam_role.step_functions.arn

  definition = jsonencode({
    Comment = "Process uploaded financial document"
    StartAt = "ExtractText"
    States = {
      ExtractText = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "${var.project_name}-ocr-processor"
          Payload = {
            "document_id.$" = "$.document_id"
            "s3_bucket.$"   = "$.s3_bucket"
            "s3_key.$"      = "$.s3_key"
            "user_id.$"     = "$.user_id"
          }
        }
        ResultPath = "$.ocr_result"
        Catch = [
          {
            ErrorEquals = ["OCRFailure", "States.TaskFailed"]
            Next        = "NotifyOCRFailure"
            ResultPath  = "$.error"
          }
        ]
        Next = "ClassifyTransaction"
      }

      ClassifyTransaction = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "${var.project_name}-transaction-classifier"
          Payload = {
            "document_id.$"      = "$.document_id"
            "user_id.$"          = "$.user_id"
            "extracted_data.$"   = "$.ocr_result.Payload"
          }
        }
        ResultPath = "$.classification_result"
        Retry = [
          {
            ErrorEquals     = ["States.TaskFailed"]
            IntervalSeconds = 2
            MaxAttempts     = 3
            BackoffRate     = 2.0
          }
        ]
        Next = "ValidateData"
      }

      ValidateData = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "${var.project_name}-data-validator"
          Payload = {
            "transaction_id.$" = "$.classification_result.Payload.transaction_id"
            "user_id.$"        = "$.user_id"
          }
        }
        ResultPath = "$.validation_result"
        Next       = "CheckConfidence"
      }

      CheckConfidence = {
        Type = "Choice"
        Choices = [
          {
            Variable      = "$.classification_result.Payload.confidence"
            NumericGreaterThanEquals = 0.7
            Next          = "ReconcileReceipts"
          }
        ]
        Default = "FlagForReview"
      }

      FlagForReview = {
        Type     = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = "AccountingCopilot"
          Key = {
            PK = {
              "S.$" = "States.Format('USER#{}', $.user_id)"
            }
            SK = {
              "S.$" = "States.Format('TXN#{}', $.classification_result.Payload.transaction_id)"
            }
          }
          UpdateExpression = "SET #status = :status, flagged_for_review = :flagged"
          ExpressionAttributeNames = {
            "#status" = "status"
          }
          ExpressionAttributeValues = {
            ":status" = {
              S = "pending_review"
            }
            ":flagged" = {
              BOOL = true
            }
          }
        }
        ResultPath = "$.flag_result"
        Next       = "NotifyPendingApproval"
      }

      NotifyPendingApproval = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn = aws_sns_topic.pending_approvals.arn
          Message = {
            "default.$" = "States.Format('Transaction {} requires review. Confidence: {}', $.classification_result.Payload.transaction_id, $.classification_result.Payload.confidence)"
          }
          Subject = "Transaction Pending Review"
        }
        ResultPath = "$.notification_result"
        Next       = "ReconcileReceipts"
      }

      ReconcileReceipts = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "${var.project_name}-reconciliation-engine"
          Payload = {
            "transaction_id.$" = "$.classification_result.Payload.transaction_id"
            "user_id.$"        = "$.user_id"
          }
        }
        ResultPath = "$.reconciliation_result"
        Next       = "LogAuditTrail"
      }

      LogAuditTrail = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "${var.project_name}-audit-logger"
          Payload = {
            "user_id.$"        = "$.user_id"
            "action_type"      = "document_processing"
            "document_id.$"    = "$.document_id"
            "transaction_id.$" = "$.classification_result.Payload.transaction_id"
            "workflow_result" = {
              "ocr_status.$"            = "$.ocr_result.Payload.status"
              "classification.$"        = "$.classification_result.Payload"
              "validation.$"            = "$.validation_result.Payload"
              "reconciliation.$"        = "$.reconciliation_result.Payload"
            }
          }
        }
        ResultPath = "$.audit_result"
        End        = true
      }

      NotifyOCRFailure = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn = aws_sns_topic.ocr_failures.arn
          Message = {
            "default.$" = "States.Format('OCR processing failed for document {}. Manual entry required.', $.document_id)"
          }
          Subject = "OCR Processing Failed"
        }
        End = true
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_functions.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tracing_configuration {
    enabled = true
  }

  tags = local.common_tags
}
