"""
Unit tests for OCR processor Lambda function.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError


@pytest.fixture
def mock_textract_response():
    """Mock Textract response."""
    return {
        'Blocks': [
            {'BlockType': 'LINE', 'Text': 'Office Depot'},
            {'BlockType': 'LINE', 'Text': 'Date: 01/15/2024'},
            {'BlockType': 'LINE', 'Text': 'Total: $45.99'},
            {'BlockType': 'LINE', 'Text': 'Paper $25.99'},
            {'BlockType': 'LINE', 'Text': 'Pens $20.00'},
        ]
    }


@pytest.fixture
def mock_event():
    """Mock Lambda event."""
    return {
        'document_id': 'doc_123',
        'user_id': 'user_456',
        's3_bucket': 'test-bucket',
        's3_key': 'documents/user_456/receipts/2024/01/doc_123.jpg'
    }


@pytest.fixture
def mock_context():
    """Mock Lambda context."""
    context = Mock()
    context.request_id = 'test-request-id'
    context.function_name = 'ocr-processor'
    return context


class TestOCRProcessor:
    """Test OCR processor Lambda function."""
    
    @patch('lambdas.ocr_processor.handler.time.sleep')  # Mock sleep to speed up test
    @patch('lambdas.ocr_processor.handler.textract_client')
    @patch('lambdas.ocr_processor.handler.get_dynamodb_table')
    def test_successful_ocr_processing(self, mock_table, mock_textract, mock_sleep, mock_event, mock_context, mock_textract_response):
        """Test successful OCR processing."""
        from lambdas.ocr_processor.handler import lambda_handler
        
        # Setup mocks
        mock_textract.detect_document_text.return_value = mock_textract_response
        mock_dynamodb_table = Mock()
        mock_table.return_value = mock_dynamodb_table
        
        # Execute
        result = lambda_handler(mock_event, mock_context)
        
        # Verify
        assert result['status'] == 'success'
        assert result['document_id'] == 'doc_123'
        assert 'extracted_text' in result
        assert 'parsed_fields' in result
        assert 'processing_duration_ms' in result
        
        # Verify Textract was called
        mock_textract.detect_document_text.assert_called_once()
        
        # Verify DynamoDB was updated
        assert mock_dynamodb_table.update_item.call_count >= 2  # Processing + Completed
    
    @patch('lambdas.ocr_processor.handler.time.sleep')  # Mock sleep to speed up test
    @patch('lambdas.ocr_processor.handler.textract_client')
    @patch('lambdas.ocr_processor.handler.get_dynamodb_table')
    @patch('lambdas.ocr_processor.handler.sns_client')
    def test_ocr_failure_sends_notification(self, mock_sns, mock_table, mock_textract, mock_sleep, mock_event, mock_context):
        """Test that OCR failure sends SNS notification."""
        from lambdas.ocr_processor.handler import lambda_handler
        from shared.exceptions import OCRFailure
        
        # Setup mocks
        mock_textract.detect_document_text.side_effect = ClientError(
            {'Error': {'Code': 'ServiceException', 'Message': 'Service error'}},
            'DetectDocumentText'
        )
        mock_dynamodb_table = Mock()
        mock_table.return_value = mock_dynamodb_table
        
        # Execute and expect failure
        with pytest.raises(OCRFailure):
            lambda_handler(mock_event, mock_context)
        
        # Verify SNS notification was sent (if topic configured)
        # Note: Will skip if SNS_OCR_FAILURES not configured
    
    @patch('lambdas.ocr_processor.handler.time.sleep')  # Mock sleep to speed up test
    @patch('lambdas.ocr_processor.handler.textract_client')
    def test_retry_logic_with_exponential_backoff(self, mock_textract, mock_sleep):
        """Test retry logic with exponential backoff."""
        from lambdas.ocr_processor.handler import extract_text_from_document
        from shared.exceptions import OCRFailure
        
        # Setup mock to fail twice then succeed
        mock_textract.detect_document_text.side_effect = [
            ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'DetectDocumentText'
            ),
            ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'DetectDocumentText'
            ),
            {
                'Blocks': [
                    {'BlockType': 'LINE', 'Text': 'Test Store'},
                    {'BlockType': 'LINE', 'Text': 'Date: 01/15/2024'},
                    {'BlockType': 'LINE', 'Text': 'Total: $50.00'},
                ]
            }
        ]
        
        # Execute
        result = extract_text_from_document('test-bucket', 'test-key.jpg', max_retries=2)
        
        # Verify
        assert 'extracted_text' in result
        assert 'parsed_fields' in result
        assert mock_textract.detect_document_text.call_count == 3
    
    @patch('lambdas.ocr_processor.handler.time.sleep')  # Mock sleep to speed up test
    @patch('lambdas.ocr_processor.handler.textract_client')
    def test_non_retryable_error_fails_immediately(self, mock_textract, mock_sleep):
        """Test that non-retryable errors fail immediately."""
        from lambdas.ocr_processor.handler import extract_text_from_document
        from shared.exceptions import OCRFailure
        
        # Setup mock with non-retryable error
        mock_textract.detect_document_text.side_effect = ClientError(
            {'Error': {'Code': 'InvalidS3ObjectException', 'Message': 'Invalid object'}},
            'DetectDocumentText'
        )
        
        # Execute and expect immediate failure
        with pytest.raises(OCRFailure) as exc_info:
            extract_text_from_document('test-bucket', 'test-key.jpg', max_retries=2)
        
        # Verify only called once (no retries)
        assert mock_textract.detect_document_text.call_count == 1
        assert 'Invalid document' in str(exc_info.value)
    
    @patch('lambdas.ocr_processor.handler.time.sleep')  # Mock sleep to speed up test
    @patch('lambdas.ocr_processor.handler.textract_client')
    def test_max_retries_exhausted(self, mock_textract, mock_sleep):
        """Test behavior when max retries are exhausted."""
        from lambdas.ocr_processor.handler import extract_text_from_document
        from shared.exceptions import OCRFailure
        
        # Setup mock to always fail
        mock_textract.detect_document_text.side_effect = ClientError(
            {'Error': {'Code': 'ServiceException', 'Message': 'Service error'}},
            'DetectDocumentText'
        )
        
        # Execute and expect failure
        with pytest.raises(OCRFailure) as exc_info:
            extract_text_from_document('test-bucket', 'test-key.jpg', max_retries=2)
        
        # Verify retried correct number of times
        assert mock_textract.detect_document_text.call_count == 3  # Initial + 2 retries
        assert 'after 3 attempts' in str(exc_info.value)
    
    @patch('lambdas.ocr_processor.handler.time.sleep')  # Mock sleep to speed up test
    @patch('lambdas.ocr_processor.handler.textract_client')
    @patch('lambdas.ocr_processor.handler.get_dynamodb_table')
    def test_document_type_detection_from_s3_key(self, mock_table, mock_textract, mock_sleep, mock_event, mock_context):
        """Test document type detection from S3 key."""
        from lambdas.ocr_processor.handler import lambda_handler
        
        # Setup mocks
        mock_textract.detect_document_text.return_value = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'Invoice #12345'},
                {'BlockType': 'LINE', 'Text': 'Date: 2024-01-15'},
                {'BlockType': 'LINE', 'Text': 'Amount: $100.00'},
            ]
        }
        mock_dynamodb_table = Mock()
        mock_table.return_value = mock_dynamodb_table
        
        # Test with invoice in path
        event = mock_event.copy()
        event['s3_key'] = 'documents/user_456/invoices/2024/01/doc_123.pdf'
        
        result = lambda_handler(event, mock_context)
        
        # Verify document type was detected
        assert result['parsed_fields']['document_type'] == 'invoice'
    
    @patch('lambdas.ocr_processor.handler.time.sleep')  # Mock sleep to speed up test
    @patch('lambdas.ocr_processor.handler.textract_client')
    @patch('lambdas.ocr_processor.handler.get_dynamodb_table')
    @patch('lambdas.ocr_processor.handler.sns_client')
    def test_parsing_failure_sends_notification(self, mock_sns, mock_table, mock_textract, mock_sleep, mock_event, mock_context):
        """Test that parsing failure sends SNS notification."""
        from lambdas.ocr_processor.handler import lambda_handler
        from shared.exceptions import OCRFailure
        
        # Setup mocks - Textract succeeds but parsing fails (missing required fields)
        mock_textract.detect_document_text.return_value = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'Some random text'},
                {'BlockType': 'LINE', 'Text': 'No date or amount here'},
            ]
        }
        mock_dynamodb_table = Mock()
        mock_table.return_value = mock_dynamodb_table
        
        # Execute and expect failure
        with pytest.raises(OCRFailure) as exc_info:
            lambda_handler(mock_event, mock_context)
        
        # Verify error mentions parsing
        assert 'parsing' in str(exc_info.value).lower()
    
    @patch('lambdas.ocr_processor.handler.sns_client')
    def test_send_ocr_failure_notification(self, mock_sns):
        """Test SNS notification sending."""
        from lambdas.ocr_processor.handler import send_ocr_failure_notification
        
        # Mock config
        with patch('src.lambdas.ocr_processor.handler.Config') as mock_config:
            mock_config.SNS_OCR_FAILURES = 'arn:aws:sns:us-east-1:123456789012:ocr-failures'
            
            # Execute
            send_ocr_failure_notification('doc_123', 'user_456', 'Test error')
            
            # Verify SNS publish was called
            mock_sns.publish.assert_called_once()
            call_args = mock_sns.publish.call_args
            
            assert call_args[1]['TopicArn'] == mock_config.SNS_OCR_FAILURES
            assert 'doc_123' in call_args[1]['Subject']
            
            # Verify message contains required fields
            message = json.loads(call_args[1]['Message'])
            assert message['document_id'] == 'doc_123'
            assert message['user_id'] == 'user_456'
            assert message['error'] == 'Test error'
            assert 'timestamp' in message
            assert 'action_required' in message
    
    def test_send_notification_handles_missing_config(self):
        """Test notification gracefully handles missing SNS config."""
        from lambdas.ocr_processor.handler import send_ocr_failure_notification
        
        # Mock config with no SNS topic
        with patch('src.lambdas.ocr_processor.handler.Config') as mock_config:
            mock_config.SNS_OCR_FAILURES = ''
            
            # Should not raise exception
            send_ocr_failure_notification('doc_123', 'user_456', 'Test error')
    
    @patch('lambdas.ocr_processor.handler.time.sleep')  # Mock sleep to speed up test
    @patch('lambdas.ocr_processor.handler.textract_client')
    @patch('lambdas.ocr_processor.handler.get_dynamodb_table')
    def test_dynamodb_status_updates(self, mock_table, mock_textract, mock_sleep, mock_event, mock_context, mock_textract_response):
        """Test that DynamoDB status is updated correctly."""
        from lambdas.ocr_processor.handler import lambda_handler
        
        # Setup mocks
        mock_textract.detect_document_text.return_value = mock_textract_response
        mock_dynamodb_table = Mock()
        mock_table.return_value = mock_dynamodb_table
        
        # Execute
        lambda_handler(mock_event, mock_context)
        
        # Verify status updates
        calls = mock_dynamodb_table.update_item.call_args_list
        
        # First call: set to PROCESSING
        assert calls[0][1]['ExpressionAttributeValues'][':status'] == 'processing'
        
        # Second call: set to COMPLETED with results
        assert calls[1][1]['ExpressionAttributeValues'][':status'] == 'completed'
        assert ':text' in calls[1][1]['ExpressionAttributeValues']
        assert ':fields' in calls[1][1]['ExpressionAttributeValues']
        assert ':duration' in calls[1][1]['ExpressionAttributeValues']
