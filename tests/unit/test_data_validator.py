"""
Unit tests for data validator Lambda function.
Tests duplicate detection, outlier detection, and invoice gap detection.
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3

# Import the handler
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from lambdas.data_validator.handler import (
    lambda_handler,
    check_duplicate,
    check_outlier,
    check_invoice_gaps,
    extract_invoice_number,
    send_notification
)


@pytest.fixture
def mock_context():
    """Mock Lambda context."""
    context = Mock()
    context.request_id = 'test-request-id'
    context.function_name = 'data-validator'
    return context


@pytest.fixture
def sample_event():
    """Sample Lambda event."""
    return {
        'transaction_id': 'txn_123',
        'user_id': 'test-user'
    }


@pytest.fixture
def mock_table_with_transaction(dynamodb_table):
    """DynamoDB table with a sample transaction."""
    dynamodb_table.put_item(Item={
        'PK': 'USER#test-user',
        'SK': 'TXN#txn_123',
        'entity_type': 'transaction',
        'transaction_id': 'txn_123',
        'date': '2024-01-15',
        'amount': Decimal('45.99'),
        'currency': 'USD',
        'type': 'expense',
        'category': 'Office Supplies',
        'vendor': 'Office Depot',
        'description': 'Office supplies purchase INV-100',
        'classification_confidence': Decimal('0.92'),
        'status': 'approved',
        'created_at': '2024-01-15T10:00:00Z'
    })
    return dynamodb_table


class TestDuplicateDetection:
    """Test duplicate detection functionality."""
    
    def test_duplicate_same_day(self, mock_table_with_transaction):
        """Test duplicate detection for transactions on same day."""
        # Add a duplicate transaction
        mock_table_with_transaction.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_124',
            'transaction_id': 'txn_124',
            'date': '2024-01-15',
            'amount': Decimal('45.99'),
            'vendor': 'Office Depot',
            'description': 'Another purchase'
        })
        
        transaction = {
            'amount': 45.99,
            'vendor': 'Office Depot',
            'date': '2024-01-15'
        }
        
        result = check_duplicate(mock_table_with_transaction, 'test-user', transaction, 'txn_125')
        assert result is True
    
    def test_duplicate_within_24_hours(self, mock_table_with_transaction):
        """Test duplicate detection within 24 hours."""
        # Add transaction from previous day
        mock_table_with_transaction.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_124',
            'transaction_id': 'txn_124',
            'date': '2024-01-14',
            'amount': Decimal('45.99'),
            'vendor': 'Office Depot'
        })
        
        transaction = {
            'amount': 45.99,
            'vendor': 'Office Depot',
            'date': '2024-01-15'
        }
        
        result = check_duplicate(mock_table_with_transaction, 'test-user', transaction, 'txn_125')
        assert result is True
    
    def test_no_duplicate_different_amount(self, mock_table_with_transaction):
        """Test no duplicate when amount differs."""
        transaction = {
            'amount': 99.99,
            'vendor': 'Office Depot',
            'date': '2024-01-15'
        }
        
        result = check_duplicate(mock_table_with_transaction, 'test-user', transaction, 'txn_125')
        assert result is False
    
    def test_no_duplicate_different_vendor(self, mock_table_with_transaction):
        """Test no duplicate when vendor differs."""
        transaction = {
            'amount': 45.99,
            'vendor': 'Staples',
            'date': '2024-01-15'
        }
        
        result = check_duplicate(mock_table_with_transaction, 'test-user', transaction, 'txn_125')
        assert result is False
    
    def test_no_duplicate_outside_24_hours(self, mock_table_with_transaction):
        """Test no duplicate when date is outside 24 hours."""
        transaction = {
            'amount': 45.99,
            'vendor': 'Office Depot',
            'date': '2024-01-17'
        }
        
        result = check_duplicate(mock_table_with_transaction, 'test-user', transaction, 'txn_125')
        assert result is False


class TestOutlierDetection:
    """Test outlier detection functionality."""
    
    def test_outlier_detected(self, dynamodb_table):
        """Test outlier detection when amount exceeds 3 std deviations."""
        # Add category statistics
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': f"STATS#Office Supplies#{datetime.now().strftime('%Y-%m')}",
            'entity_type': 'category_stats',
            'category': 'Office Supplies',
            'month': datetime.now().strftime('%Y-%m'),
            'transaction_count': 20,
            'total_amount': Decimal('500.00'),
            'average_amount': Decimal('25.00'),
            'std_deviation': Decimal('5.00'),
            'min_amount': Decimal('10.00'),
            'max_amount': Decimal('50.00')
        })
        
        # Transaction with amount = 25 + (3.1 * 5) = 40.5 (outlier)
        transaction = {
            'amount': 41.00,
            'category': 'Office Supplies'
        }
        
        result = check_outlier(dynamodb_table, 'test-user', transaction)
        assert result is True
    
    def test_no_outlier_within_range(self, dynamodb_table):
        """Test no outlier when amount is within normal range."""
        # Add category statistics
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': f"STATS#Office Supplies#{datetime.now().strftime('%Y-%m')}",
            'entity_type': 'category_stats',
            'category': 'Office Supplies',
            'month': datetime.now().strftime('%Y-%m'),
            'transaction_count': 20,
            'total_amount': Decimal('500.00'),
            'average_amount': Decimal('25.00'),
            'std_deviation': Decimal('5.00')
        })
        
        # Transaction within 3 std deviations
        transaction = {
            'amount': 30.00,
            'category': 'Office Supplies'
        }
        
        result = check_outlier(dynamodb_table, 'test-user', transaction)
        assert result is False
    
    def test_no_outlier_insufficient_data(self, dynamodb_table):
        """Test no outlier when insufficient transaction history."""
        # Add category statistics with < 10 transactions
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': f"STATS#Office Supplies#{datetime.now().strftime('%Y-%m')}",
            'entity_type': 'category_stats',
            'category': 'Office Supplies',
            'month': datetime.now().strftime('%Y-%m'),
            'transaction_count': 5,
            'average_amount': Decimal('25.00'),
            'std_deviation': Decimal('5.00')
        })
        
        transaction = {
            'amount': 100.00,
            'category': 'Office Supplies'
        }
        
        result = check_outlier(dynamodb_table, 'test-user', transaction)
        assert result is False
    
    def test_no_outlier_no_stats(self, dynamodb_table):
        """Test no outlier when no statistics exist."""
        transaction = {
            'amount': 100.00,
            'category': 'Office Supplies'
        }
        
        result = check_outlier(dynamodb_table, 'test-user', transaction)
        assert result is False


class TestInvoiceGapDetection:
    """Test invoice gap detection functionality."""
    
    def test_extract_invoice_number_inv_format(self):
        """Test extracting invoice number from INV-123 format."""
        assert extract_invoice_number("Purchase INV-123") == 123
        assert extract_invoice_number("INV-456 Office supplies") == 456
    
    def test_extract_invoice_number_hash_format(self):
        """Test extracting invoice number from #123 format."""
        assert extract_invoice_number("Invoice #789") == 789
        assert extract_invoice_number("#100 Payment") == 100
    
    def test_extract_invoice_number_no_format(self):
        """Test no invoice number extracted."""
        assert extract_invoice_number("Regular purchase") is None
        assert extract_invoice_number("") is None
    
    def test_invoice_gap_detected(self, dynamodb_table):
        """Test invoice gap detection."""
        # Add transactions with invoice numbers 100, 102, 105
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_1',
            'transaction_id': 'txn_1',
            'vendor': 'Office Depot',
            'description': 'Purchase INV-100'
        })
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_2',
            'transaction_id': 'txn_2',
            'vendor': 'Office Depot',
            'description': 'Purchase INV-102'
        })
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_3',
            'transaction_id': 'txn_3',
            'vendor': 'Office Depot',
            'description': 'Purchase INV-105'
        })
        
        transaction = {
            'vendor': 'Office Depot',
            'description': 'Purchase INV-106'
        }
        
        gaps = check_invoice_gaps(dynamodb_table, 'test-user', transaction)
        assert 101 in gaps
        assert 103 in gaps
        assert 104 in gaps
    
    def test_no_invoice_gap(self, dynamodb_table):
        """Test no gaps in sequential invoices."""
        # Add transactions with sequential invoice numbers
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_1',
            'transaction_id': 'txn_1',
            'vendor': 'Office Depot',
            'description': 'Purchase INV-100'
        })
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_2',
            'transaction_id': 'txn_2',
            'vendor': 'Office Depot',
            'description': 'Purchase INV-101'
        })
        
        transaction = {
            'vendor': 'Office Depot',
            'description': 'Purchase INV-102'
        }
        
        gaps = check_invoice_gaps(dynamodb_table, 'test-user', transaction)
        assert len(gaps) == 0
    
    def test_no_invoice_gap_different_vendor(self, dynamodb_table):
        """Test invoice gaps only checked for same vendor."""
        # Add transaction for different vendor
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_1',
            'transaction_id': 'txn_1',
            'vendor': 'Staples',
            'description': 'Purchase INV-100'
        })
        
        transaction = {
            'vendor': 'Office Depot',
            'description': 'Purchase INV-105'
        }
        
        gaps = check_invoice_gaps(dynamodb_table, 'test-user', transaction)
        assert len(gaps) == 0


