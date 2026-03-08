"""
Unit tests for audit trail API Lambda function.
"""

import pytest
import json
import csv
import io
from unittest.mock import Mock, patch
from src.lambdas.audit_trail_api.handler import (
    lambda_handler,
    lambda_handler_export,
    parse_query_parameters,
    query_audit_entries,
    export_audit_trail_csv,
    format_audit_entries_as_csv
)
from src.shared.entities import AuditEntry
from src.shared.exceptions import ValidationError, AuthenticationError


@pytest.fixture
def mock_context():
    """Mock Lambda context."""
    context = Mock()
    context.request_id = 'test-request-id'
    return context


@pytest.fixture
def api_gateway_event():
    """Mock API Gateway event."""
    return {
        'headers': {
            'Authorization': 'Bearer test-token'
        },
        'queryStringParameters': {},
        'requestContext': {
            'requestId': 'test-request-id'
        }
    }


@pytest.fixture
def sample_audit_entries():
    """Create sample audit entries for testing."""
    return [
        AuditEntry(
            user_id='test-user',
            action_id='audit_001',
            timestamp='2024-01-15T10:00:00Z',
            action_type='classification',
            actor='ai',
            subject_type='transaction',
            subject_id='txn_001',
            result='success',
            actor_details='bedrock:claude-3-haiku',
            action_details={
                'category': 'Office Supplies',
                'confidence': 0.92,
                'reasoning': 'Vendor name indicates office supplies'
            }
        ),
        AuditEntry(
            user_id='test-user',
            action_id='audit_002',
            timestamp='2024-01-15T11:00:00Z',
            action_type='reconciliation',
            actor='ai',
            subject_type='transaction',
            subject_id='txn_002',
            result='success',
            actor_details='reconciliation-engine',
            action_details={
                'matched_bank_transaction': 'bank_001',
                'confidence': 0.95
            }
        ),
        AuditEntry(
            user_id='test-user',
            action_id='audit_003',
            timestamp='2024-01-15T12:00:00Z',
            action_type='approval',
            actor='user',
            subject_type='transaction',
            subject_id='txn_001',
            result='approved',
            actor_details='user:test-user',
            action_details={
                'action': 'approved',
                'comment': 'Looks good'
            }
        ),
        AuditEntry(
            user_id='test-user',
            action_id='audit_004',
            timestamp='2024-01-16T10:00:00Z',
            action_type='classification',
            actor='ai',
            subject_type='transaction',
            subject_id='txn_003',
            result='success',
            actor_details='bedrock:claude-3-haiku',
            action_details={
                'category': 'Utilities',
                'confidence': 0.88,
                'reasoning': 'Utility company vendor'
            }
        ),
    ]


def test_parse_query_parameters_default():
    """Test parsing query parameters with defaults."""
    event = {'queryStringParameters': None}
    
    params = parse_query_parameters(event)
    
    assert params['start_date'] is None
    assert params['end_date'] is None
    assert params['action_type'] is None
    assert params['transaction_id'] is None
    assert params['limit'] == 50
    assert params['last_evaluated_key'] is None


def test_parse_query_parameters_with_filters():
    """Test parsing query parameters with filters."""
    event = {
        'queryStringParameters': {
            'start_date': '2024-01-15T00:00:00Z',
            'end_date': '2024-01-16T23:59:59Z',
            'action_type': 'classification',
            'transaction_id': 'txn_001',
            'limit': '25'
        }
    }
    
    params = parse_query_parameters(event)
    
    assert params['start_date'] == '2024-01-15T00:00:00Z'
    assert params['end_date'] == '2024-01-16T23:59:59Z'
    assert params['action_type'] == 'classification'
    assert params['transaction_id'] == 'txn_001'
    assert params['limit'] == 25


def test_parse_query_parameters_limit_cap():
    """Test that limit is capped at 100."""
    event = {
        'queryStringParameters': {
            'limit': '200'
        }
    }
    
    params = parse_query_parameters(event)
    
    assert params['limit'] == 100


