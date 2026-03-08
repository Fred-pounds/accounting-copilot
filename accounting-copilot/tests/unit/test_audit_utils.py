"""
Unit tests for shared audit utilities.
"""

import pytest
import json
from unittest.mock import Mock, patch, call
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from shared.audit import (
    log_audit_entry,
    log_classification_audit,
    log_reconciliation_audit,
    log_assistant_query_audit,
    log_approval_audit,
    log_correction_audit
)


class TestLogAuditEntry:
    """Tests for log_audit_entry function."""
    
    @patch('shared.audit.get_lambda_client')
    def test_log_audit_entry_async(self, mock_get_lambda_client):
        """Test async audit entry logging."""
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        mock_get_lambda_client.return_value = mock_lambda_client
        
        result = log_audit_entry(
            user_id='user123',
            action_type='classification',
            async_invoke=True
        )
        
        assert result is None
        mock_lambda_client.invoke.assert_called_once()
        call_args = mock_lambda_client.invoke.call_args
        assert call_args.kwargs['InvocationType'] == 'Event'
    
    @patch('shared.audit.get_lambda_client')
    def test_log_audit_entry_sync(self, mock_get_lambda_client):
        """Test synchronous audit entry logging."""
        mock_lambda_client = Mock()
        mock_response = {
            'Payload': Mock(read=lambda: json.dumps({
                'status': 'success',
                'action_id': 'audit_123',
                'timestamp': '2024-01-15T10:30:00Z'
            }).encode())
        }
        mock_lambda_client.invoke.return_value = mock_response
        mock_get_lambda_client.return_value = mock_lambda_client
        
        result = log_audit_entry(
            user_id='user123',
            action_type='classification',
            async_invoke=False
        )
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['action_id'] == 'audit_123'
        
        call_args = mock_lambda_client.invoke.call_args
        assert call_args.kwargs['InvocationType'] == 'RequestResponse'
    
    @patch('shared.audit.get_lambda_client')
    def test_log_audit_entry_with_details(self, mock_get_lambda_client):
        """Test logging with action details."""
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        mock_get_lambda_client.return_value = mock_lambda_client
        
        log_audit_entry(
            user_id='user123',
            action_type='classification',
            actor='ai',
            actor_details='bedrock:claude-3-haiku',
            subject_type='transaction',
            subject_id='txn_456',
            action_details={'confidence': 0.95, 'category': 'Office Supplies'},
            result='success'
        )
        
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args.kwargs['Payload'])
        
        assert payload['user_id'] == 'user123'
        assert payload['action_type'] == 'classification'
        assert payload['actor'] == 'ai'
        assert payload['actor_details'] == 'bedrock:claude-3-haiku'
        assert payload['subject_type'] == 'transaction'
        assert payload['subject_id'] == 'txn_456'
        assert payload['action_details']['confidence'] == 0.95
        assert payload['result'] == 'success'
    
    @patch('shared.audit.get_lambda_client')
    def test_log_audit_entry_error_handling(self, mock_get_lambda_client):
        """Test error handling when Lambda invocation fails."""
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.side_effect = Exception("Lambda error")
        mock_get_lambda_client.return_value = mock_lambda_client
        
        # Should not raise exception
        result = log_audit_entry(
            user_id='user123',
            action_type='classification'
        )
        
        assert result is None


class TestClassificationAudit:
    """Tests for log_classification_audit function."""
    
    @patch('shared.audit.get_lambda_client')
    def test_log_classification_audit(self, mock_get_lambda_client):
        """Test classification audit logging."""
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        mock_get_lambda_client.return_value = mock_lambda_client
        
        log_classification_audit(
            user_id='user123',
            transaction_id='txn_456',
            category='Office Supplies',
            confidence=0.92,
            reasoning='Vendor name indicates office supplies'
        )
        
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args.kwargs['Payload'])
        
        assert payload['action_type'] == 'classification'
        assert payload['actor'] == 'ai'
        assert payload['subject_type'] == 'transaction'
        assert payload['subject_id'] == 'txn_456'
        assert payload['action_details']['category'] == 'Office Supplies'
        assert payload['action_details']['confidence'] == 0.92
        assert payload['action_details']['reasoning'] == 'Vendor name indicates office supplies'


