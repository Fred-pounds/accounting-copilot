"""
Unit tests for audit logger Lambda function.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from lambdas.audit_logger.handler import (
    create_audit_entry,
    log_single_entry,
    log_batch_entries,
    lambda_handler
)


class TestCreateAuditEntry:
    """Tests for create_audit_entry function."""
    
    def test_create_audit_entry_with_required_fields(self):
        """Test creating audit entry with only required fields."""
        entry = create_audit_entry(
            user_id='user123',
            action_type='classification'
        )
        
        assert entry['PK'] == 'USER#user123'
        assert entry['SK'].startswith('AUDIT#')
        assert entry['entity_type'] == 'audit_entry'
        assert entry['action_type'] == 'classification'
        assert entry['actor'] == 'ai'
        assert 'action_id' in entry
        assert 'timestamp' in entry
    
    def test_create_audit_entry_with_all_fields(self):
        """Test creating audit entry with all fields."""
        entry = create_audit_entry(
            user_id='user123',
            action_type='classification',
            actor='user',
            actor_details='user123',
            subject_type='transaction',
            subject_id='txn_456',
            action_details={'confidence': 0.95, 'category': 'Office Supplies'},
            result='success'
        )
        
        assert entry['actor'] == 'user'
        assert entry['actor_details'] == 'user123'
        assert entry['subject_type'] == 'transaction'
        assert entry['subject_id'] == 'txn_456'
        assert entry['action_details']['confidence'] == 0.95
        assert entry['result'] == 'success'
    
    def test_create_audit_entry_generates_unique_ids(self):
        """Test that each audit entry gets a unique ID."""
        entry1 = create_audit_entry(user_id='user123', action_type='classification')
        entry2 = create_audit_entry(user_id='user123', action_type='classification')
        
        assert entry1['action_id'] != entry2['action_id']
        assert entry1['SK'] != entry2['SK']


class TestLogSingleEntry:
    """Tests for log_single_entry function."""
    
    @patch('lambdas.audit_logger.handler.get_dynamodb_table')
    def test_log_single_entry_success(self, mock_get_table):
        """Test successful single entry logging."""
        mock_table = Mock()
        mock_get_table.return_value = mock_table
        
        event = {
            'user_id': 'user123',
            'action_type': 'classification',
            'actor': 'ai',
            'subject_type': 'transaction',
            'subject_id': 'txn_456'
        }
        
        result = log_single_entry(event)
        
        assert result['status'] == 'success'
        assert 'action_id' in result
        assert 'timestamp' in result
        mock_table.put_item.assert_called_once()
    
    @patch('lambdas.audit_logger.handler.get_dynamodb_table')
    def test_log_single_entry_with_details(self, mock_get_table):
        """Test logging entry with action details."""
        mock_table = Mock()
        mock_get_table.return_value = mock_table
        
        event = {
            'user_id': 'user123',
            'action_type': 'classification',
            'action_details': {
                'confidence': 0.92,
                'category': 'Office Supplies',
                'reasoning': 'Vendor name indicates office supplies'
            }
        }
        
        result = log_single_entry(event)
        
        assert result['status'] == 'success'
        
        # Verify the item passed to DynamoDB includes action_details
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs['Item']
        assert item['action_details']['confidence'] == 0.92
        assert item['action_details']['category'] == 'Office Supplies'


class TestLogBatchEntries:
    """Tests for log_batch_entries function."""
    
    @patch('lambdas.audit_logger.handler.get_dynamodb_table')
    def test_log_batch_entries_small_batch(self, mock_get_table):
        """Test logging a small batch of entries."""
        mock_table = Mock()
        mock_batch_writer = MagicMock()
        mock_table.batch_writer = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=mock_batch_writer), __exit__=MagicMock()))
        mock_get_table.return_value = mock_table
        
        entries = [
            {'user_id': 'user123', 'action_type': 'classification'},
            {'user_id': 'user123', 'action_type': 'reconciliation'},
            {'user_id': 'user123', 'action_type': 'assistant_query'}
        ]
        
        result = log_batch_entries(entries)
        
        assert result['status'] == 'success'
        assert result['entries_logged'] == 3
        assert mock_batch_writer.put_item.call_count == 3
    
    @patch('lambdas.audit_logger.handler.get_dynamodb_table')
    def test_log_batch_entries_large_batch(self, mock_get_table):
        """Test logging a batch larger than DynamoDB limit (25)."""
        mock_table = Mock()
        mock_batch_writer = MagicMock()
        mock_table.batch_writer = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=mock_batch_writer), __exit__=MagicMock()))
        mock_get_table.return_value = mock_table
        
        # Create 30 entries (should be split into 2 batches)
        entries = [
            {'user_id': 'user123', 'action_type': 'classification'}
            for _ in range(30)
        ]
        
        result = log_batch_entries(entries)
        
        assert result['status'] == 'success'
        assert result['entries_logged'] == 30
        assert mock_batch_writer.put_item.call_count == 30


class TestLambdaHandler:
    """Tests for lambda_handler function."""
    
    @patch('lambdas.audit_logger.handler.get_dynamodb_table')
    def test_lambda_handler_single_entry(self, mock_get_table):
        """Test lambda handler with single entry."""
        mock_table = Mock()
        mock_get_table.return_value = mock_table
        
        event = {
            'user_id': 'user123',
            'action_type': 'classification'
        }
        
        context = Mock()
        result = lambda_handler(event, context)
        
        assert result['status'] == 'success'
        assert 'action_id' in result
    
    @patch('lambdas.audit_logger.handler.get_dynamodb_table')
    def test_lambda_handler_batch_entries(self, mock_get_table):
        """Test lambda handler with batch entries."""
        mock_table = Mock()
        mock_batch_writer = MagicMock()
        mock_table.batch_writer = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=mock_batch_writer), __exit__=MagicMock()))
        mock_get_table.return_value = mock_table
        
        event = {
            'entries': [
                {'user_id': 'user123', 'action_type': 'classification'},
                {'user_id': 'user123', 'action_type': 'reconciliation'}
            ]
        }
        
        context = Mock()
        result = lambda_handler(event, context)
        
        assert result['status'] == 'success'
        assert result['entries_logged'] == 2
    
    @patch('lambdas.audit_logger.handler.get_dynamodb_table')
    def test_lambda_handler_error_handling(self, mock_get_table):
        """Test lambda handler error handling."""
        mock_table = Mock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_get_table.return_value = mock_table
        
        event = {
            'user_id': 'user123',
            'action_type': 'classification'
        }
        
        context = Mock()
        result = lambda_handler(event, context)
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    @patch('lambdas.audit_logger.handler.get_dynamodb_table')
    def test_lambda_handler_invalid_batch_format(self, mock_get_table):
        """Test lambda handler with invalid batch format."""
        mock_table = Mock()
        mock_get_table.return_value = mock_table
        
        event = {
            'entries': 'not a list'  # Invalid: should be a list
        }
        
        context = Mock()
        result = lambda_handler(event, context)
        
        assert result['status'] == 'error'
        assert 'error' in result


class TestAuditEntryStructure:
    """Tests for audit entry structure and format."""
    
    def test_partition_key_format(self):
        """Test partition key format."""
        entry = create_audit_entry(user_id='user123', action_type='classification')
        assert entry['PK'] == 'USER#user123'
    
    def test_sort_key_format(self):
        """Test sort key format for chronological ordering."""
        entry = create_audit_entry(user_id='user123', action_type='classification')
        
        # Sort key should be AUDIT#{timestamp}#{action_id}
        assert entry['SK'].startswith('AUDIT#')
        parts = entry['SK'].split('#')
        assert len(parts) == 3
        assert parts[0] == 'AUDIT'
    
    def test_timestamp_format(self):
        """Test timestamp is in ISO 8601 format."""
        entry = create_audit_entry(user_id='user123', action_type='classification')
        
        timestamp = entry['timestamp']
        assert isinstance(timestamp, str)
        assert timestamp.endswith('Z')
        
        # Should be parseable
        from datetime import datetime
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed is not None
    
    def test_action_id_format(self):
        """Test action_id format."""
        entry = create_audit_entry(user_id='user123', action_type='classification')
        
        action_id = entry['action_id']
        assert action_id.startswith('audit_')
    
    def test_default_values(self):
        """Test default values for optional fields."""
        entry = create_audit_entry(user_id='user123', action_type='classification')
        
        assert entry['actor'] == 'ai'
        assert entry['actor_details'] == 'system'
        assert entry['subject_type'] == ''
        assert entry['subject_id'] == ''
        assert entry['action_details'] == {}
        assert entry['result'] == 'success'
