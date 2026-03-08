"""
Unit tests for Document API Lambda function.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError

# Mock the shared modules before importing handler
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'lambdas' / 'document_api'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


@pytest.fixture
def mock_context():
    """Mock Lambda context."""
    context = Mock()
    context.request_id = 'test-request-id-123'
    context.function_name = 'document-api'
    context.memory_limit_in_mb = 512
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:document-api'
    return context


@pytest.fixture
def mock_document():
    """Mock document object."""
    from shared.models import Document, generate_user_pk, generate_document_sk
    
    return Document(
        PK=generate_user_pk('user123'),
        SK=generate_document_sk('doc_abc123'),
        document_id='doc_abc123',
        s3_key='documents/user123/receipts/2024/01/doc_abc123.jpg',
        s3_bucket='accounting-copilot-documents',
        upload_timestamp='2024-01-15T10:30:00Z',
        document_type='receipt',
        ocr_status='completed',
        extracted_text='Office Depot\nDate: 01/15/2024\nTotal: $45.99',
        parsed_fields={
            'date': '2024-01-15',
            'amount': 45.99,
            'vendor': 'Office Depot'
        },
        processing_duration_ms=3450
    )


@pytest.fixture
def api_gateway_event_get():
    """Mock API Gateway event for GET /documents/{id}."""
    return {
        'httpMethod': 'GET',
        'path': '/documents/doc_abc123',
        'pathParameters': {
            'id': 'doc_abc123'
        },
        'headers': {
            'Authorization': 'Bearer mock-token-123'
        },
        'requestContext': {
            'requestId': 'test-request-id',
            'identity': {
                'sourceIp': '127.0.0.1'
            }
        }
    }


@pytest.fixture
def api_gateway_event_list():
    """Mock API Gateway event for GET /documents."""
    return {
        'httpMethod': 'GET',
        'path': '/documents',
        'queryStringParameters': {
            'limit': '10'
        },
        'headers': {
            'Authorization': 'Bearer mock-token-123'
        },
        'requestContext': {
            'requestId': 'test-request-id',
            'identity': {
                'sourceIp': '127.0.0.1'
            }
        }
    }


class TestDocumentAPIGet:
    """Tests for GET /documents/{id} endpoint."""
    
    @patch('handler.get_repository')
    @patch('handler.extract_token_from_event')
    @patch('handler.get_user_id_from_token')
    @patch('handler.s3_client')
    def test_get_document_success(self, mock_s3, mock_get_user, mock_extract_token,
                                  mock_get_repo, api_gateway_event_get, mock_context, mock_document):
        """Test successful document retrieval with pre-signed URL."""
        from handler import lambda_handler_get
        
        # Setup mocks
        mock_extract_token.return_value = 'mock-token-123'
        mock_get_user.return_value = 'user123'
        
        mock_repo = Mock()
        mock_repo.get_document.return_value = mock_document
        mock_get_repo.return_value = mock_repo
        
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/presigned-url'
        
        # Execute
        response = lambda_handler_get(api_gateway_event_get, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['document_id'] == 'doc_abc123'
        assert body['s3_bucket'] == 'accounting-copilot-documents'
        assert body['download_url'] == 'https://s3.amazonaws.com/presigned-url'
        assert body['ocr_status'] == 'completed'
        
        # Verify S3 pre-signed URL was generated correctly
        mock_s3.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={
                'Bucket': 'accounting-copilot-documents',
                'Key': 'documents/user123/receipts/2024/01/doc_abc123.jpg'
            },
            ExpiresIn=300
        )
    
    @patch('handler.get_repository')
    @patch('handler.extract_token_from_event')
    @patch('handler.get_user_id_from_token')
    def test_get_document_not_found(self, mock_get_user, mock_extract_token,
                                   mock_get_repo, api_gateway_event_get, mock_context):
        """Test document not found error."""
        from handler import lambda_handler_get
        
        # Setup mocks
        mock_extract_token.return_value = 'mock-token-123'
        mock_get_user.return_value = 'user123'
        
        mock_repo = Mock()
        mock_repo.get_document.return_value = None
        mock_get_repo.return_value = mock_repo
        
        # Execute
        response = lambda_handler_get(api_gateway_event_get, mock_context)
        
        # Verify
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'not found' in body['error']['message'].lower()
    
    @patch('handler.get_repository')
    @patch('handler.extract_token_from_event')
    @patch('handler.get_user_id_from_token')
    def test_get_document_missing_id(self, mock_get_user, mock_extract_token,
                                    mock_get_repo, mock_context):
        """Test missing document ID error."""
        from handler import lambda_handler_get
        
        # Setup mocks
        mock_extract_token.return_value = 'mock-token-123'
        mock_get_user.return_value = 'user123'
        
        # Event without document ID
        event = {
            'httpMethod': 'GET',
            'path': '/documents/',
            'pathParameters': {},
            'headers': {'Authorization': 'Bearer mock-token-123'}
        }
        
        # Execute
        response = lambda_handler_get(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'required' in body['error']['message'].lower()
    
    @patch('handler.get_repository')
    @patch('handler.extract_token_from_event')
    @patch('handler.get_user_id_from_token')
    @patch('handler.s3_client')
    def test_get_document_s3_error(self, mock_s3, mock_get_user, mock_extract_token,
                                  mock_get_repo, api_gateway_event_get, mock_context, mock_document):
        """Test S3 pre-signed URL generation error."""
        from handler import lambda_handler_get
        
        # Setup mocks
        mock_extract_token.return_value = 'mock-token-123'
        mock_get_user.return_value = 'user123'
        
        mock_repo = Mock()
        mock_repo.get_document.return_value = mock_document
        mock_get_repo.return_value = mock_repo
        
        # Simulate S3 error
        mock_s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
            'generate_presigned_url'
        )
        
        # Execute
        response = lambda_handler_get(api_gateway_event_get, mock_context)
        
        # Verify - should still return 200 but with error message in download_url_error
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['document_id'] == 'doc_abc123'
        assert 'download_url_error' in body
        assert 'download_url' not in body
    
    @patch('handler.extract_token_from_event')
    def test_get_document_authentication_error(self, mock_extract_token, api_gateway_event_get, mock_context):
        """Test authentication error."""
        from handler import lambda_handler_get
        from shared.exceptions import AuthenticationError
        
        # Setup mock to raise authentication error
        mock_extract_token.side_effect = AuthenticationError("Invalid token")
        
        # Execute
        response = lambda_handler_get(api_gateway_event_get, mock_context)
        
        # Verify
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert 'error' in body


class TestDocumentAPIList:
    """Tests for GET /documents endpoint."""
    
    @patch('handler.get_repository')
    @patch('handler.extract_token_from_event')
    @patch('handler.get_user_id_from_token')
    def test_list_documents_success(self, mock_get_user, mock_extract_token,
                                   mock_get_repo, api_gateway_event_list, mock_context):
        """Test successful document listing."""
        from handler import lambda_handler_list
        from shared.models import Document, generate_user_pk, generate_document_sk
        
        # Setup mocks
        mock_extract_token.return_value = 'mock-token-123'
        mock_get_user.return_value = 'user123'
        
        # Create mock documents
        mock_docs = [
            Document(
                PK=generate_user_pk('user123'),
                SK=generate_document_sk(f'doc_{i}'),
                document_id=f'doc_{i}',
                s3_key=f'documents/user123/doc_{i}.jpg',
                s3_bucket='accounting-copilot-documents',
                upload_timestamp=f'2024-01-{15+i:02d}T10:30:00Z',
                document_type='receipt',
                ocr_status='completed'
            )
            for i in range(3)
        ]
        
        mock_repo = Mock()
        mock_repo.list_documents.return_value = mock_docs
        mock_get_repo.return_value = mock_repo
        
        # Execute
        response = lambda_handler_list(api_gateway_event_list, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'documents' in body
        assert 'count' in body
        assert body['count'] == 3
        assert len(body['documents']) == 3
        assert body['documents'][0]['document_id'] == 'doc_0'
        
        # Verify repository was called with correct limit
        mock_repo.list_documents.assert_called_once_with('user123', 10)
    
    @patch('handler.get_repository')
    @patch('handler.extract_token_from_event')
    @patch('handler.get_user_id_from_token')
    def test_list_documents_default_limit(self, mock_get_user, mock_extract_token,
                                         mock_get_repo, mock_context):
        """Test document listing with default limit."""
        from handler import lambda_handler_list
        
        # Setup mocks
        mock_extract_token.return_value = 'mock-token-123'
        mock_get_user.return_value = 'user123'
        
        mock_repo = Mock()
        mock_repo.list_documents.return_value = []
        mock_get_repo.return_value = mock_repo
        
        # Event without limit parameter
        event = {
            'httpMethod': 'GET',
            'path': '/documents',
            'headers': {'Authorization': 'Bearer mock-token-123'}
        }
        
        # Execute
        response = lambda_handler_list(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 0
        
        # Verify default limit of 50 was used
        mock_repo.list_documents.assert_called_once_with('user123', 50)
    
    @patch('handler.get_repository')
    @patch('handler.extract_token_from_event')
    @patch('handler.get_user_id_from_token')
    def test_list_documents_invalid_limit(self, mock_get_user, mock_extract_token,
                                         mock_get_repo, mock_context):
        """Test document listing with invalid limit."""
        from handler import lambda_handler_list
        
        # Setup mocks
        mock_extract_token.return_value = 'mock-token-123'
        mock_get_user.return_value = 'user123'
        
        # Event with invalid limit (too high)
        event = {
            'httpMethod': 'GET',
            'path': '/documents',
            'queryStringParameters': {'limit': '200'},
            'headers': {'Authorization': 'Bearer mock-token-123'}
        }
        
        # Execute
        response = lambda_handler_list(event, mock_context)
        
        # Verify
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'between 1 and 100' in body['error']['message'].lower()
    
    @patch('handler.get_repository')
    @patch('handler.extract_token_from_event')
    @patch('handler.get_user_id_from_token')
    def test_list_documents_empty_result(self, mock_get_user, mock_extract_token,
                                        mock_get_repo, api_gateway_event_list, mock_context):
        """Test document listing with no documents."""
        from handler import lambda_handler_list
        
        # Setup mocks
        mock_extract_token.return_value = 'mock-token-123'
        mock_get_user.return_value = 'user123'
        
        mock_repo = Mock()
        mock_repo.list_documents.return_value = []
        mock_get_repo.return_value = mock_repo
        
        # Execute
        response = lambda_handler_list(api_gateway_event_list, mock_context)
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 0
        assert body['documents'] == []
    
    @patch('handler.extract_token_from_event')
    def test_list_documents_authentication_error(self, mock_extract_token, api_gateway_event_list, mock_context):
        """Test authentication error."""
        from handler import lambda_handler_list
        from shared.exceptions import AuthenticationError
        
        # Setup mock to raise authentication error
        mock_extract_token.side_effect = AuthenticationError("Invalid token")
        
        # Execute
        response = lambda_handler_list(api_gateway_event_list, mock_context)
        
        # Verify
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert 'error' in body


class TestPresignedURLGeneration:
    """Tests for pre-signed URL generation."""
    
    @patch('handler.s3_client')
    def test_generate_presigned_url_success(self, mock_s3):
        """Test successful pre-signed URL generation."""
        from handler import generate_presigned_download_url
        
        # Setup mock
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/presigned-url'
        
        # Execute
        url = generate_presigned_download_url('test-bucket', 'test-key', 300)
        
        # Verify
        assert url == 'https://s3.amazonaws.com/presigned-url'
        mock_s3.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': 'test-bucket', 'Key': 'test-key'},
            ExpiresIn=300
        )
    
    @patch('handler.s3_client')
    def test_generate_presigned_url_error(self, mock_s3):
        """Test pre-signed URL generation error."""
        from handler import generate_presigned_download_url
        from shared.exceptions import AppError
        
        # Setup mock to raise error
        mock_s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
            'generate_presigned_url'
        )
        
        # Execute and verify
        with pytest.raises(AppError) as exc_info:
            generate_presigned_download_url('test-bucket', 'test-key', 300)
        
        assert 'Failed to generate download URL' in str(exc_info.value.message)
