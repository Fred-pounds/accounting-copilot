# API Gateway REST API

resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-api"
  description = "AI Accounting Copilot REST API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.common_tags
}

# Cognito Authorizer
resource "aws_api_gateway_authorizer" "cognito" {
  name          = "${var.project_name}-cognito-authorizer"
  rest_api_id   = aws_api_gateway_rest_api.main.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = [aws_cognito_user_pool.main.arn]
}

# API Gateway Account (for CloudWatch logging)
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.dashboard.id,
      aws_api_gateway_resource.transactions.id,
      aws_api_gateway_resource.documents.id,
      aws_api_gateway_resource.audit.id,
      aws_api_gateway_resource.approvals.id,
      aws_api_gateway_resource.assistant.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.dashboard_summary,
    aws_api_gateway_integration.transactions_get,
    aws_api_gateway_integration.transactions_post,
    aws_api_gateway_integration.documents_get,
    aws_api_gateway_integration.documents_post,
    aws_api_gateway_integration.audit_get,
    aws_api_gateway_integration.approvals_get,
    aws_api_gateway_integration.approvals_post,
    aws_api_gateway_integration.assistant_post,
    aws_api_gateway_integration_response.cors_options,
  ]
}

# API Gateway Stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  xray_tracing_enabled = true

  tags = local.common_tags
}

# CloudWatch log group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}"
  retention_in_days = 30

  tags = local.common_tags
}

# API Gateway Method Settings - commented out until stage is created
# Uncomment after Lambda integrations are added
# resource "aws_api_gateway_method_settings" "main" {
#   rest_api_id = aws_api_gateway_rest_api.main.id
#   stage_name  = aws_api_gateway_stage.main.stage_name
#   method_path = "*/*"
#
#   settings {
#     metrics_enabled        = true
#     logging_level          = "INFO"
#     data_trace_enabled     = true
#     throttling_burst_limit = 200
#     throttling_rate_limit  = var.api_rate_limit
#     caching_enabled        = false # Enable per-method as needed
#   }
# }

# CORS configuration
resource "aws_api_gateway_gateway_response" "cors_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  response_type = "DEFAULT_4XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT,DELETE'"
  }
}

resource "aws_api_gateway_gateway_response" "cors_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  response_type = "DEFAULT_5XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT,DELETE'"
  }
}

# Usage Plan - commented out until stage is created
# Uncomment after Lambda integrations are added
# resource "aws_api_gateway_usage_plan" "main" {
#   name        = "${var.project_name}-usage-plan"
#   description = "Usage plan for AI Accounting Copilot API"
#
#   api_stages {
#     api_id = aws_api_gateway_rest_api.main.id
#     stage  = aws_api_gateway_stage.main.stage_name
#   }
#
#   quota_settings {
#     limit  = 10000
#     period = "DAY"
#   }
#
#   throttle_settings {
#     burst_limit = 200
#     rate_limit  = var.api_rate_limit
#   }
#
#   tags = local.common_tags
# }

# API Key (optional - for additional rate limiting per user)
resource "aws_api_gateway_api_key" "main" {
  name    = "${var.project_name}-api-key"
  enabled = true

  tags = local.common_tags
}

# Commented out until usage plan is created
# resource "aws_api_gateway_usage_plan_key" "main" {
#   key_id        = aws_api_gateway_api_key.main.id
#   key_type      = "API_KEY"
#   usage_plan_id = aws_api_gateway_usage_plan.main.id
# }
