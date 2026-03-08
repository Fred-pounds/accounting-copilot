"""
AWS service clients with proper configuration.
"""

import boto3
from botocore.config import Config as BotoConfig
from .config import Config


# Configure boto3 with retries and timeouts
boto_config = BotoConfig(
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'
    },
    connect_timeout=5,
    read_timeout=60
)


# DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=Config.AWS_REGION, config=boto_config)
dynamodb_client = boto3.client('dynamodb', region_name=Config.AWS_REGION, config=boto_config)

# S3
s3_client = boto3.client('s3', region_name=Config.AWS_REGION, config=boto_config)

# Textract
textract_client = boto3.client('textract', region_name=Config.AWS_REGION, config=boto_config)

# Bedrock Runtime
bedrock_runtime = boto3.client(
    'bedrock-runtime',
    region_name=Config.AWS_REGION,
    config=boto_config
)

# SNS
sns_client = boto3.client('sns', region_name=Config.AWS_REGION, config=boto_config)

# Step Functions
sfn_client = boto3.client('stepfunctions', region_name=Config.AWS_REGION, config=boto_config)

# CloudWatch Logs
logs_client = boto3.client('logs', region_name=Config.AWS_REGION, config=boto_config)


def get_dynamodb_table():
    """Get the main DynamoDB table."""
    return dynamodb.Table(Config.DYNAMODB_TABLE)


def get_sns_client():
    """Get SNS client."""
    return sns_client

