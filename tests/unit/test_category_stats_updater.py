"""
Unit tests for category statistics updater Lambda function.
Tests statistics calculation, stream processing, and scheduled recalculation.
Requirements: 3.3, 3.4
"""

import pytest
import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3

# Import the handler
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from lambdas.category_stats_updater.handler import (
    lambda_handler,
    lambda_handler_stream,
    lambda_handler_scheduled,
    calculate_category_statistics,
    update_category_stats,
    recalculate_all_statistics,
    process_stream_record
)


@pytest.fixture
def mock_context():
    """Mock Lambda context."""
    context = Mock()
    context.request_id = 'test-request-id'
    context.function_name = 'category-stats-updater'
    return context


@pytest.fixture
def sample_stream_event():
    """Sample DynamoDB Stream event."""
    return {
        'Records': [
            {
                'eventName': 'INSERT',
                'dynamodb': {
                    'NewImage': {
                        'PK': {'S': 'USER#test-user'},
                        'SK': {'S': 'TXN#txn_123'},
                        'category': {'S': 'Office Supplies'},
                        'date': {'S': '2024-01-15'},
                        'amount': {'N': '45.99'}
                    }
                }
            }
        ]
    }


@pytest.fixture
def sample_scheduled_event():
    """Sample EventBridge scheduled event."""
    return {
        'source': 'aws.events',
        'detail-type': 'Scheduled Event',
        'time': '2024-01-15T02:00:00Z'
    }


@pytest.fixture
def table_with_transactions(dynamodb_table):
    """DynamoDB table with sample transactions."""
    # Add multiple transactions for Office Supplies category
    transactions = [
        {'amount': 25.00, 'date': '2024-01-05'},
        {'amount': 30.00, 'date': '2024-01-10'},
        {'amount': 45.99, 'date': '2024-01-15'},
        {'amount': 20.00, 'date': '2024-01-20'},
        {'amount': 35.50, 'date': '2024-01-25'},
        {'amount': 50.00, 'date': '2024-01-28'},
        {'amount': 15.00, 'date': '2024-01-30'},
    ]
    
    for i, txn in enumerate(transactions):
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': f'TXN#txn_{i}',
            'GSI1PK': 'USER#test-user#CAT#Office Supplies',
            'GSI1SK': f"DATE#{txn['date']}",
            'entity_type': 'transaction',
            'transaction_id': f'txn_{i}',
            'date': txn['date'],
            'amount': Decimal(str(txn['amount'])),
            'currency': 'USD',
            'type': 'expense',
            'category': 'Office Supplies',
            'vendor': 'Office Depot',
            'description': f'Purchase {i}',
            'status': 'approved'
        })
    
    # Add user profile
    dynamodb_table.put_item(Item={
        'PK': 'USER#test-user',
        'SK': 'PROFILE',
        'entity_type': 'user_profile',
        'email': 'test@example.com',
        'business_name': 'Test Business'
    })
    
    return dynamodb_table


class TestStatisticsCalculation:
    """Test statistics calculation functionality."""
    
    def test_calculate_statistics_with_transactions(self, table_with_transactions):
        """Test calculating statistics with multiple transactions."""
        stats = calculate_category_statistics(
            'test-user',
            'Office Supplies',
            '2024-01',
            table_with_transactions
        )
        
        assert stats is not None
        assert stats.category == 'Office Supplies'
        assert stats.month == '2024-01'
        assert stats.transaction_count == 7
        assert abs(stats.total_amount - 221.49) < 0.01
        assert abs(stats.average_amount - 31.64) < 0.01
        assert stats.min_amount == 15.00
        assert stats.max_amount == 50.00
        assert stats.std_deviation > 0
    
    def test_calculate_statistics_no_transactions(self, dynamodb_table):
        """Test calculating statistics with no transactions."""
        stats = calculate_category_statistics(
            'test-user',
            'NonExistent',
            '2024-01',
            dynamodb_table
        )
        
        assert stats is None
    
    def test_calculate_statistics_single_transaction(self, dynamodb_table):
        """Test calculating statistics with single transaction."""
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_single',
            'GSI1PK': 'USER#test-user#CAT#Marketing',
            'GSI1SK': 'DATE#2024-01-15',
            'entity_type': 'transaction',
            'transaction_id': 'txn_single',
            'date': '2024-01-15',
            'amount': Decimal('100.00'),
            'category': 'Marketing',
            'type': 'expense'
        })
        
        stats = calculate_category_statistics(
            'test-user',
            'Marketing',
            '2024-01',
            dynamodb_table
        )
        
        assert stats is not None
        assert stats.transaction_count == 1
        assert stats.total_amount == 100.00
        assert stats.average_amount == 100.00
        assert stats.std_deviation == 0.0  # Only one transaction
        assert stats.min_amount == 100.00
        assert stats.max_amount == 100.00
    
    def test_calculate_statistics_two_transactions(self, dynamodb_table):
        """Test calculating statistics with two transactions (minimum for std dev)."""
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_1',
            'GSI1PK': 'USER#test-user#CAT#Utilities',
            'GSI1SK': 'DATE#2024-01-10',
            'entity_type': 'transaction',
            'transaction_id': 'txn_1',
            'date': '2024-01-10',
            'amount': Decimal('100.00'),
            'category': 'Utilities',
            'type': 'expense'
        })
        
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_2',
            'GSI1PK': 'USER#test-user#CAT#Utilities',
            'GSI1SK': 'DATE#2024-01-20',
            'entity_type': 'transaction',
            'transaction_id': 'txn_2',
            'date': '2024-01-20',
            'amount': Decimal('200.00'),
            'category': 'Utilities',
            'type': 'expense'
        })
        
        stats = calculate_category_statistics(
            'test-user',
            'Utilities',
            '2024-01',
            dynamodb_table
        )
        
        assert stats is not None
        assert stats.transaction_count == 2
        assert stats.average_amount == 150.00
        assert stats.std_deviation > 0  # Should have std dev with 2 values


