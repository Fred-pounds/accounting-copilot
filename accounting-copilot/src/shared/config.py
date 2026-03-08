"""
Configuration management for Lambda functions.
"""

import os
from typing import Optional


class Config:
    """Application configuration from environment variables."""
    
    # AWS Resources
    DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "AccountingCopilot")
    DOCUMENTS_BUCKET: str = os.getenv("DOCUMENTS_BUCKET", "")
    WEBSITE_BUCKET: str = os.getenv("WEBSITE_BUCKET", "")
    
    # Step Functions
    WORKFLOW_ARN: str = os.getenv("WORKFLOW_ARN", "")
    
    # SNS Topics
    SNS_PENDING_APPROVALS: str = os.getenv("SNS_PENDING_APPROVALS", "")
    SNS_OCR_FAILURES: str = os.getenv("SNS_OCR_FAILURES", "")
    SNS_UNMATCHED_TRANSACTIONS: str = os.getenv("SNS_UNMATCHED_TRANSACTIONS", "")
    SNS_APPROVAL_REMINDERS: str = os.getenv("SNS_APPROVAL_REMINDERS", "")
    
    # Cognito
    COGNITO_USER_POOL_ID: str = os.getenv("COGNITO_USER_POOL_ID", "")
    COGNITO_CLIENT_ID: str = os.getenv("COGNITO_CLIENT_ID", "")
    
    # AWS Region (automatically set by Lambda runtime)
    AWS_REGION: str = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    
    # Bedrock
    BEDROCK_MODEL_ID: str = os.getenv(
        "BEDROCK_MODEL_ID",
        "anthropic.claude-3-haiku-20240307-v1:0"
    )
    
    # Application Settings
    CLASSIFICATION_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.7")
    )
    RECONCILIATION_HIGH_CONFIDENCE: float = float(
        os.getenv("RECONCILIATION_HIGH_CONFIDENCE", "0.8")
    )
    RECONCILIATION_MEDIUM_CONFIDENCE: float = float(
        os.getenv("RECONCILIATION_MEDIUM_CONFIDENCE", "0.5")
    )
    OUTLIER_STD_DEVIATION: float = float(
        os.getenv("OUTLIER_STD_DEVIATION", "3.0")
    )
    UNMATCHED_TRANSACTION_DAYS: int = int(
        os.getenv("UNMATCHED_TRANSACTION_DAYS", "7")
    )
    APPROVAL_REMINDER_HOURS: int = int(
        os.getenv("APPROVAL_REMINDER_HOURS", "48")
    )
    LARGE_TRANSACTION_THRESHOLD: float = float(
        os.getenv("LARGE_TRANSACTION_THRESHOLD", "0.1")  # 10% of average
    )
    
    # Performance Settings
    MAX_DOCUMENT_SIZE_MB: int = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "10"))
    OCR_TIMEOUT_SECONDS: int = int(os.getenv("OCR_TIMEOUT_SECONDS", "60"))
    CLASSIFICATION_TIMEOUT_SECONDS: int = int(
        os.getenv("CLASSIFICATION_TIMEOUT_SECONDS", "10")
    )
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values are set."""
        required = [
            "DYNAMODB_TABLE",
            "DOCUMENTS_BUCKET",
            "AWS_REGION",
        ]
        
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")


# Validate configuration on import
Config.validate()
