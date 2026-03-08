"""
Shared test fixtures and configuration.
"""

import pytest
import boto3
import os
from moto import mock_aws
from unittest.mock import Mock, patch


# Set required environment variables for testing
os.environ.setdefault('DYNAMODB_TABLE', 'AccountingCopilot')
os.environ.setdefault('DOCUMENTS_BUCKET', 'test-documents-bucket')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('SNS_OCR_FAILURES', 'arn:aws:sns:us-east-1:123456789012:ocr-failures')
os.environ.setdefault('SNS_PENDING_APPROVALS', 'arn:aws:sns:us-east-1:123456789012:pending-approvals')


@pytest.fixture
def mock_aws_services():
    """Mock AWS services for testing."""
    with mock_aws():
        yield


@pytest.fixture
def dynamodb_table(mock_aws_services):
    """Create a mock DynamoDB table."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    table = dynamodb.create_table(
        TableName='AccountingCopilot',
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI2PK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI2SK', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'GSI2',
                'KeySchema': [
                    {'AttributeName': 'GSI2PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'GSI2SK', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    return table


@pytest.fixture
def s3_bucket(mock_aws_services):
    """Create a mock S3 bucket."""
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'test-documents-bucket'
    s3.create_bucket(Bucket=bucket_name)
    return bucket_name


@pytest.fixture
def mock_textract():
    """Mock Textract client."""
    with patch('boto3.client') as mock:
        textract = Mock()
        textract.detect_document_text.return_value = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'Office Depot'},
                {'BlockType': 'LINE', 'Text': 'Date: 01/15/2024'},
                {'BlockType': 'LINE', 'Text': 'Total: $45.99'}
            ]
        }
        mock.return_value = textract
        yield textract


@pytest.fixture
def mock_bedrock():
    """Mock Bedrock client."""
    with patch('boto3.client') as mock:
        bedrock = Mock()
        bedrock.invoke_model.return_value = {
            'body': Mock(read=lambda: b'{"content": [{"text": "{\\"category\\": \\"Office Supplies\\", \\"confidence\\": 0.92, \\"reasoning\\": \\"Vendor indicates office supplies\\", \\"transaction_type\\": \\"expense\\"}"}]}')
        }
        mock.return_value = bedrock
        yield bedrock


@pytest.fixture
def sample_transaction():
    """Sample transaction for testing."""
    return {
        'PK': 'USER#test-user',
        'SK': 'TXN#txn_123',
        'entity_type': 'transaction',
        'transaction_id': 'txn_123',
        'date': '2024-01-15',
        'amount': 45.99,
        'currency': 'USD',
        'type': 'expense',
        'category': 'Office Supplies',
        'vendor': 'Office Depot',
        'description': 'Office supplies purchase',
        'classification_confidence': 0.92,
        'status': 'approved',
        'created_at': '2024-01-15T10:00:00Z'
    }


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        'PK': 'USER#test-user',
        'SK': 'DOC#doc_123',
        'entity_type': 'document',
        'document_id': 'doc_123',
        's3_key': 'documents/test-user/receipts/2024/01/doc_123.jpg',
        's3_bucket': 'test-bucket',
        'upload_timestamp': '2024-01-15T10:00:00Z',
        'document_type': 'receipt',
        'ocr_status': 'completed'
    }