class TestUpdateCategoryStats:
    """Test updating category statistics in DynamoDB."""
    
    def test_update_stats_creates_record(self, table_with_transactions):
        """Test that update_category_stats creates a new record."""
        update_category_stats('test-user', 'Office Supplies', '2024-01', table_with_transactions)
        
        # Verify stats record was created
        response = table_with_transactions.get_item(
            Key={
                'PK': 'USER#test-user',
                'SK': 'STATS#Office Supplies#2024-01'
            }
        )
        
        assert 'Item' in response
        item = response['Item']
        assert item['entity_type'] == 'category_stats'
        assert item['category'] == 'Office Supplies'
        assert item['month'] == '2024-01'
        assert int(item['transaction_count']) == 7
        assert 'updated_at' in item
    
    def test_update_stats_deletes_empty_category(self, dynamodb_table):
        """Test that update_category_stats deletes record when no transactions exist."""
        # Create a stats record
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'STATS#Empty#2024-01',
            'entity_type': 'category_stats',
            'category': 'Empty',
            'month': '2024-01',
            'transaction_count': 0
        })
        
        # Update stats for category with no transactions
        update_category_stats('test-user', 'Empty', '2024-01', dynamodb_table)
        
        # Verify stats record was deleted
        response = dynamodb_table.get_item(
            Key={
                'PK': 'USER#test-user',
                'SK': 'STATS#Empty#2024-01'
            }
        )
        
        assert 'Item' not in response


class TestStreamProcessing:
    """Test DynamoDB Stream event processing."""
    
    def test_process_insert_event(self, table_with_transactions):
        """Test processing INSERT stream event."""
        record = {
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'PK': {'S': 'USER#test-user'},
                    'SK': {'S': 'TXN#txn_new'},
                    'category': {'S': 'Office Supplies'},
                    'date': {'S': '2024-01-31'},
                    'amount': {'N': '60.00'}
                }
            }
        }
        
        process_stream_record(record, table_with_transactions)
        
        # Verify stats were updated
        response = table_with_transactions.get_item(
            Key={
                'PK': 'USER#test-user',
                'SK': 'STATS#Office Supplies#2024-01'
            }
        )
        
        assert 'Item' in response
    
    def test_process_modify_event(self, table_with_transactions):
        """Test processing MODIFY stream event."""
        record = {
            'eventName': 'MODIFY',
            'dynamodb': {
                'NewImage': {
                    'PK': {'S': 'USER#test-user'},
                    'SK': {'S': 'TXN#txn_0'},
                    'category': {'S': 'Office Supplies'},
                    'date': {'S': '2024-01-05'},
                    'amount': {'N': '30.00'}  # Changed from 25.00
                }
            }
        }
        
        process_stream_record(record, table_with_transactions)
        
        # Verify stats were recalculated
        response = table_with_transactions.get_item(
            Key={
                'PK': 'USER#test-user',
                'SK': 'STATS#Office Supplies#2024-01'
            }
        )
        
        assert 'Item' in response
    
    def test_process_remove_event(self, table_with_transactions):
        """Test processing REMOVE stream event."""
        record = {
            'eventName': 'REMOVE',
            'dynamodb': {
                'OldImage': {
                    'PK': {'S': 'USER#test-user'},
                    'SK': {'S': 'TXN#txn_0'},
                    'category': {'S': 'Office Supplies'},
                    'date': {'S': '2024-01-05'},
                    'amount': {'N': '25.00'}
                }
            }
        }
        
        process_stream_record(record, table_with_transactions)
        
        # Verify stats were recalculated
        response = table_with_transactions.get_item(
            Key={
                'PK': 'USER#test-user',
                'SK': 'STATS#Office Supplies#2024-01'
            }
        )
        
        assert 'Item' in response
    
    def test_process_non_transaction_record(self, dynamodb_table):
        """Test that non-transaction records are ignored."""
        record = {
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'PK': {'S': 'USER#test-user'},
                    'SK': {'S': 'DOC#doc_123'},  # Not a transaction
                    'entity_type': {'S': 'document'}
                }
            }
        }
        
        # Should not raise an error
        process_stream_record(record, dynamodb_table)