def test_parse_query_parameters_invalid_limit():
    """Test parsing with invalid limit."""
    event = {
        'queryStringParameters': {
            'limit': 'invalid'
        }
    }
    
    with pytest.raises(ValidationError):
        parse_query_parameters(event)


def test_parse_query_parameters_negative_limit():
    """Test parsing with negative limit."""
    event = {
        'queryStringParameters': {
            'limit': '-5'
        }
    }
    
    with pytest.raises(ValidationError):
        parse_query_parameters(event)


def test_query_audit_entries_no_filters(sample_audit_entries):
    """Test querying audit entries without filters."""
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = sample_audit_entries
    
    result = query_audit_entries(
        user_id='test-user',
        repository=mock_repo,
        limit=50
    )
    
    assert len(result['audit_entries']) == 4
    assert result['pagination']['limit'] == 50
    
    # Verify repository was called correctly
    mock_repo.query_audit_entries.assert_called_once_with(
        user_id='test-user',
        start_timestamp=None,
        end_timestamp=None,
        action_type=None,
        limit=50
    )


def test_query_audit_entries_with_date_range(sample_audit_entries):
    """Test querying audit entries with date range filter."""
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = sample_audit_entries[:3]
    
    result = query_audit_entries(
        user_id='test-user',
        repository=mock_repo,
        start_date='2024-01-15T00:00:00Z',
        end_date='2024-01-15T23:59:59Z',
        limit=50
    )
    
    assert len(result['audit_entries']) == 3
    
    # Verify repository was called with date filters
    mock_repo.query_audit_entries.assert_called_once_with(
        user_id='test-user',
        start_timestamp='2024-01-15T00:00:00Z',
        end_timestamp='2024-01-15T23:59:59Z',
        action_type=None,
        limit=50
    )


def test_query_audit_entries_with_action_type(sample_audit_entries):
    """Test querying audit entries with action type filter."""
    classification_entries = [e for e in sample_audit_entries if e.action_type == 'classification']
    
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = classification_entries
    
    result = query_audit_entries(
        user_id='test-user',
        repository=mock_repo,
        action_type='classification',
        limit=50
    )
    
    assert len(result['audit_entries']) == 2
    
    # All returned entries should be classification type
    for entry in result['audit_entries']:
        assert entry['action_type'] == 'classification'
    
    # Verify repository was called with action type filter
    mock_repo.query_audit_entries.assert_called_once_with(
        user_id='test-user',
        start_timestamp=None,
        end_timestamp=None,
        action_type='classification',
        limit=50
    )


def test_query_audit_entries_with_transaction_id(sample_audit_entries):
    """Test querying audit entries with transaction ID filter."""
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = sample_audit_entries
    
    result = query_audit_entries(
        user_id='test-user',
        repository=mock_repo,
        transaction_id='txn_001',
        limit=50
    )
    
    # Should only return entries for txn_001
    assert len(result['audit_entries']) == 2
    for entry in result['audit_entries']:
        assert entry['subject_id'] == 'txn_001'


def test_query_audit_entries_with_all_filters(sample_audit_entries):
    """Test querying audit entries with all filters."""
    classification_entries = [sample_audit_entries[0]]
    
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = classification_entries
    
    result = query_audit_entries(
        user_id='test-user',
        repository=mock_repo,
        start_date='2024-01-15T00:00:00Z',
        end_date='2024-01-15T23:59:59Z',
        action_type='classification',
        transaction_id='txn_001',
        limit=25
    )
    
    # Should return only entries matching all filters
    assert len(result['audit_entries']) == 1
    assert result['audit_entries'][0]['action_id'] == 'audit_001'
    assert result['audit_entries'][0]['action_type'] == 'classification'
    assert result['audit_entries'][0]['subject_id'] == 'txn_001'


def test_query_audit_entries_pagination_token(sample_audit_entries):
    """Test that pagination token is generated when limit is reached."""
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = sample_audit_entries[:2]
    
    result = query_audit_entries(
        user_id='test-user',
        repository=mock_repo,
        limit=2
    )
    
    # Should have pagination token since we got exactly the limit
    assert 'last_evaluated_key' in result['pagination']
    assert result['pagination']['last_evaluated_key'] is not None