class TestReconciliationAudit:
    """Tests for log_reconciliation_audit function."""
    
    @patch('shared.audit.get_lambda_client')
    def test_log_reconciliation_audit(self, mock_get_lambda_client):
        """Test reconciliation audit logging."""
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        mock_get_lambda_client.return_value = mock_lambda_client
        
        log_reconciliation_audit(
            user_id='user123',
            transaction_id='txn_456',
            bank_transaction_id='bank_txn_789',
            match_confidence=0.85,
            match_status='auto_linked'
        )
        
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args.kwargs['Payload'])
        
        assert payload['action_type'] == 'reconciliation'
        assert payload['actor'] == 'ai'
        assert payload['subject_type'] == 'transaction'
        assert payload['subject_id'] == 'txn_456'
        assert payload['action_details']['bank_transaction_id'] == 'bank_txn_789'
        assert payload['action_details']['match_confidence'] == 0.85
        assert payload['action_details']['match_status'] == 'auto_linked'


class TestAssistantQueryAudit:
    """Tests for log_assistant_query_audit function."""
    
    @patch('shared.audit.get_lambda_client')
    def test_log_assistant_query_audit(self, mock_get_lambda_client):
        """Test assistant query audit logging."""
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        mock_get_lambda_client.return_value = mock_lambda_client
        
        log_assistant_query_audit(
            user_id='user123',
            question='Can I afford to hire a new employee?',
            answer='Based on your current cash flow...',
            confidence=0.85,
            citations=['txn_1', 'txn_2']
        )
        
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args.kwargs['Payload'])
        
        assert payload['action_type'] == 'assistant_query'
        assert payload['actor'] == 'ai'
        assert payload['subject_type'] == 'conversation'
        assert payload['action_details']['question'] == 'Can I afford to hire a new employee?'
        assert payload['action_details']['confidence'] == 0.85
        assert payload['action_details']['citations'] == ['txn_1', 'txn_2']
    
    @patch('shared.audit.get_lambda_client')
    def test_log_assistant_query_truncates_long_answer(self, mock_get_lambda_client):
        """Test that long answers are truncated."""
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        mock_get_lambda_client.return_value = mock_lambda_client
        
        long_answer = 'A' * 1000
        
        log_assistant_query_audit(
            user_id='user123',
            question='Test question',
            answer=long_answer,
            confidence=0.85,
            citations=[]
        )
        
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args.kwargs['Payload'])
        
        # Answer should be truncated to 500 characters
        assert len(payload['action_details']['answer']) == 500


class TestApprovalAudit:
    """Tests for log_approval_audit function."""
    
    @patch('shared.audit.get_lambda_client')
    def test_log_approval_audit(self, mock_get_lambda_client):
        """Test approval audit logging."""
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        mock_get_lambda_client.return_value = mock_lambda_client
        
        log_approval_audit(
            user_id='user123',
            subject_type='transaction',
            subject_id='txn_456',
            approval_action='approved',
            details={'reason': 'Verified with receipt'}
        )
        
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args.kwargs['Payload'])
        
        assert payload['action_type'] == 'approval'
        assert payload['actor'] == 'user'
        assert payload['actor_details'] == 'user123'
        assert payload['subject_type'] == 'transaction'
        assert payload['subject_id'] == 'txn_456'
        assert payload['action_details']['reason'] == 'Verified with receipt'


class TestCorrectionAudit:
    """Tests for log_correction_audit function."""
    
    @patch('shared.audit.get_lambda_client')
    def test_log_correction_audit(self, mock_get_lambda_client):
        """Test correction audit logging."""
        mock_lambda_client = Mock()
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        mock_get_lambda_client.return_value = mock_lambda_client
        
        log_correction_audit(
            user_id='user123',
            transaction_id='txn_456',
            original_category='Office Supplies',
            corrected_category='Marketing',
            original_confidence=0.75
        )
        
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args.kwargs['Payload'])
        
        assert payload['action_type'] == 'correction'
        assert payload['actor'] == 'user'
        assert payload['subject_type'] == 'transaction'
        assert payload['subject_id'] == 'txn_456'
        assert payload['action_details']['original_category'] == 'Office Supplies'
        assert payload['action_details']['corrected_category'] == 'Marketing'
        assert payload['action_details']['original_confidence'] == 0.75
