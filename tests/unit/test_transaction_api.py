"""
Unit tests for Transaction API Lambda function.
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from src.lambdas.transaction_api.handler import (
    lambda_handler_create,
    lambda_handler_get,
    lambda_handler_list,
    lambda_handler_update,
    lambda_handler_delete,
    lambda_handler_approve,
    lambda_handler_correct,
    validate_transaction_data,
    update_category_statistics
)
from src.shared.exceptions import ValidationError, NotFoundError
from src.shared.exceptions import ValidationError, NotFoundError
from src.shared.models import Transaction, CategoryStats, generate_user_pk, generate_transaction_sk


@pytest.fixture
def mock_context():
    """Create mock Lambda context."""
    context = Mock()
    context.request_id = "test-request-id"
    return context


@pytest.fixture
def mock_event():
    """Create mock API Gateway event."""
    return {
        'headers': {
            'Authorization': 'Bearer test-token'
        },
        'body': '{}',
        'pathParameters': {},
        'queryStringParameters': None
    }


@pytest.fixture
def mock_repository():
    """Create mock DynamoDB repository."""
    with patch('src.lambdas.transaction_api.handler.get_repository') as mock_get_repo:
        repo = Mock()
        mock_get_repo.return_value = repo
        yield repo


@pytest.fixture
def mock_auth():
    """Mock authentication functions."""
    with patch('src.lambdas.transaction_api.handler.extract_token_from_event') as mock_extract, \
         patch('src.lambdas.transaction_api.handler.get_user_id_from_token') as mock_get_user:
        mock_extract.return_value = 'test-token'
        mock_get_user.return_value = 'test-user-id'
        yield mock_extract, mock_get_user


class TestValidateTransactionData:
    """Tests for validate_transaction_data function."""
    
    def test_valid_transaction_data(self):
        """Test validation with valid data."""
        data = {
            'date': '2024-01-15',
            'amount': 100.50,
            'type': 'expense',
            'category': 'Office Supplies',
            'vendor': 'Office Depot',
            'description': 'Paper and pens'
        }
        # Should not raise
        validate_transaction_data(data)
    
    def test_partial_validation(self):
        """Test partial validation for updates."""
        data = {
            'amount': 150.00
        }
        # Should not raise with partial=True
        validate_transaction_data(data, partial=True)


class TestCreateTransaction:
    """Tests for lambda_handler_create."""
    
    def test_create_transaction_success(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test successful transaction creation."""
        # Setup
        transaction_data = {
            'date': '2024-01-15',
            'amount': 100.50,
            'type': 'expense',
            'category': 'Office Supplies',
            'vendor': 'Office Depot',
            'description': 'Paper and pens'
        }
        mock_event['body'] = json.dumps(transaction_data)
        
        # Mock repository methods
        mock_repository.create_transaction.return_value = Mock()
        mock_repository.query_transactions_by_category.return_value = []
        
        # Execute
        response = lambda_handler_create(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert 'transaction_id' in body
        assert body['message'] == 'Transaction created successfully'
        mock_repository.create_transaction.assert_called_once()
    
    def test_create_transaction_missing_fields(self, mock_event, mock_context, mock_auth):
        """Test creation with missing required fields."""
        # Setup
        transaction_data = {
            'date': '2024-01-15',
            'amount': 100.50
        }
        mock_event['body'] = json.dumps(transaction_data)
        
        # Execute
        response = lambda_handler_create(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing required fields' in body['error']['message']
    
    def test_create_transaction_invalid_date(self, mock_event, mock_context, mock_auth):
        """Test creation with invalid date format."""
        # Setup
        transaction_data = {
            'date': '01/15/2024',
            'amount': 100.50,
            'type': 'expense',
            'category': 'Office Supplies',
            'vendor': 'Office Depot',
            'description': 'Paper and pens'
        }
        mock_event['body'] = json.dumps(transaction_data)
        
        # Execute
        response = lambda_handler_create(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid date format' in body['error']['message']


class TestGetTransaction:
    """Tests for lambda_handler_get."""
    
    def test_get_transaction_success(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test successful transaction retrieval."""
        # Setup
        transaction_id = 'txn_123'
        mock_event['pathParameters'] = {'id': transaction_id}
        
        mock_transaction = Mock()
        mock_transaction.to_dict.return_value = {
            'transaction_id': transaction_id,
            'amount': 100.50,
            'category': 'Office Supplies'
        }
        mock_repository.get_transaction.return_value = mock_transaction
        
        # Execute
        response = lambda_handler_get(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['transaction_id'] == transaction_id
        mock_repository.get_transaction.assert_called_once_with('test-user-id', transaction_id)
    
    def test_get_transaction_not_found(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test retrieval of non-existent transaction."""
        # Setup
        transaction_id = 'txn_nonexistent'
        mock_event['pathParameters'] = {'id': transaction_id}
        mock_repository.get_transaction.return_value = None
        
        # Execute
        response = lambda_handler_get(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found' in body['error']['message']
    
    def test_get_transaction_missing_id(self, mock_event, mock_context, mock_auth):
        """Test retrieval without transaction ID."""
        # Setup
        mock_event['pathParameters'] = {}
        
        # Execute
        response = lambda_handler_get(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Transaction ID is required' in body['error']['message']


class TestListTransactions:
    """Tests for lambda_handler_list."""
    
    def test_list_transactions_no_filters(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test listing all transactions without filters."""
        # Setup
        mock_transactions = [
            Mock(to_dict=lambda: {'transaction_id': 'txn_1', 'amount': 100}),
            Mock(to_dict=lambda: {'transaction_id': 'txn_2', 'amount': 200})
        ]
        mock_repository.list_transactions.return_value = mock_transactions
        
        # Execute
        response = lambda_handler_list(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2
        assert len(body['transactions']) == 2
        mock_repository.list_transactions.assert_called_once()
    
    def test_list_transactions_by_category(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test listing transactions filtered by category."""
        # Setup
        mock_event['queryStringParameters'] = {'category': 'Office Supplies'}
        mock_transactions = [
            Mock(to_dict=lambda: {'transaction_id': 'txn_1', 'category': 'Office Supplies'})
        ]
        mock_repository.query_transactions_by_category.return_value = mock_transactions
        
        # Execute
        response = lambda_handler_list(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        mock_repository.query_transactions_by_category.assert_called_once()
    
    def test_list_transactions_by_date_range(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test listing transactions filtered by date range."""
        # Setup
        mock_event['queryStringParameters'] = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        mock_transactions = [
            Mock(to_dict=lambda: {'transaction_id': 'txn_1', 'date': '2024-01-15'})
        ]
        mock_repository.query_transactions_by_date_range.return_value = mock_transactions
        
        # Execute
        response = lambda_handler_list(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        mock_repository.query_transactions_by_date_range.assert_called_once()
    
    def test_list_transactions_by_status(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test listing transactions filtered by status."""
        # Setup
        mock_event['queryStringParameters'] = {'status': 'pending'}
        mock_transactions = [
            Mock(to_dict=lambda: {'transaction_id': 'txn_1', 'status': 'pending'})
        ]
        mock_repository.query_transactions_by_status.return_value = mock_transactions
        
        # Execute
        response = lambda_handler_list(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        mock_repository.query_transactions_by_status.assert_called_once()
    
    def test_list_transactions_by_type(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test listing transactions filtered by type."""
        # Setup
        mock_event['queryStringParameters'] = {'type': 'expense'}
        mock_transactions = [
            Mock(type='expense', to_dict=lambda: {'transaction_id': 'txn_1', 'type': 'expense'}),
            Mock(type='income', to_dict=lambda: {'transaction_id': 'txn_2', 'type': 'income'})
        ]
        mock_repository.list_transactions.return_value = mock_transactions
        
        # Execute
        response = lambda_handler_list(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1  # Only expense transactions


class TestUpdateTransaction:
    """Tests for lambda_handler_update."""
    
    def test_update_transaction_success(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test successful transaction update."""
        # Setup
        transaction_id = 'txn_123'
        mock_event['pathParameters'] = {'id': transaction_id}
        mock_event['body'] = json.dumps({'amount': 150.00})
        
        existing_transaction = Mock()
        existing_transaction.category = 'Office Supplies'
        existing_transaction.date = '2024-01-15'
        mock_repository.get_transaction.return_value = existing_transaction
        
        updated_transaction = Mock()
        updated_transaction.to_dict.return_value = {
            'transaction_id': transaction_id,
            'amount': 150.00
        }
        mock_repository.update_transaction.return_value = updated_transaction
        mock_repository.query_transactions_by_category.return_value = []
        
        # Execute
        response = lambda_handler_update(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Transaction updated successfully'
        mock_repository.update_transaction.assert_called_once()
    
    def test_update_transaction_not_found(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test updating non-existent transaction."""
        # Setup
        transaction_id = 'txn_nonexistent'
        mock_event['pathParameters'] = {'id': transaction_id}
        mock_event['body'] = json.dumps({'amount': 150.00})
        mock_repository.get_transaction.return_value = None
        
        # Execute
        response = lambda_handler_update(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found' in body['error']['message']
    
    def test_update_transaction_category_change(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test updating transaction with category change."""
        # Setup
        transaction_id = 'txn_123'
        mock_event['pathParameters'] = {'id': transaction_id}
        mock_event['body'] = json.dumps({'category': 'Utilities'})
        
        existing_transaction = Mock()
        existing_transaction.category = 'Office Supplies'
        existing_transaction.date = '2024-01-15'
        mock_repository.get_transaction.return_value = existing_transaction
        
        updated_transaction = Mock()
        updated_transaction.to_dict.return_value = {
            'transaction_id': transaction_id,
            'category': 'Utilities'
        }
        mock_repository.update_transaction.return_value = updated_transaction
        mock_repository.query_transactions_by_category.return_value = []
        
        # Execute
        response = lambda_handler_update(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        # Should update stats for both old and new categories
        assert mock_repository.query_transactions_by_category.call_count >= 2


class TestDeleteTransaction:
    """Tests for lambda_handler_delete."""
    
    def test_delete_transaction_success(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test successful transaction deletion."""
        # Setup
        transaction_id = 'txn_123'
        mock_event['pathParameters'] = {'id': transaction_id}
        
        existing_transaction = Mock()
        existing_transaction.category = 'Office Supplies'
        existing_transaction.date = '2024-01-15'
        mock_repository.get_transaction.return_value = existing_transaction
        mock_repository.query_transactions_by_category.return_value = []
        
        # Execute
        response = lambda_handler_delete(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Transaction deleted successfully'
        mock_repository.delete_transaction.assert_called_once_with('test-user-id', transaction_id)
    
    def test_delete_transaction_not_found(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test deleting non-existent transaction."""
        # Setup
        transaction_id = 'txn_nonexistent'
        mock_event['pathParameters'] = {'id': transaction_id}
        mock_repository.get_transaction.return_value = None
        
        # Execute
        response = lambda_handler_delete(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found' in body['error']['message']


class TestApproveTransaction:
    """Tests for lambda_handler_approve."""
    
    def test_approve_transaction_success(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test successful transaction approval."""
        # Setup
        transaction_id = 'txn_123'
        mock_event['pathParameters'] = {'id': transaction_id}
        
        existing_transaction = Mock()
        existing_transaction.status = 'pending_review'
        mock_repository.get_transaction.return_value = existing_transaction
        
        updated_transaction = Mock()
        updated_transaction.to_dict.return_value = {
            'transaction_id': transaction_id,
            'status': 'approved'
        }
        mock_repository.update_transaction.return_value = updated_transaction
        
        # Execute
        response = lambda_handler_approve(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Transaction approved successfully'
        mock_repository.update_transaction.assert_called_once()
    
    def test_approve_transaction_not_found(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test approving non-existent transaction."""
        # Setup
        transaction_id = 'txn_nonexistent'
        mock_event['pathParameters'] = {'id': transaction_id}
        mock_repository.get_transaction.return_value = None
        
        # Execute
        response = lambda_handler_approve(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found' in body['error']['message']


class TestCorrectTransaction:
    """Tests for lambda_handler_correct."""
    
    def test_correct_transaction_success(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test successful transaction classification correction."""
        # Setup
        transaction_id = 'txn_123'
        mock_event['pathParameters'] = {'id': transaction_id}
        mock_event['body'] = json.dumps({
            'new_category': 'Utilities',
            'reason': 'Misclassified'
        })
        
        existing_transaction = Mock()
        existing_transaction.category = 'Office Supplies'
        existing_transaction.date = '2024-01-15'
        mock_repository.get_transaction.return_value = existing_transaction
        
        updated_transaction = Mock()
        updated_transaction.to_dict.return_value = {
            'transaction_id': transaction_id,
            'category': 'Utilities'
        }
        mock_repository.update_transaction.return_value = updated_transaction
        mock_repository.query_transactions_by_category.return_value = []
        
        # Execute
        response = lambda_handler_correct(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Transaction classification corrected successfully'
        mock_repository.update_transaction.assert_called_once()
        # Should update stats for both old and new categories
        assert mock_repository.query_transactions_by_category.call_count >= 2
    
    def test_correct_transaction_missing_category(self, mock_event, mock_context, mock_auth):
        """Test correction without new_category."""
        # Setup
        transaction_id = 'txn_123'
        mock_event['pathParameters'] = {'id': transaction_id}
        mock_event['body'] = json.dumps({'reason': 'Misclassified'})
        
        # Execute
        response = lambda_handler_correct(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'new_category is required' in body['error']['message']
    
    def test_correct_transaction_not_found(self, mock_event, mock_context, mock_repository, mock_auth):
        """Test correcting non-existent transaction."""
        # Setup
        transaction_id = 'txn_nonexistent'
        mock_event['pathParameters'] = {'id': transaction_id}
        mock_event['body'] = json.dumps({'new_category': 'Utilities'})
        mock_repository.get_transaction.return_value = None
        
        # Execute
        response = lambda_handler_correct(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found' in body['error']['message']


class TestUpdateCategoryStatistics:
    """Tests for update_category_statistics function."""
    
    def test_update_stats_with_transactions(self, mock_repository):
        """Test updating category statistics with transactions."""
        # Setup
        user_id = 'test-user-id'
        category = 'Office Supplies'
        month = '2024-01'
        
        mock_transactions = [
            Mock(amount=Decimal('100.00')),
            Mock(amount=Decimal('150.00')),
            Mock(amount=Decimal('200.00'))
        ]
        mock_repository.query_transactions_by_category.return_value = mock_transactions
        
        # Execute
        update_category_statistics(user_id, category, month, mock_repository)
        
        # Assert
        mock_repository.create_or_update_category_stats.assert_called_once()
        call_args = mock_repository.create_or_update_category_stats.call_args[0]
        stats = call_args[1]
        
        assert stats.category == category
        assert stats.month == month
        assert stats.transaction_count == 3
        assert stats.total_amount == 450.00
        assert stats.average_amount == 150.00
    
    def test_update_stats_no_transactions(self, mock_repository):
        """Test updating category statistics with no transactions."""
        # Setup
        user_id = 'test-user-id'
        category = 'Office Supplies'
        month = '2024-01'
        
        mock_repository.query_transactions_by_category.return_value = []
        
        # Execute
        update_category_statistics(user_id, category, month, mock_repository)
        
        # Assert
        # Should not create stats if no transactions
        mock_repository.create_or_update_category_stats.assert_not_called()
    
    def test_update_stats_single_transaction(self, mock_repository):
        """Test updating category statistics with single transaction."""
        # Setup
        user_id = 'test-user-id'
        category = 'Office Supplies'
        month = '2024-01'
        
        mock_transactions = [
            Mock(amount=Decimal('100.00'))
        ]
        mock_repository.query_transactions_by_category.return_value = mock_transactions
        
        # Execute
        update_category_statistics(user_id, category, month, mock_repository)
        
        # Assert
        mock_repository.create_or_update_category_stats.assert_called_once()
        call_args = mock_repository.create_or_update_category_stats.call_args[0]
        stats = call_args[1]
        
        assert stats.transaction_count == 1
        assert stats.std_deviation == 0.0  # Single value has no deviation


class TestErrorHandling:
    """Tests for general error handling."""
    
    def test_unhandled_exception(self, mock_event, mock_context, mock_auth, mock_repository):
        """Test handling of unexpected exceptions."""
        # Setup
        mock_event['body'] = json.dumps({
            'date': '2024-01-15',
            'amount': 100.50,
            'type': 'expense',
            'category': 'Office Supplies',
            'vendor': 'Office Depot',
            'description': 'Paper and pens'
        })
        
        # Make repository raise an unexpected exception
        mock_repository.create_transaction.side_effect = Exception("Unexpected error")
        
        # Execute
        response = lambda_handler_create(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Internal server error' in body['error']['message']