def test_query_audit_entries_no_pagination_token(sample_audit_entries):
    """Test that no pagination token is generated when results are less than limit."""
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = sample_audit_entries[:2]
    
    result = query_audit_entries(
        user_id='test-user',
        repository=mock_repo,
        limit=50
    )
    
    # Should not have pagination token since we got less than the limit
    assert 'last_evaluated_key' not in result['pagination']


def test_query_audit_entries_response_format(sample_audit_entries):
    """Test that audit entries are formatted correctly in response."""
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = [sample_audit_entries[0]]
    
    result = query_audit_entries(
        user_id='test-user',
        repository=mock_repo,
        limit=50
    )
    
    entry = result['audit_entries'][0]
    
    # Check required fields
    assert 'action_id' in entry
    assert 'timestamp' in entry
    assert 'action_type' in entry
    assert 'actor' in entry
    assert 'subject_type' in entry
    assert 'subject_id' in entry
    assert 'result' in entry
    
    # Check optional fields
    assert 'actor_details' in entry
    assert 'action_details' in entry


def test_lambda_handler_success(api_gateway_event, mock_context, sample_audit_entries):
    """Test successful Lambda handler execution."""
    with patch('src.lambdas.audit_trail_api.handler.extract_token_from_event') as mock_extract_token, \
         patch('src.lambdas.audit_trail_api.handler.get_user_id_from_token') as mock_get_user_id, \
         patch('src.lambdas.audit_trail_api.handler.get_repository') as mock_get_repo:
        
        mock_extract_token.return_value = 'test-token'
        mock_get_user_id.return_value = 'test-user'
        
        mock_repo = Mock()
        mock_repo.query_audit_entries.return_value = sample_audit_entries
        mock_get_repo.return_value = mock_repo
        
        response = lambda_handler(api_gateway_event, mock_context)
        
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['status'] == 'success'
        assert 'data' in body
        assert 'audit_entries' in body['data']
        assert 'pagination' in body['data']


def test_lambda_handler_with_filters(api_gateway_event, mock_context, sample_audit_entries):
    """Test Lambda handler with query filters."""
    api_gateway_event['queryStringParameters'] = {
        'start_date': '2024-01-15T00:00:00Z',
        'end_date': '2024-01-16T23:59:59Z',
        'action_type': 'classification',
        'limit': '10'
    }
    
    with patch('src.lambdas.audit_trail_api.handler.extract_token_from_event') as mock_extract_token, \
         patch('src.lambdas.audit_trail_api.handler.get_user_id_from_token') as mock_get_user_id, \
         patch('src.lambdas.audit_trail_api.handler.get_repository') as mock_get_repo:
        
        mock_extract_token.return_value = 'test-token'
        mock_get_user_id.return_value = 'test-user'
        
        mock_repo = Mock()
        mock_repo.query_audit_entries.return_value = [sample_audit_entries[0]]
        mock_get_repo.return_value = mock_repo
        
        response = lambda_handler(api_gateway_event, mock_context)
        
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert len(body['data']['audit_entries']) == 1


def test_lambda_handler_authentication_error(api_gateway_event, mock_context):
    """Test Lambda handler with authentication error."""
    with patch('src.lambdas.audit_trail_api.handler.extract_token_from_event') as mock_extract_token:
        mock_extract_token.side_effect = AuthenticationError('Invalid token')
        
        response = lambda_handler(api_gateway_event, mock_context)
        
        # Should return an error response (either 401 or 500 depending on how exception is caught)
        assert response['statusCode'] in [401, 500]
        body = json.loads(response['body'])
        assert 'error' in body