class TestLambdaHandler:
    """Test the main Lambda handler."""
    
    @patch('lambdas.data_validator.handler.send_notification')
    def test_handler_no_issues(self, mock_send, mock_table_with_transaction, sample_event, mock_context):
        """Test handler when no validation issues found."""
        with patch('lambdas.data_validator.handler.get_dynamodb_table', return_value=mock_table_with_transaction):
            result = lambda_handler(sample_event, mock_context)
        
        assert result['status'] == 'success'
        assert result['transaction_id'] == 'txn_123'
        assert result['has_issues'] is False
        assert len(result['validation_issues']) == 0
        mock_send.assert_not_called()
    
    @patch('lambdas.data_validator.handler.send_notification')
    def test_handler_duplicate_detected(self, mock_send, mock_table_with_transaction, sample_event, mock_context):
        """Test handler when duplicate is detected."""
        # Add duplicate transaction
        mock_table_with_transaction.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_124',
            'transaction_id': 'txn_124',
            'date': '2024-01-15',
            'amount': Decimal('45.99'),
            'vendor': 'Office Depot',
            'description': 'Duplicate purchase'
        })
        
        with patch('lambdas.data_validator.handler.get_dynamodb_table', return_value=mock_table_with_transaction):
            result = lambda_handler(sample_event, mock_context)
        
        assert result['status'] == 'success'
        assert result['has_issues'] is True
        assert 'duplicate_detected' in result['validation_issues']
        mock_send.assert_called()
    
    @patch('lambdas.data_validator.handler.send_notification')
    def test_handler_outlier_detected(self, mock_send, dynamodb_table, sample_event, mock_context):
        """Test handler when outlier is detected."""
        # Add transaction
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_123',
            'transaction_id': 'txn_123',
            'date': '2024-01-15',
            'amount': Decimal('500.00'),  # Outlier amount
            'category': 'Office Supplies',
            'vendor': 'Office Depot',
            'description': 'Large purchase'
        })
        
        # Add category statistics
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': f"STATS#Office Supplies#{datetime.now().strftime('%Y-%m')}",
            'entity_type': 'category_stats',
            'category': 'Office Supplies',
            'month': datetime.now().strftime('%Y-%m'),
            'transaction_count': 20,
            'average_amount': Decimal('25.00'),
            'std_deviation': Decimal('10.00')
        })
        
        with patch('lambdas.data_validator.handler.get_dynamodb_table', return_value=dynamodb_table):
            result = lambda_handler(sample_event, mock_context)
        
        assert result['status'] == 'success'
        assert result['has_issues'] is True
        assert 'outlier_detected' in result['validation_issues']
        mock_send.assert_called()
    
    @patch('lambdas.data_validator.handler.send_notification')
    def test_handler_invoice_gap_detected(self, mock_send, dynamodb_table, sample_event, mock_context):
        """Test handler when invoice gap is detected."""
        # Add transactions with gaps
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_123',
            'transaction_id': 'txn_123',
            'date': '2024-01-15',
            'amount': Decimal('45.99'),
            'category': 'Office Supplies',
            'vendor': 'Office Depot',
            'description': 'Purchase INV-105'
        })
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_100',
            'transaction_id': 'txn_100',
            'vendor': 'Office Depot',
            'description': 'Purchase INV-100'
        })
        
        with patch('lambdas.data_validator.handler.get_dynamodb_table', return_value=dynamodb_table):
            result = lambda_handler(sample_event, mock_context)
        
        assert result['status'] == 'success'
        assert result['has_issues'] is True
        assert 'invoice_gap_detected' in result['validation_issues']
        assert len(result['invoice_gaps']) > 0
        mock_send.assert_called()
    
    def test_handler_transaction_not_found(self, dynamodb_table, sample_event, mock_context):
        """Test handler when transaction not found."""
        with patch('lambdas.data_validator.handler.get_dynamodb_table', return_value=dynamodb_table):
            result = lambda_handler(sample_event, mock_context)
        
        assert result['status'] == 'error'
        assert 'not found' in result['error'].lower()
    
    def test_handler_missing_fields(self, mock_context):
        """Test handler with missing required fields."""
        event = {'transaction_id': 'txn_123'}  # Missing user_id
        
        result = lambda_handler(event, mock_context)
        
        assert result['status'] == 'error'
        assert 'missing' in result['error'].lower()


class TestNotifications:
    """Test notification functionality."""
    
    @patch('lambdas.data_validator.handler.sns_client')
    def test_send_notification_success(self, mock_sns):
        """Test successful notification sending."""
        send_notification('arn:aws:sns:us-east-1:123456789012:test', 'Test Subject', 'Test Message')
        
        mock_sns.publish.assert_called_once_with(
            TopicArn='arn:aws:sns:us-east-1:123456789012:test',
            Subject='Test Subject',
            Message='Test Message'
        )
    
    @patch('lambdas.data_validator.handler.sns_client')
    def test_send_notification_no_topic(self, mock_sns):
        """Test notification with no topic ARN."""
        send_notification('', 'Test Subject', 'Test Message')
        
        mock_sns.publish.assert_not_called()
    
    @patch('lambdas.data_validator.handler.sns_client')
    def test_send_notification_failure(self, mock_sns):
        """Test notification failure handling."""
        mock_sns.publish.side_effect = Exception("SNS error")
        
        # Should not raise exception
        send_notification('arn:aws:sns:us-east-1:123456789012:test', 'Test Subject', 'Test Message')
