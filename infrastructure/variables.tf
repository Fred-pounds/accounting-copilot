# Variables for AI Accounting Copilot Infrastructure

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "accounting-copilot"
}

variable "lambda_runtime" {
  description = "Lambda runtime version"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Default Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "api_rate_limit" {
  description = "API Gateway rate limit per user (requests per minute)"
  type        = number
  default     = 100
}

variable "session_timeout_minutes" {
  description = "Cognito session timeout in minutes"
  type        = number
  default     = 15
}

variable "document_retention_days" {
  description = "Number of days to retain documents before archiving"
  type        = number
  default     = 365
}

variable "document_expiration_days" {
  description = "Number of days to retain documents before deletion (7 years for compliance)"
  type        = number
  default     = 2555
}