class TestStreamHandler:
    """Test stream handler Lambda function."""
    
    def test_stream_handler_success(self, sample_stream_event, table_with_transactions, mock_context):
        """Test successful stream event processing."""
        response = lambda_handler_stream(sample_stream_event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Statistics updated successfully'
        assert body['records_processed'] == 1
    
    def test_stream_handler_multiple_records(self, table_with_transactions, mock_context):
        """Test processing multiple stream records."""
        event = {
            'Records': [
                {
                    'eventName': 'INSERT',
                    'dynamodb': {
                        'NewImage': {
                            'PK': {'S': 'USER#test-user'},
                            'SK': {'S': 'TXN#txn_new1'},
                            'category': {'S': 'Office Supplies'},
                            'date': {'S': '2024-01-31'},
                            'amount': {'N': '60.00'}
                        }
                    }
                },
                {
                    'eventName': 'INSERT',
                    'dynamodb': {
                        'NewImage': {
                            'PK': {'S': 'USER#test-user'},
                            'SK': {'S': 'TXN#txn_new2'},
                            'category': {'S': 'Marketing'},
                            'date': {'S': '2024-01-31'},
                            'amount': {'N': '100.00'}
                        }
                    }
                }
            ]
        }
        
        response = lambda_handler_stream(event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['records_processed'] == 2


class TestRecalculateAllStatistics:
    """Test full recalculation of statistics."""
    
    def test_recalculate_all_statistics(self, table_with_transactions):
        """Test recalculating all statistics for a user."""
        # Add transactions in different categories and months
        table_with_transactions.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_marketing',
            'GSI1PK': 'USER#test-user#CAT#Marketing',
            'GSI1SK': 'DATE#2024-01-15',
            'entity_type': 'transaction',
            'transaction_id': 'txn_marketing',
            'date': '2024-01-15',
            'amount': Decimal('200.00'),
            'category': 'Marketing',
            'type': 'expense'
        })
        
        table_with_transactions.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_feb',
            'GSI1PK': 'USER#test-user#CAT#Office Supplies',
            'GSI1SK': 'DATE#2024-02-10',
            'entity_type': 'transaction',
            'transaction_id': 'txn_feb',
            'date': '2024-02-10',
            'amount': Decimal('40.00'),
            'category': 'Office Supplies',
            'type': 'expense'
        })
        
        result = recalculate_all_statistics('test-user', table_with_transactions)
        
        assert result['categories_processed'] >= 2  # Office Supplies and Marketing
        assert result['months_processed'] >= 2  # January and February
        assert result['total_combinations'] >= 3  # Office Supplies Jan, Marketing Jan, Office Supplies Feb
        assert 'error' not in result
    
    def test_recalculate_no_transactions(self, dynamodb_table):
        """Test recalculating statistics when user has no transactions."""
        # Add user profile
        dynamodb_table.put_item(Item={
            'PK': 'USER#empty-user',
            'SK': 'PROFILE',
            'entity_type': 'user_profile',
            'email': 'empty@example.com'
        })
        
        result = recalculate_all_statistics('empty-user', dynamodb_table)
        
        assert result['categories_processed'] == 0
        assert result['months_processed'] == 0
        assert result['total_combinations'] == 0


