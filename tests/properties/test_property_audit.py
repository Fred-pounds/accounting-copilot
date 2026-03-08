"""
Property-based tests for audit trail functionality.
"""

import pytest
from hypothesis import given, settings, strategies as st
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from lambdas.audit_logger.handler import create_audit_entry, log_single_entry, log_batch_entries


# Strategies for generating test data
action_types = st.sampled_from([
    'classification', 'reconciliation', 'assistant_query',
    'approval', 'correction', 'data_access'
])

actors = st.sampled_from(['ai', 'user'])

user_ids = st.text(min_size=1, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48, max_codepoint=122
))

subject_types = st.sampled_from(['transaction', 'document', 'conversation', 'vendor', ''])

confidence_scores = st.floats(min_value=0.0, max_value=1.0)


@settings(max_examples=100)
@given(
    user_id=user_ids,
    action_type=action_types,
    actor=actors,
    subject_type=subject_types,
    confidence=confidence_scores
)
def test_property_audit_entry_structure(user_id, action_type, actor, subject_type, confidence):
    """
    **Validates: Requirements 2.6, 4.6, 6.6, 7.1, 7.2, 7.3, 10.6**
    
    Property 19: Comprehensive Audit Trail
    For any AI or human action, system should create audit trail entry with required fields.
    """
    # Create audit entry
    audit_entry = create_audit_entry(
        user_id=user_id,
        action_type=action_type,
        actor=actor,
        subject_type=subject_type,
        subject_id='test_subject_123',
        action_details={'confidence': confidence}
    )
    
    # Verify required fields are present
    assert 'PK' in audit_entry
    assert 'SK' in audit_entry
    assert 'entity_type' in audit_entry
    assert 'action_id' in audit_entry
    assert 'timestamp' in audit_entry
    assert 'action_type' in audit_entry
    assert 'actor' in audit_entry
    
    # Verify field values
    assert audit_entry['PK'] == f"USER#{user_id}"
    assert audit_entry['SK'].startswith('AUDIT#')
    assert audit_entry['entity_type'] == 'audit_entry'
    assert audit_entry['action_type'] == action_type
    assert audit_entry['actor'] == actor
    assert audit_entry['subject_type'] == subject_type
    
    # Verify action_details contains confidence if AI action
    if actor == 'ai':
        assert 'confidence' in audit_entry['action_details']
        assert audit_entry['action_details']['confidence'] == confidence


@settings(max_examples=100)
@given(
    user_id=user_ids,
    action_type=action_types,
    confidence=confidence_scores
)
def test_property_ai_action_includes_confidence(user_id, action_type, confidence):
    """
    **Validates: Requirements 7.1, 7.2**
    
    Property: AI actions should include confidence scores in audit details.
    """
    # Create audit entry for AI action
    audit_entry = create_audit_entry(
        user_id=user_id,
        action_type=action_type,
        actor='ai',
        action_details={'confidence': confidence, 'reasoning': 'test reasoning'}
    )
    
    # Verify confidence is included
    assert 'action_details' in audit_entry
    assert 'confidence' in audit_entry['action_details']
    assert 0.0 <= audit_entry['action_details']['confidence'] <= 1.0


@settings(max_examples=100)
@given(
    user_id=user_ids,
    action_type=action_types
)
@patch('lambdas.audit_logger.handler.get_dynamodb_table')
def test_property_single_entry_logging(mock_get_table, user_id, action_type):
    """
    **Validates: Requirements 7.1, 7.2, 7.3**
    
    Property: Single audit entry logging should succeed and return action_id.
    """
    # Mock DynamoDB table
    mock_table = Mock()
    mock_get_table.return_value = mock_table
    
    # Create event
    event = {
        'user_id': user_id,
        'action_type': action_type,
        'actor': 'ai',
        'subject_type': 'transaction',
        'subject_id': 'txn_123'
    }
    
    # Log entry
    result = log_single_entry(event)
    
    # Verify result
    assert result['status'] == 'success'
    assert 'action_id' in result
    assert 'timestamp' in result
    assert result['action_id'].startswith('audit_')
    
    # Verify DynamoDB was called
    mock_table.put_item.assert_called_once()


@settings(max_examples=50)
@given(
    user_id=user_ids,
    batch_size=st.integers(min_value=1, max_value=30)
)
@patch('lambdas.audit_logger.handler.get_dynamodb_table')
def test_property_batch_entry_logging(mock_get_table, user_id, batch_size):
    """
    **Validates: Requirements 7.1, 7.2, 7.3**
    
    Property: Batch audit entry logging should handle multiple entries efficiently.
    """
    # Mock DynamoDB table with batch writer
    mock_table = Mock()
    mock_batch_writer = MagicMock()
    mock_table.batch_writer = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=mock_batch_writer), __exit__=MagicMock()))
    mock_get_table.return_value = mock_table
    
    # Create batch of entries
    entries = []
    for i in range(batch_size):
        entries.append({
            'user_id': user_id,
            'action_type': 'classification',
            'actor': 'ai',
            'subject_type': 'transaction',
            'subject_id': f'txn_{i}'
        })
    
    # Log batch
    result = log_batch_entries(entries)
    
    # Verify result
    assert result['status'] == 'success'
    assert result['entries_logged'] == batch_size
    
    # Verify batch writer was used
    assert mock_batch_writer.put_item.call_count == batch_size


