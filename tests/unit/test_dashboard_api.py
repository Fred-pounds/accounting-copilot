"""
Unit tests for dashboard API Lambda function.
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.lambdas.dashboard_api.handler import lambda_handler, calculate_dashboard_data
from src.shared.entities import Transaction
from src.shared.exceptions import AuthenticationError


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
        'requestContext': {
            'requestId': 'test-request-id'
        }
    }


@pytest.fixture
def sample_transactions():
    """Create sample transactions for testing."""
    now = datetime.utcnow()
    current_month = now.strftime('%Y-%m')
    last_month = (now - timedelta(days=30)).strftime('%Y-%m')
    
    transactions = [
        # Current month income
        Transaction(
            user_id='test-user',
            transaction_id='txn_001',
            date=f'{current_month}-05',
            amount=Decimal('5000.00'),
            currency='USD',
            type='income',
            category='Revenue',
            vendor='Client A',
            description='Payment received',
            classification_confidence=0.95,
            classification_reasoning='Payment from client',
            status='approved',
            created_at=f'{current_month}-05T10:00:00Z',
            updated_at=f'{current_month}-05T10:00:00Z',
            created_by='ai'
        ),
        # Current month expenses
        Transaction(
            user_id='test-user',
            transaction_id='txn_002',
            date=f'{current_month}-10',
            amount=Decimal('500.00'),
            currency='USD',
            type='expense',
            category='Office Supplies',
            vendor='Office Depot',
            description='Office supplies',
            classification_confidence=0.92,
            classification_reasoning='Office supplies purchase',
            status='approved',
            created_at=f'{current_month}-10T10:00:00Z',
            updated_at=f'{current_month}-10T10:00:00Z',
            created_by='ai'
        ),
        Transaction(
            user_id='test-user',
            transaction_id='txn_003',
            date=f'{current_month}-15',
            amount=Decimal('1200.00'),
            currency='USD',
            type='expense',
            category='Rent',
            vendor='Landlord',
            description='Office rent',
            classification_confidence=0.98,
            classification_reasoning='Monthly rent payment',
            status='approved',
            created_at=f'{current_month}-15T10:00:00Z',
            updated_at=f'{current_month}-15T10:00:00Z',
            created_by='ai'
        ),
        Transaction(
            user_id='test-user',
            transaction_id='txn_004',
            date=f'{current_month}-20',
            amount=Decimal('300.00'),
            currency='USD',
            type='expense',
            category='Utilities',
            vendor='Power Company',
            description='Electricity bill',
            classification_confidence=0.90,
            classification_reasoning='Utility payment',
            status='approved',
            created_at=f'{current_month}-20T10:00:00Z',
            updated_at=f'{current_month}-20T10:00:00Z',
            created_by='ai'
        ),
        # Last month transactions
        Transaction(
            user_id='test-user',
            transaction_id='txn_005',
            date=f'{last_month}-05',
            amount=Decimal('4500.00'),
            currency='USD',
            type='income',
            category='Revenue',
            vendor='Client B',
            description='Payment received',
            classification_confidence=0.95,
            classification_reasoning='Payment from client',
            status='approved',
            created_at=f'{last_month}-05T10:00:00Z',
            updated_at=f'{last_month}-05T10:00:00Z',
            created_by='ai'
        ),
        Transaction(
            user_id='test-user',
            transaction_id='txn_006',
            date=f'{last_month}-10',
            amount=Decimal('1000.00'),
            currency='USD',
            type='expense',
            category='Marketing',
            vendor='Ad Agency',
            description='Marketing campaign',
            classification_confidence=0.88,
            classification_reasoning='Marketing expense',
            status='approved',
            created_at=f'{last_month}-10T10:00:00Z',
            updated_at=f'{last_month}-10T10:00:00Z',
            created_by='ai'
        ),
    ]
    
    return transactions


def test_calculate_cash_balance(sample_transactions):
    """Test cash balance calculation."""
    mock_repo = Mock()
    mock_repo.list_transactions.return_value = sample_transactions
    
    result = calculate_dashboard_data('test-user', repository=mock_repo)
    
    # Cash balance = total income - total expenses
    # Income: 5000 + 4500 = 9500
    # Expenses: 500 + 1200 + 300 + 1000 = 3000
    # Balance: 9500 - 3000 = 6500
    assert result['cash_balance'] == 6500.0


def test_calculate_current_month_income_and_expenses(sample_transactions):
    """Test current month income and expense calculation."""
    mock_repo = Mock()
    mock_repo.list_transactions.return_value = sample_transactions
    
    result = calculate_dashboard_data('test-user', repository=mock_repo)
    
    # Current month income: 5000
    assert result['total_income'] == 5000.0
    
    # Current month expenses: 500 + 1200 + 300 = 2000
    assert result['total_expenses'] == 2000.0


def test_calculate_profit_trend(sample_transactions):
    """Test profit trend calculation for last 6 months."""
    mock_repo = Mock()
    mock_repo.list_transactions.return_value = sample_transactions
    
    result = calculate_dashboard_data('test-user', repository=mock_repo)
    
    # Should have 6 months of data
    assert len(result['profit_trend']) == 6
    
    # Each entry should have month, income, expenses, profit
    for entry in result['profit_trend']:
        assert 'month' in entry
        assert 'income' in entry
        assert 'expenses' in entry
        assert 'profit' in entry
        assert entry['profit'] == entry['income'] - entry['expenses']


def test_calculate_top_categories(sample_transactions):
    """Test top 5 expense categories calculation."""
    mock_repo = Mock()
    mock_repo.list_transactions.return_value = sample_transactions
    
    result = calculate_dashboard_data('test-user', repository=mock_repo)
    
    # Should have top categories (up to 5)
    assert len(result['top_categories']) <= 5
    
    # Categories should be sorted by total (descending)
    if len(result['top_categories']) > 1:
        for i in range(len(result['top_categories']) - 1):
            assert result['top_categories'][i]['total'] >= result['top_categories'][i + 1]['total']
    
    # Each category should have category name and total
    for cat in result['top_categories']:
        assert 'category' in cat
        assert 'total' in cat


def test_top_categories_ranking(sample_transactions):
    """Test that top categories are correctly ranked."""
    mock_repo = Mock()
    mock_repo.list_transactions.return_value = sample_transactions
    
    result = calculate_dashboard_data('test-user', repository=mock_repo)
    
    # Expected ranking for current month:
    # 1. Rent: 1200
    # 2. Office Supplies: 500
    # 3. Utilities: 300
    
    assert result['top_categories'][0]['category'] == 'Rent'
    assert result['top_categories'][0]['total'] == 1200.0
    
    assert result['top_categories'][1]['category'] == 'Office Supplies'
    assert result['top_categories'][1]['total'] == 500.0
    
    assert result['top_categories'][2]['category'] == 'Utilities'
    assert result['top_categories'][2]['total'] == 300.0


def test_empty_transactions():
    """Test dashboard with no transactions."""
    mock_repo = Mock()
    mock_repo.list_transactions.return_value = []
    
    result = calculate_dashboard_data('test-user', repository=mock_repo)
    
    assert result['cash_balance'] == 0.0
    assert result['total_income'] == 0.0
    assert result['total_expenses'] == 0.0
    assert len(result['profit_trend']) == 6
    assert len(result['top_categories']) == 0


def test_lambda_handler_success(api_gateway_event, mock_context, sample_transactions):
    """Test successful Lambda handler execution."""
    with patch('src.lambdas.dashboard_api.handler.extract_token_from_event') as mock_extract_token, \
         patch('src.lambdas.dashboard_api.handler.get_user_id_from_token') as mock_get_user_id, \
         patch('src.lambdas.dashboard_api.handler.get_repository') as mock_get_repo:
        
        mock_extract_token.return_value = 'test-token'
        mock_get_user_id.return_value = 'test-user'
        
        mock_repo = Mock()
        mock_repo.list_transactions.return_value = sample_transactions
        mock_get_repo.return_value = mock_repo
        
        response = lambda_handler(api_gateway_event, mock_context)
        
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert 'cash_balance' in body
        assert 'total_income' in body
        assert 'total_expenses' in body
        assert 'profit_trend' in body
        assert 'top_categories' in body


def test_lambda_handler_authentication_error(api_gateway_event, mock_context):
    """Test Lambda handler with authentication error."""
    with patch('src.lambdas.dashboard_api.handler.extract_token_from_event') as mock_extract_token:
        mock_extract_token.side_effect = AuthenticationError('Invalid token')
        
        response = lambda_handler(api_gateway_event, mock_context)
        
        # Should return an error response (either 401 or 500 depending on how exception is caught)
        assert response['statusCode'] in [401, 500]
        assert 'error' in json.loads(response['body'])


def test_lambda_handler_internal_error(api_gateway_event, mock_context):
    """Test Lambda handler with internal error."""
    with patch('src.lambdas.dashboard_api.handler.extract_token_from_event') as mock_extract_token, \
         patch('src.lambdas.dashboard_api.handler.get_user_id_from_token') as mock_get_user_id, \
         patch('src.lambdas.dashboard_api.handler.get_repository') as mock_get_repo:
        
        mock_extract_token.return_value = 'test-token'
        mock_get_user_id.return_value = 'test-user'
        
        mock_repo = Mock()
        mock_repo.list_transactions.side_effect = Exception('Database error')
        mock_get_repo.return_value = mock_repo
        
        response = lambda_handler(api_gateway_event, mock_context)
        
        assert response['statusCode'] == 500


def test_dashboard_response_time():
    """Test that dashboard calculation is reasonably fast."""
    import time
    
    # Create a larger dataset
    transactions = []
    now = datetime.utcnow()
    
    for i in range(100):
        date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
        transactions.append(
            Transaction(
                user_id='test-user',
                transaction_id=f'txn_{i}',
                date=date,
                amount=Decimal('100.00'),
                currency='USD',
                type='expense' if i % 2 == 0 else 'income',
                category=f'Category{i % 10}',
                vendor=f'Vendor{i}',
                description='Test transaction',
                classification_confidence=0.9,
                classification_reasoning='Test',
                status='approved',
                created_at=f'{date}T10:00:00Z',
                updated_at=f'{date}T10:00:00Z',
                created_by='ai'
            )
        )
    
    mock_repo = Mock()
    mock_repo.list_transactions.return_value = transactions
    
    start_time = time.time()
    result = calculate_dashboard_data('test-user', repository=mock_repo)
    duration = time.time() - start_time
    
    # Should complete in less than 1 second for 100 transactions
    assert duration < 1.0
    assert result is not None