class TestScheduledHandler:
    """Test scheduled handler Lambda function."""
    
    def test_scheduled_handler_success(self, sample_scheduled_event, table_with_transactions, mock_context):
        """Test successful scheduled recalculation."""
        # Mock get_dynamodb_table to return our test table
        with patch('lambdas.category_stats_updater.handler.get_dynamodb_table', return_value=table_with_transactions):
            response = lambda_handler_scheduled(sample_scheduled_event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Scheduled recalculation completed'
        assert 'statistics' in body
        assert body['statistics']['users_processed'] >= 1
    
    def test_scheduled_handler_multiple_users(self, dynamodb_table, mock_context, sample_scheduled_event):
        """Test scheduled handler with multiple users."""
        # Add multiple user profiles
        for i in range(3):
            dynamodb_table.put_item(Item={
                'PK': f'USER#user{i}',
                'SK': 'PROFILE',
                'entity_type': 'user_profile',
                'email': f'user{i}@example.com'
            })
            
            # Add a transaction for each user
            dynamodb_table.put_item(Item={
                'PK': f'USER#user{i}',
                'SK': f'TXN#txn_{i}',
                'GSI1PK': f'USER#user{i}#CAT#Office Supplies',
                'GSI1SK': 'DATE#2024-01-15',
                'entity_type': 'transaction',
                'transaction_id': f'txn_{i}',
                'date': '2024-01-15',
                'amount': Decimal('50.00'),
                'category': 'Office Supplies',
                'type': 'expense'
            })
        
        # Mock get_dynamodb_table to return our test table
        with patch('lambdas.category_stats_updater.handler.get_dynamodb_table', return_value=dynamodb_table):
            response = lambda_handler_scheduled(sample_scheduled_event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['statistics']['users_processed'] == 3


class TestMainHandler:
    """Test main Lambda handler routing."""
    
    def test_handler_routes_to_stream(self, sample_stream_event, table_with_transactions, mock_context):
        """Test that main handler routes to stream handler."""
        response = lambda_handler(sample_stream_event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'records_processed' in body
    
    def test_handler_routes_to_scheduled(self, sample_scheduled_event, table_with_transactions, mock_context):
        """Test that main handler routes to scheduled handler."""
        # Mock get_dynamodb_table to return our test table
        with patch('lambdas.category_stats_updater.handler.get_dynamodb_table', return_value=table_with_transactions):
            response = lambda_handler(sample_scheduled_event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'statistics' in body
    
    def test_handler_defaults_to_scheduled(self, table_with_transactions, mock_context):
        """Test that main handler defaults to scheduled for unknown events."""
        event = {'unknown': 'event'}
        
        # Mock get_dynamodb_table to return our test table
        with patch('lambdas.category_stats_updater.handler.get_dynamodb_table', return_value=table_with_transactions):
            response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'statistics' in body


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_calculate_stats_with_decimal_amounts(self, dynamodb_table):
        """Test calculating statistics with Decimal amounts."""
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_1',
            'GSI1PK': 'USER#test-user#CAT#Test',
            'GSI1SK': 'DATE#2024-01-15',
            'entity_type': 'transaction',
            'transaction_id': 'txn_1',
            'date': '2024-01-15',
            'amount': Decimal('45.99'),
            'category': 'Test',
            'type': 'expense'
        })
        
        stats = calculate_category_statistics('test-user', 'Test', '2024-01', dynamodb_table)
        
        assert stats is not None
        assert isinstance(stats.average_amount, float)
    
    def test_process_stream_record_missing_fields(self, dynamodb_table):
        """Test processing stream record with missing fields."""
        record = {
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'PK': {'S': 'USER#test-user'},
                    'SK': {'S': 'TXN#txn_incomplete'}
                    # Missing category and date
                }
            }
        }
        
        # Should not raise an error
        process_stream_record(record, dynamodb_table)
    
    def test_calculate_stats_with_iso_date_format(self, dynamodb_table):
        """Test calculating statistics with ISO 8601 date format."""
        dynamodb_table.put_item(Item={
            'PK': 'USER#test-user',
            'SK': 'TXN#txn_iso',
            'GSI1PK': 'USER#test-user#CAT#Test',
            'GSI1SK': 'DATE#2024-01-15T10:30:00Z',
            'entity_type': 'transaction',
            'transaction_id': 'txn_iso',
            'date': '2024-01-15T10:30:00Z',
            'amount': Decimal('100.00'),
            'category': 'Test',
            'type': 'expense'
        })
        
        stats = calculate_category_statistics('test-user', 'Test', '2024-01', dynamodb_table)
        
        assert stats is not None
        assert stats.month == '2024-01'