@settings(max_examples=100)
@given(
    user_id=user_ids,
    action_type=action_types
)
def test_property_timestamp_format(user_id, action_type):
    """
    **Validates: Requirements 7.1**
    
    Property: Audit entries should have valid ISO 8601 timestamps.
    """
    # Create audit entry
    audit_entry = create_audit_entry(
        user_id=user_id,
        action_type=action_type
    )
    
    # Verify timestamp format
    timestamp = audit_entry['timestamp']
    assert isinstance(timestamp, str)
    assert timestamp.endswith('Z')
    
    # Should be parseable as ISO 8601
    try:
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed is not None
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {timestamp}")


@settings(max_examples=100)
@given(
    user_id=user_ids,
    action_type=action_types,
    result=st.sampled_from(['success', 'error', 'pending'])
)
def test_property_result_field(user_id, action_type, result):
    """
    **Validates: Requirements 7.1, 7.2, 7.3**
    
    Property: Audit entries should record the result of the action.
    """
    # Create audit entry
    audit_entry = create_audit_entry(
        user_id=user_id,
        action_type=action_type,
        result=result
    )
    
    # Verify result field
    assert 'result' in audit_entry
    assert audit_entry['result'] == result


@settings(max_examples=100)
@given(
    user_id=user_ids,
    category=st.text(min_size=1, max_size=50),
    confidence=confidence_scores,
    reasoning=st.text(min_size=1, max_size=200)
)
def test_property_classification_audit_details(user_id, category, confidence, reasoning):
    """
    **Validates: Requirements 2.6, 7.1**
    
    Property: Classification audit entries should include category, confidence, and reasoning.
    """
    # Create classification audit entry
    audit_entry = create_audit_entry(
        user_id=user_id,
        action_type='classification',
        actor='ai',
        subject_type='transaction',
        subject_id='txn_123',
        action_details={
            'category': category,
            'confidence': confidence,
            'reasoning': reasoning
        }
    )
    
    # Verify classification details
    details = audit_entry['action_details']
    assert 'category' in details
    assert 'confidence' in details
    assert 'reasoning' in details
    assert details['category'] == category
    assert details['confidence'] == confidence
    assert details['reasoning'] == reasoning


@settings(max_examples=100)
@given(
    user_id=user_ids,
    match_confidence=confidence_scores,
    match_status=st.sampled_from(['auto_linked', 'pending_approval', 'no_match'])
)
def test_property_reconciliation_audit_details(user_id, match_confidence, match_status):
    """
    **Validates: Requirements 4.6, 7.2**
    
    Property: Reconciliation audit entries should include match confidence and status.
    """
    # Create reconciliation audit entry
    audit_entry = create_audit_entry(
        user_id=user_id,
        action_type='reconciliation',
        actor='ai',
        subject_type='transaction',
        subject_id='txn_123',
        action_details={
            'bank_transaction_id': 'bank_txn_456',
            'match_confidence': match_confidence,
            'match_status': match_status
        }
    )
    
    # Verify reconciliation details
    details = audit_entry['action_details']
    assert 'bank_transaction_id' in details
    assert 'match_confidence' in details
    assert 'match_status' in details
    assert details['match_confidence'] == match_confidence
    assert details['match_status'] == match_status


@settings(max_examples=100)
@given(
    user_id=user_ids,
    question=st.text(min_size=1, max_size=200),
    answer=st.text(min_size=1, max_size=500),
    confidence=confidence_scores
)
def test_property_assistant_query_audit_details(user_id, question, answer, confidence):
    """
    **Validates: Requirements 6.6, 7.2**
    
    Property: Assistant query audit entries should include question, answer, and confidence.
    """
    # Create assistant query audit entry
    audit_entry = create_audit_entry(
        user_id=user_id,
        action_type='assistant_query',
        actor='ai',
        subject_type='conversation',
        action_details={
            'question': question,
            'answer': answer,
            'confidence': confidence,
            'citations': ['txn_1', 'txn_2']
        }
    )
    
    # Verify assistant query details
    details = audit_entry['action_details']
    assert 'question' in details
    assert 'answer' in details
    assert 'confidence' in details
    assert 'citations' in details
    assert details['question'] == question
    assert details['answer'] == answer
    assert details['confidence'] == confidence


@settings(max_examples=100)
@given(
    user_id=user_ids,
    subject_type=subject_types,
    subject_id=st.text(min_size=1, max_size=50)
)
def test_property_unique_audit_ids(user_id, subject_type, subject_id):
    """
    **Validates: Requirements 7.1**
    
    Property: Each audit entry should have a unique action_id.
    """
    # Create multiple audit entries
    entries = []
    for _ in range(10):
        entry = create_audit_entry(
            user_id=user_id,
            action_type='classification',
            subject_type=subject_type,
            subject_id=subject_id
        )
        entries.append(entry['action_id'])
    
    # Verify all IDs are unique
    assert len(entries) == len(set(entries))


@settings(max_examples=100)
@given(
    user_id=user_ids,
    action_type=action_types
)
def test_property_sort_key_format(user_id, action_type):
    """
    **Validates: Requirements 7.1, 7.4**
    
    Property: Audit entry sort keys should enable chronological ordering.
    """
    # Create audit entry
    audit_entry = create_audit_entry(
        user_id=user_id,
        action_type=action_type
    )
    
    # Verify sort key format
    sk = audit_entry['SK']
    assert sk.startswith('AUDIT#')
    
    # Should contain timestamp and action_id
    parts = sk.split('#')
    assert len(parts) == 3
    assert parts[0] == 'AUDIT'
    
    # Timestamp part should be ISO 8601 format
    timestamp_part = parts[1]
    try:
        datetime.fromisoformat(timestamp_part.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Invalid timestamp in sort key: {timestamp_part}")
