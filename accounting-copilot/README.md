# AI Accounting Copilot

[![Run Tests](https://github.com/Fred-pounds/accounting-copilot/actions/workflows/test.yml/badge.svg)](https://github.com/Fred-pounds/accounting-copilot/actions/workflows/test.yml)
[![Deploy to Staging](https://github.com/Fred-pounds/accounting-copilot/actions/workflows/deploy-staging.yml/badge.svg)](https://github.com/Fred-pounds/accounting-copilot/actions/workflows/deploy-staging.yml)

An AI-powered financial management system for small and medium enterprises (SMEs) built on AWS serverless architecture.

## Overview

The AI Accounting Copilot automates daily financial activity capture, provides intelligent transaction classification, validates financial data, and delivers plain-language insights to support business decisions.

## Architecture

- **Frontend**: React SPA hosted on S3 + CloudFront
- **Authentication**: Amazon Cognito
- **API**: API Gateway with REST endpoints
- **Compute**: AWS Lambda (Python 3.11)
- **AI/ML**: Amazon Textract (OCR) + Amazon Bedrock (Classification & Assistant)
- **Data**: DynamoDB (single-table design) + S3 (document storage)
- **Orchestration**: AWS Step Functions
- **Notifications**: Amazon SNS
- **Monitoring**: CloudWatch Logs, Metrics, and Alarms

## Project Structure

```
.
├── infrastructure/          # Terraform infrastructure as code
│   ├── main.tf             # Main configuration
│   ├── variables.tf        # Input variables
│   ├── outputs.tf          # Output values
│   ├── s3.tf               # S3 buckets
│   ├── dynamodb.tf         # DynamoDB table
│   ├── cognito.tf          # Cognito user pool
│   ├── api_gateway.tf      # API Gateway
│   ├── iam.tf              # IAM roles and policies
│   ├── sns.tf              # SNS topics
│   ├── cloudwatch.tf       # CloudWatch logs and alarms
│   └── step_functions.tf   # Step Functions state machine
│
├── src/
│   ├── shared/             # Shared utilities and libraries
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration management
│   │   ├── exceptions.py   # Custom exceptions
│   │   ├── response.py     # HTTP response utilities
│   │   ├── aws_clients.py  # AWS service clients
│   │   ├── models.py       # Data models
│   │   ├── auth.py         # Authentication utilities
│   │   └── logger.py       # Logging utilities
│   │
│   └── lambdas/            # Lambda function handlers
│       ├── document_upload_handler/
│       ├── ocr_processor/
│       ├── transaction_classifier/
│       ├── data_validator/
│       ├── reconciliation_engine/
│       ├── dashboard_api/
│       ├── financial_assistant/
│       └── audit_logger/
│
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── properties/        # Property-based tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Shared test fixtures
│
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Prerequisites

- AWS Account
- Terraform >= 1.0
- Python 3.11
- AWS CLI configured with appropriate credentials

## Setup

### CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

- **Automated Testing**: Tests run on every pull request
- **Staging Deployment**: Auto-deploys to staging when merged to `main`
- **Production Deployment**: Manual deployment with approval required

See [.github/SETUP_GUIDE.md](.github/SETUP_GUIDE.md) for CI/CD configuration details.

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Terraform Variables

Create a `terraform.tfvars` file in the `infrastructure/` directory:

```hcl
aws_region   = "us-east-1"
environment  = "dev"
project_name = "accounting-copilot"
```

### 3. Deploy Infrastructure

```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

### 4. Deploy Lambda Functions

After infrastructure is deployed, package and deploy Lambda functions:

```bash
# TODO: Add deployment script
```

### 5. Configure Environment Variables

Set the following environment variables for Lambda functions (automatically set by Terraform):

- `DYNAMODB_TABLE`: DynamoDB table name
- `DOCUMENTS_BUCKET`: S3 documents bucket name
- `WORKFLOW_ARN`: Step Functions state machine ARN
- `SNS_PENDING_APPROVALS`: SNS topic ARN for pending approvals
- `SNS_OCR_FAILURES`: SNS topic ARN for OCR failures
- `SNS_UNMATCHED_TRANSACTIONS`: SNS topic ARN for unmatched transactions
- `SNS_APPROVAL_REMINDERS`: SNS topic ARN for approval reminders
- `COGNITO_USER_POOL_ID`: Cognito user pool ID
- `COGNITO_CLIENT_ID`: Cognito client ID
- `AWS_REGION`: AWS region

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run property-based tests
pytest tests/properties/

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/
pylint src/

# Type checking
mypy src/
```

## Cost Estimation

**Monthly costs for typical SME usage (100-200 documents/month):**

- AWS Free Tier services: $0
- Amazon Textract: $0.15 - $0.30
- Amazon Bedrock: $2 - $5
- AWS Step Functions: $0.01

**Total: $2.16 - $5.31/month**

## Security

- All data encrypted at rest (AES-256)
- All data encrypted in transit (TLS 1.3)
- Authentication via Cognito JWT tokens
- Fine-grained IAM permissions
- Comprehensive audit trail

## Monitoring

CloudWatch dashboards and alarms are configured for:

- Lambda error rates
- API Gateway 5xx errors
- DynamoDB throttling
- Step Functions execution failures
- Textract failure rates

## License

[Add your license here]

## Support

[Add support information here]
