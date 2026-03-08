# Terraform Outputs

output "documents_bucket_name" {
  description = "Name of the S3 bucket for documents"
  value       = aws_s3_bucket.documents.id
}

output "website_bucket_name" {
  description = "Name of the S3 bucket for static website"
  value       = aws_s3_bucket.website.id
}

output "website_url" {
  description = "URL of the static website"
  value       = "http://${aws_s3_bucket.website.bucket}.s3-website-${local.region}.amazonaws.com"
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.main.name
}

output "cognito_user_pool_id" {
  description = "ID of the Cognito user pool"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito user pool client"
  value       = aws_cognito_user_pool_client.web.id
}

output "cognito_domain" {
  description = "Cognito user pool domain"
  value       = aws_cognito_user_pool_domain.main.domain
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.main.id
}

output "step_functions_arn" {
  description = "ARN of the Step Functions state machine"
  value       = aws_sfn_state_machine.document_processing.arn
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "sns_topic_arns" {
  description = "ARNs of SNS topics"
  value = {
    pending_approvals       = aws_sns_topic.pending_approvals.arn
    ocr_failures            = aws_sns_topic.ocr_failures.arn
    unmatched_transactions  = aws_sns_topic.unmatched_transactions.arn
    approval_reminders      = aws_sns_topic.approval_reminders.arn
  }
}

output "region" {
  description = "AWS region"
  value       = local.region
}

output "account_id" {
  description = "AWS account ID"
  value       = local.account_id
}
