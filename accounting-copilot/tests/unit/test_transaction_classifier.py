"""
Unit tests for transaction classifier Lambda function.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from src.lambdas.transaction_classifier.handler import (
    build_classification_prompt,
    fallback_classification,
    classify_with_bedrock,
    get_user_categories,
    lambda_handler,
    DEFAULT_CATEGORIES
)
from shared.exceptions import BedrockError


class TestBuildClassificationPrompt:
    """Tests for build_classification_prompt function."""
    
    def test_builds_prompt_with_all_fields(self):
        """Test prompt building with complete data."""
        extracted_data = {
            'parsed_fields': {
                'date': '2024-01-15',
                'amount': 45.99,
                'vendor': 'Office Depot'
            },
            'extracted_text': 'Office supplies purchase'
        }
        categories = ['Office Supplies', 'Utilities', 'Other']
        
        prompt = build_classification_prompt(extracted_data, categories)
        
        assert 'Office Supplies' in prompt
        assert 'Utilities' in prompt
        assert 'Other' in prompt
        assert '2024-01-15' in prompt
        assert '45.99' in prompt
        assert 'Office Depot' in prompt
        assert 'Office supplies purchase' in prompt
    
    def test_handles_missing_fields(self):
        """Test prompt building with missing fields."""
        extracted_data = {
            'parsed_fields': {},
            'extracted_text': ''
        }
        categories = ['Other']
        
        prompt = build_classification_prompt(extracted_data, categories)
        
        assert 'Unknown' in prompt
        assert 'Other' in prompt


class TestFallbackClassification:
    """Tests for fallback_classification function."""
    
    def test_classifies_office_supplies(self):
        """Test fallback classification for office supplies."""
        extracted_data = {
            'parsed_fields': {
                'vendor': 'Office Depot',
                'amount': 45.99
            },
            'extracted_text': 'Paper and pens'
        }
        
        result = fallback_classification(extracted_data)
        
        assert result['category'] == 'Office Supplies'
        assert result['confidence'] == 0.5
        assert 'office supply keywords' in result['reasoning']
        assert result['transaction_type'] == 'expense'
    
    def test_classifies_utilities(self):
        """Test fallback classification for utilities."""
        extracted_data = {
            'parsed_fields': {
                'vendor': 'Electric Company',
                'amount': 150.00
            },
            'extracted_text': 'Monthly power bill'
        }
        
        result = fallback_classification(extracted_data)
        
        assert result['category'] == 'Utilities'
        assert result['confidence'] == 0.5
    
    def test_classifies_revenue(self):
        """Test fallback classification for revenue."""
        extracted_data = {
            'parsed_fields': {
                'vendor': 'Customer Payment',
                'amount': 1000.00
            },
            'extracted_text': 'Payment received for services'
        }
        
        result = fallback_classification(extracted_data)
        
        assert result['category'] == 'Revenue'
        assert result['transaction_type'] == 'income'
    
    def test_defaults_to_other(self):
        """Test fallback classification defaults to Other."""
        extracted_data = {
            'parsed_fields': {
                'vendor': 'Unknown Vendor',
                'amount': 100.00
            },
            'extracted_text': 'Some transaction'
        }
        
        result = fallback_classification(extracted_data)
        
        assert result['category'] == 'Other'
        assert result['confidence'] == 0.5


class TestGetUserCategories:
    """Tests for get_user_categories function."""
    
    @patch('src.lambdas.transaction_classifier.handler.get_dynamodb_table')
    def test_returns_default_and_custom_categories(self, mock_get_table):
        """Test returns combined default and custom categories."""
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'custom_categories': ['Custom1', 'Custom2']
            }
        }
        mock_get_table.return_value = mock_table
        
        categories = get_user_categories('user123')
        
        assert len(categories) == len(DEFAULT_CATEGORIES) + 2
        assert 'Custom1' in categories
        assert 'Custom2' in categories
        assert 'Office Supplies' in categories
    
    @patch('src.lambdas.transaction_classifier.handler.get_dynamodb_table')
    def test_returns_defaults_when_no_profile(self, mock_get_table):
        """Test returns default categories when no user profile."""
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_get_table.return_value = mock_table
        
        categories = get_user_categories('user123')
        
        assert categories == DEFAULT_CATEGORIES
    
    @patch('src.lambdas.transaction_classifier.handler.get_dynamodb_table')
    def test_returns_defaults_on_error(self, mock_get_table):
        """Test returns default categories on DynamoDB error."""
        mock_table = Mock()
        mock_table.get_item.side_effect = Exception("DynamoDB error")
        mock_get_table.return_value = mock_table
        
        categories = get_user_categories('user123')
        
        assert categories == DEFAULT_CATEGORIES


class TestClassifyWithBedrock:
    """Tests for classify_with_bedrock function."""
    
    @patch('src.lambdas.transaction_classifier.handler.bedrock_runtime')
    def test_successful_classification(self, mock_bedrock):
        """Test successful Bedrock classification."""
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': json.dumps({
                    'category': 'Office Supplies',
                    'confidence': 0.92,
                    'reasoning': 'Vendor indicates office supplies',
                    'transaction_type': 'expense'
                })
            }]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        extracted_data = {
            'parsed_fields': {'vendor': 'Office Depot', 'amount': 45.99},
            'extracted_text': 'Office supplies'
        }
        categories = ['Office Supplies', 'Other']
        
        result = classify_with_bedrock(extracted_data, categories)
        
        assert result['category'] == 'Office Supplies'
        assert result['confidence'] == 0.92
        assert result['reasoning'] == 'Vendor indicates office supplies'
    
    @patch('src.lambdas.transaction_classifier.handler.bedrock_runtime')
    @patch('src.lambdas.transaction_classifier.handler.time.sleep')
    def test_retries_on_client_error(self, mock_sleep, mock_bedrock):
        """Test retry logic on Bedrock client error."""
        mock_bedrock.invoke_model.side_effect = [
            ClientError({'Error': {'Code': 'ThrottlingException'}}, 'invoke_model'),
            ClientError({'Error': {'Code': 'ThrottlingException'}}, 'invoke_model'),
            ClientError({'Error': {'Code': 'ThrottlingException'}}, 'invoke_model')
        ]
        
        extracted_data = {
            'parsed_fields': {'vendor': 'Test', 'amount': 100},
            'extracted_text': 'Test'
        }
        categories = ['Other']
        
        with pytest.raises(BedrockError) as exc_info:
            classify_with_bedrock(extracted_data, categories, max_retries=2)
        
        assert 'Failed to classify transaction after 3 attempts' in str(exc_info.value)
        assert mock_bedrock.invoke_model.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between retries
    
    @patch('src.lambdas.transaction_classifier.handler.bedrock_runtime')
    def test_validates_confidence_score(self, mock_bedrock):
        """Test validation of confidence score."""
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': json.dumps({
                    'category': 'Other',
                    'confidence': 1.5,  # Invalid: > 1.0
                    'reasoning': 'Test',
                    'transaction_type': 'expense'
                })
            }]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        extracted_data = {
            'parsed_fields': {'vendor': 'Test', 'amount': 100},
            'extracted_text': 'Test'
        }
        categories = ['Other']
        
        with pytest.raises(BedrockError):
            classify_with_bedrock(extracted_data, categories, max_retries=0)


class TestLambdaHandler:
    """Tests for lambda_handler function."""
    
    @patch('src.lambdas.transaction_classifier.handler.get_dynamodb_table')
    @patch('src.lambdas.transaction_classifier.handler.classify_with_bedrock')
    @patch('src.lambdas.transaction_classifier.handler.get_user_categories')
    def test_successful_classification_above_threshold(
        self, mock_get_categories, mock_classify, mock_get_table
    ):
        """Test successful classification with high confidence."""
        mock_get_categories.return_value = DEFAULT_CATEGORIES
        mock_classify.return_value = {
            'category': 'Office Supplies',
            'confidence': 0.92,
            'reasoning': 'Test reasoning',
            'transaction_type': 'expense'
        }
        mock_table = Mock()
        mock_get_table.return_value = mock_table
        
        event = {
            'document_id': 'doc_123',
            'user_id': 'user_456',
            'extracted_data': {
                'parsed_fields': {
                    'date': '2024-01-15',
                    'amount': 45.99,
                    'vendor': 'Office Depot',
                    'currency': 'USD'
                },
                'extracted_text': 'Office supplies'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['status'] == 'success'
        assert result['category'] == 'Office Supplies'
        assert result['confidence'] == 0.92
        assert result['flagged_for_review'] is False
        assert mock_table.put_item.called
    
    @patch('src.lambdas.transaction_classifier.handler.get_dynamodb_table')
    @patch('src.lambdas.transaction_classifier.handler.classify_with_bedrock')
    @patch('src.lambdas.transaction_classifier.handler.get_user_categories')
    def test_flags_low_confidence_transactions(
        self, mock_get_categories, mock_classify, mock_get_table
    ):
        """Test transaction flagged when confidence below threshold."""
        mock_get_categories.return_value = DEFAULT_CATEGORIES
        mock_classify.return_value = {
            'category': 'Other',
            'confidence': 0.5,  # Below 0.7 threshold
            'reasoning': 'Uncertain classification',
            'transaction_type': 'expense'
        }
        mock_table = Mock()
        mock_get_table.return_value = mock_table
        
        event = {
            'document_id': 'doc_123',
            'user_id': 'user_456',
            'extracted_data': {
                'parsed_fields': {
                    'date': '2024-01-15',
                    'amount': 100.00,
                    'vendor': 'Unknown Vendor',
                    'currency': 'USD'
                },
                'extracted_text': 'Unknown transaction'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['status'] == 'success'
        assert result['confidence'] == 0.5
        assert result['flagged_for_review'] is True
    
    @patch('src.lambdas.transaction_classifier.handler.get_dynamodb_table')
    @patch('src.lambdas.transaction_classifier.handler.classify_with_bedrock')
    @patch('src.lambdas.transaction_classifier.handler.fallback_classification')
    @patch('src.lambdas.transaction_classifier.handler.get_user_categories')
    def test_uses_fallback_on_bedrock_failure(
        self, mock_get_categories, mock_fallback, mock_classify, mock_get_table
    ):
        """Test fallback classification when Bedrock fails."""
        mock_get_categories.return_value = DEFAULT_CATEGORIES
        mock_classify.side_effect = BedrockError("Bedrock unavailable")
        mock_fallback.return_value = {
            'category': 'Other',
            'confidence': 0.5,
            'reasoning': 'Fallback classification',
            'transaction_type': 'expense'
        }
        mock_table = Mock()
        mock_get_table.return_value = mock_table
        
        event = {
            'document_id': 'doc_123',
            'user_id': 'user_456',
            'extracted_data': {
                'parsed_fields': {
                    'date': '2024-01-15',
                    'amount': 100.00,
                    'vendor': 'Test Vendor',
                    'currency': 'USD'
                },
                'extracted_text': 'Test transaction'
            }
        }
        
        result = lambda_handler(event, None)
        
        assert result['status'] == 'success'
        assert result['category'] == 'Other'
        assert mock_fallback.called
        assert mock_table.put_item.called