def test_lambda_handler_validation_error(api_gateway_event, mock_context):
    """Test Lambda handler with validation error."""
    api_gateway_event['queryStringParameters'] = {
        'limit': 'invalid'
    }
    
    with patch('src.lambdas.audit_trail_api.handler.extract_token_from_event') as mock_extract_token, \
         patch('src.lambdas.audit_trail_api.handler.get_user_id_from_token') as mock_get_user_id:
        
        mock_extract_token.return_value = 'test-token'
        mock_get_user_id.return_value = 'test-user'
        
        response = lambda_handler(api_gateway_event, mock_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body


def test_lambda_handler_internal_error(api_gateway_event, mock_context):
    """Test Lambda handler with internal error."""
    with patch('src.lambdas.audit_trail_api.handler.extract_token_from_event') as mock_extract_token, \
         patch('src.lambdas.audit_trail_api.handler.get_user_id_from_token') as mock_get_user_id, \
         patch('src.lambdas.audit_trail_api.handler.get_repository') as mock_get_repo:
        
        mock_extract_token.return_value = 'test-token'
        mock_get_user_id.return_value = 'test-user'
        
        mock_repo = Mock()
        mock_repo.query_audit_entries.side_effect = Exception('Database error')
        mock_get_repo.return_value = mock_repo
        
        response = lambda_handler(api_gateway_event, mock_context)
        
        assert response['statusCode'] == 500


def test_empty_audit_trail():
    """Test querying with no audit entries."""
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = []
    
    result = query_audit_entries(
        user_id='test-user',
        repository=mock_repo,
        limit=50
    )
    
    assert len(result['audit_entries']) == 0
    assert result['pagination']['limit'] == 50
    assert 'last_evaluated_key' not in result['pagination']


def test_format_audit_entries_as_csv(sample_audit_entries):
    """Test formatting audit entries as CSV."""
    csv_content = format_audit_entries_as_csv(sample_audit_entries)
    
    # Parse CSV to verify format
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    # Should have same number of rows as entries
    assert len(rows) == 4
    
    # Check headers
    assert csv_reader.fieldnames == [
        'timestamp',
        'action_type',
        'actor',
        'subject_type',
        'subject_id',
        'result',
        'actor_details',
        'action_details'
    ]
    
    # Check first row content
    first_row = rows[0]
    assert first_row['timestamp'] == '2024-01-15T10:00:00Z'
    assert first_row['action_type'] == 'classification'
    assert first_row['actor'] == 'ai'
    assert first_row['subject_type'] == 'transaction'
    assert first_row['subject_id'] == 'txn_001'
    assert first_row['result'] == 'success'
    assert first_row['actor_details'] == 'bedrock:claude-3-haiku'
    
    # Check action_details is JSON string
    action_details = json.loads(first_row['action_details'])
    assert action_details['category'] == 'Office Supplies'
    assert action_details['confidence'] == 0.92


def test_format_audit_entries_as_csv_empty():
    """Test formatting empty audit entries list as CSV."""
    csv_content = format_audit_entries_as_csv([])
    
    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    # Should have headers but no data rows
    assert len(rows) == 0
    assert csv_reader.fieldnames == [
        'timestamp',
        'action_type',
        'actor',
        'subject_type',
        'subject_id',
        'result',
        'actor_details',
        'action_details'
    ]


def test_format_audit_entries_as_csv_with_none_fields(sample_audit_entries):
    """Test formatting audit entries with None optional fields."""
    # Create entry with None optional fields
    entry = AuditEntry(
        user_id='test-user',
        action_id='audit_005',
        timestamp='2024-01-17T10:00:00Z',
        action_type='data_access',
        actor='user',
        subject_type='document',
        subject_id='doc_001',
        result='success',
        actor_details=None,
        action_details=None
    )
    
    csv_content = format_audit_entries_as_csv([entry])
    
    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    assert len(rows) == 1
    assert rows[0]['actor_details'] == ''
    assert rows[0]['action_details'] == ''


def test_export_audit_trail_csv(sample_audit_entries):
    """Test exporting all audit entries as CSV."""
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = sample_audit_entries
    
    csv_content = export_audit_trail_csv('test-user', mock_repo)
    
    # Verify repository was called with no limit
    mock_repo.query_audit_entries.assert_called_once_with(
        user_id='test-user',
        start_timestamp=None,
        end_timestamp=None,
        action_type=None,
        limit=None
    )
    
    # Verify CSV content
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    assert len(rows) == 4


def test_export_audit_trail_csv_empty():
    """Test exporting empty audit trail as CSV."""
    mock_repo = Mock()
    mock_repo.query_audit_entries.return_value = []
    
    csv_content = export_audit_trail_csv('test-user', mock_repo)
    
    # Should still have headers
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    assert len(rows) == 0
    assert csv_reader.fieldnames is not None


def test_lambda_handler_export_success(api_gateway_event, mock_context, sample_audit_entries):
    """Test successful CSV export Lambda handler execution."""
    with patch('src.lambdas.audit_trail_api.handler.extract_token_from_event') as mock_extract_token, \
         patch('src.lambdas.audit_trail_api.handler.get_user_id_from_token') as mock_get_user_id, \
         patch('src.lambdas.audit_trail_api.handler.get_repository') as mock_get_repo:
        
        mock_extract_token.return_value = 'test-token'
        mock_get_user_id.return_value = 'test-user'
        
        mock_repo = Mock()
        mock_repo.query_audit_entries.return_value = sample_audit_entries
        mock_get_repo.return_value = mock_repo
        
        response = lambda_handler_export(api_gateway_event, mock_context)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/csv'
        assert response['headers']['Content-Disposition'] == 'attachment; filename="audit_trail.csv"'
        assert 'Access-Control-Allow-Origin' in response['headers']
        
        # Verify CSV content
        csv_content = response['body']
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        assert len(rows) == 4


def test_lambda_handler_export_authentication_error(api_gateway_event, mock_context):
    """Test CSV export Lambda handler with authentication error."""
    with patch('src.lambdas.audit_trail_api.handler.extract_token_from_event') as mock_extract_token:
        mock_extract_token.side_effect = AuthenticationError('Invalid token')
        
        response = lambda_handler_export(api_gateway_event, mock_context)
        
        assert response['statusCode'] in [401, 500]
        body = json.loads(response['body'])
        assert 'error' in body


def test_lambda_handler_export_internal_error(api_gateway_event, mock_context):
    """Test CSV export Lambda handler with internal error."""
    with patch('src.lambdas.audit_trail_api.handler.extract_token_from_event') as mock_extract_token, \
         patch('src.lambdas.audit_trail_api.handler.get_user_id_from_token') as mock_get_user_id, \
         patch('src.lambdas.audit_trail_api.handler.get_repository') as mock_get_repo:
        
        mock_extract_token.return_value = 'test-token'
        mock_get_user_id.return_value = 'test-user'
        
        mock_repo = Mock()
        mock_repo.query_audit_entries.side_effect = Exception('Database error')
        mock_get_repo.return_value = mock_repo
        
        response = lambda_handler_export(api_gateway_event, mock_context)
        
        assert response['statusCode'] == 500


def test_csv_export_special_characters(sample_audit_entries):
    """Test CSV export handles special characters correctly."""
    # Create entry with special characters
    entry = AuditEntry(
        user_id='test-user',
        action_id='audit_006',
        timestamp='2024-01-18T10:00:00Z',
        action_type='classification',
        actor='ai',
        subject_type='transaction',
        subject_id='txn_004',
        result='success',
        actor_details='bedrock:claude-3-haiku',
        action_details={
            'vendor': 'Company, Inc.',
            'description': 'Item with "quotes" and commas, etc.',
            'note': 'Line 1\nLine 2'
        }
    )
    
    csv_content = format_audit_entries_as_csv([entry])
    
    # Parse CSV - should handle special characters correctly
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    assert len(rows) == 1
    action_details = json.loads(rows[0]['action_details'])
    assert action_details['vendor'] == 'Company, Inc.'
    assert action_details['description'] == 'Item with "quotes" and commas, etc.'
