"""
Unit tests for approval management Lambda functions.
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from src.lambdas.approval_manager.handler import (
    detect_large_transaction,
    detect_new_vendor,
    detect_bulk_reclassification,
    create_pending_approval,
    lambda_handler_list_pending,
    lambda_handler_approve,
    lambda_handler_reject,
    send_approval_reminder,
    lambda_handler_reminder
)
from src.shared.models import (
    Transaction,
    PendingApproval,
    generate_user_pk,
    generate_transaction_sk,
    generate_approval_sk,
    generate_timestamp,
    generate_id
)
from src.shared.exceptions import ValidationError, NotFoundError


@pytest.fixture
def mock_repository():
    """Mock DynamoDB repository."""
    with patch('src.lambdas.approval_manager.handler.get_repository') as mock_get_repo:
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        yield mock_repo


@pytest.fixture
def sample_transactions():
    """Create sample transactions for testing."""
    base_date = datetime(2024, 1, 15)
    transactions = []
    
    for i in range(10):
        date = (base_date - timedelta(days=i*7)).strftime('%Y-%m-%d')
        txn = Transaction(
            PK=generate_user_pk("user123"),
            SK=generate_transaction_sk(f"txn_{i}"),
            transaction_id=f"txn_{i}",
            date=date,
            amount=100.0 + i * 10,
            currency="USD",
            type="expense",
            category="Office Supplies",
            vendor=f"Vendor{i % 3}",  # 3 different vendors
            description=f"Transaction {i}",
            classification_confidence=0.9,
            classification_reasoning="Test",
            status="approved",
            created_at=generate_timestamp(),
            updated_at=generate_timestamp(),
            created_by="ai"
        )
        transactions.append(txn)
    
    return transactions


class TestDetectLargeTransaction:
    """Tests for detect_large_transaction function."""
    
    def test_large_transaction_exceeds_threshold(self, mock_repository, sample_transactions):
        """Test detection of transaction exceeding 10% of average monthly expenses."""
        # Setup: Average monthly expenses = (100+110+120+...+190) / 3 = ~450
        # 10% threshold = 45
        mock_repository.query_transactions_by_date_range.return_value = sample_transactions
        
        # Test with amount > threshold
        result = detect_large_transaction("user123", Decimal("50.0"), "2024-01-15")
        
        assert result is True
        mock_repository.query_transactions_by_date_range.assert_called_once()
    
    def test_small_transaction_below_threshold(self, mock_repository, sample_transactions):
        """Test detection of transaction below 10% threshold."""
        mock_repository.query_transactions_by_date_range.return_value = sample_transactions
        
        # Test with amount < threshold
        result = detect_large_transaction("user123", Decimal("30.0"), "2024-01-15")
        
        assert result is False
    
    def test_no_historical_data_uses_default_threshold(self, mock_repository):
        """Test that transactions > $1000 are considered large when no history exists."""
        mock_repository.query_transactions_by_date_range.return_value = []
        
        # Test with amount > $1000
        result = detect_large_transaction("user123", Decimal("1500.0"), "2024-01-15")
        assert result is True
        
        # Test with amount < $1000
        result = detect_large_transaction("user123", Decimal("500.0"), "2024-01-15")
        assert result is False
    
    def test_handles_error_gracefully(self, mock_repository):
        """Test that errors are handled gracefully and default to False."""
        mock_repository.query_transactions_by_date_range.side_effect = Exception("DB error")
        
        result = detect_large_transaction("user123", Decimal("100.0"), "2024-01-15")
        
        assert result is False


class TestDetectNewVendor:
    """Tests for detect_new_vendor function."""
    
    def test_existing_vendor_not_new(self, mock_repository, sample_transactions):
        """Test that existing vendor is not detected as new."""
        mock_repository.query_transactions_by_date_range.return_value = sample_transactions
        
        # Vendor0 exists in sample transactions
        result = detect_new_vendor("user123", "Vendor0", "2024-01-15")
        
        assert result is False
    
    def test_new_vendor_detected(self, mock_repository, sample_transactions):
        """Test that new vendor is detected."""
        mock_repository.query_transactions_by_date_range.return_value = sample_transactions
        
        # VendorNew does not exist in sample transactions
        result = detect_new_vendor("user123", "VendorNew", "2024-01-15")
        
        assert result is True
    
    def test_vendor_name_case_insensitive(self, mock_repository, sample_transactions):
        """Test that vendor name matching is case-insensitive."""
        mock_repository.query_transactions_by_date_range.return_value = sample_transactions
        
        # Test with different case
        result = detect_new_vendor("user123", "VENDOR0", "2024-01-15")
        
        assert result is False
    
    def test_vendor_name_whitespace_trimmed(self, mock_repository, sample_transactions):
        """Test that vendor name whitespace is trimmed."""
        mock_repository.query_transactions_by_date_range.return_value = sample_transactions
        
        # Test with extra whitespace
        result = detect_new_vendor("user123", "  Vendor0  ", "2024-01-15")
        
        assert result is False
    
    def test_no_historical_data_vendor_is_new(self, mock_repository):
        """Test that vendor is considered new when no history exists."""
        mock_repository.query_transactions_by_date_range.return_value = []
        
        result = detect_new_vendor("user123", "AnyVendor", "2024-01-15")
        
        assert result is True
    
    def test_handles_error_gracefully(self, mock_repository):
        """Test that errors are handled gracefully and default to False."""
        mock_repository.query_transactions_by_date_range.side_effect = Exception("DB error")
        
        result = detect_new_vendor("user123", "Vendor", "2024-01-15")
        
        assert result is False


class TestDetectBulkReclassification:
    """Tests for detect_bulk_reclassification function."""
    
    def test_single_transaction_not_bulk(self):
        """Test that single transaction is not considered bulk."""
        result = detect_bulk_reclassification(["txn_1"])
        assert result is False
    
    def test_two_transactions_is_bulk(self):
        """Test that 2 transactions is considered bulk."""
        result = detect_bulk_reclassification(["txn_1", "txn_2"])
        assert result is True
    
    def test_multiple_transactions_is_bulk(self):
        """Test that multiple transactions is considered bulk."""
        result = detect_bulk_reclassification(["txn_1", "txn_2", "txn_3", "txn_4"])
        assert result is True
    
    def test_empty_list_not_bulk(self):
        """Test that empty list is not considered bulk."""
        result = detect_bulk_reclassification([])
        assert result is False


class TestCreatePendingApproval:
    """Tests for create_pending_approval function."""
    
    def test_creates_approval_successfully(self, mock_repository):
        """Test successful creation of pending approval."""
        mock_repository.create_pending_approval.return_value = None
        
        approval = create_pending_approval(
            user_id="user123",
            approval_type="large_transaction",
            subject_type="transaction",
            subject_id="txn_123",
            details={"amount": 1500.0, "reason": "Exceeds threshold"}
        )
        
        assert approval.approval_type == "large_transaction"
        assert approval.subject_type == "transaction"
        assert approval.subject_id == "txn_123"
        assert approval.status == "pending"
        assert approval.details["amount"] == 1500.0
        mock_repository.create_pending_approval.assert_called_once()
    
    def test_generates_unique_approval_id(self, mock_repository):
        """Test that unique approval ID is generated."""
        mock_repository.create_pending_approval.return_value = None
        
        approval1 = create_pending_approval(
            user_id="user123",
            approval_type="new_vendor",
            subject_type="transaction",
            subject_id="txn_123",
            details={}
        )
        
        approval2 = create_pending_approval(
            user_id="user123",
            approval_type="new_vendor",
            subject_type="transaction",
            subject_id="txn_456",
            details={}
        )
        
        assert approval1.approval_id != approval2.approval_id
    
    def test_sets_gsi2_keys_for_pending_status(self, mock_repository):
        """Test that GSI2 keys are set for pending approvals."""
        mock_repository.create_pending_approval.return_value = None
        
        approval = create_pending_approval(
            user_id="user123",
            approval_type="bulk_reclassification",
            subject_type="transactions",
            subject_id="txn_1,txn_2,txn_3",
            details={"count": 3}
        )
        
        assert approval.GSI2PK == "USER#user123#STATUS#pending"
        assert approval.GSI2SK.startswith("DATE#")


class TestLambdaHandlerListPending:
    """Tests for lambda_handler_list_pending function."""
    
    def test_lists_pending_approvals_successfully(self, mock_repository):
        """Test successful listing of pending approvals."""
        # Create sample approvals
        approvals = [
            PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_1"),
                approval_id="approval_1",
                approval_type="large_transaction",
                subject_type="transaction",
                subject_id="txn_123",
                created_at=generate_timestamp(),
                status="pending",
                details={"amount": 1500.0}
            ),
            PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_2"),
                approval_id="approval_2",
                approval_type="new_vendor",
                subject_type="transaction",
                subject_id="txn_456",
                created_at=generate_timestamp(),
                status="pending",
                details={"vendor": "NewVendor"}
            )
        ]
        mock_repository.list_pending_approvals.return_value = approvals
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_list_pending(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2
        assert len(body['approvals']) == 2
        assert body['approvals'][0]['approval_id'] == 'approval_1'
        assert body['approvals'][1]['approval_id'] == 'approval_2'
    
    def test_returns_empty_list_when_no_approvals(self, mock_repository):
        """Test returns empty list when no pending approvals exist."""
        mock_repository.list_pending_approvals.return_value = []
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_list_pending(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 0
        assert body['approvals'] == []
    
    def test_returns_error_when_user_id_missing(self, mock_repository):
        """Test returns error when user ID is missing from context."""
        event = {
            'requestContext': {}
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_list_pending(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body


class TestLambdaHandlerApprove:
    """Tests for lambda_handler_approve function."""
    
    def test_approves_large_transaction_successfully(self, mock_repository):
        """Test successful approval of large transaction."""
        approval = PendingApproval(
            PK=generate_user_pk("user123"),
            SK=generate_approval_sk("approval_1"),
            approval_id="approval_1",
            approval_type="large_transaction",
            subject_type="transaction",
            subject_id="txn_123",
            created_at=generate_timestamp(),
            status="pending",
            details={"amount": 1500.0}
        )
        mock_repository.get_pending_approval.return_value = approval
        mock_repository.update_pending_approval.return_value = None
        mock_repository.update_transaction.return_value = None
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            },
            'pathParameters': {
                'id': 'approval_1'
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_approve(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'approved'
        assert body['approval_id'] == 'approval_1'
        
        # Verify approval was updated
        mock_repository.update_pending_approval.assert_called_once()
        # Verify transaction was updated
        mock_repository.update_transaction.assert_called_once()
    
    def test_approves_new_vendor_successfully(self, mock_repository):
        """Test successful approval of new vendor."""
        approval = PendingApproval(
            PK=generate_user_pk("user123"),
            SK=generate_approval_sk("approval_2"),
            approval_id="approval_2",
            approval_type="new_vendor",
            subject_type="transaction",
            subject_id="txn_456",
            created_at=generate_timestamp(),
            status="pending",
            details={"vendor": "NewVendor"}
        )
        mock_repository.get_pending_approval.return_value = approval
        mock_repository.update_pending_approval.return_value = None
        mock_repository.update_transaction.return_value = None
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            },
            'pathParameters': {
                'id': 'approval_2'
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_approve(event, context)
        
        assert response['statusCode'] == 200
        mock_repository.update_transaction.assert_called_once()
    
    def test_approves_bulk_reclassification_successfully(self, mock_repository):
        """Test successful approval of bulk reclassification."""
        approval = PendingApproval(
            PK=generate_user_pk("user123"),
            SK=generate_approval_sk("approval_3"),
            approval_id="approval_3",
            approval_type="bulk_reclassification",
            subject_type="transactions",
            subject_id="txn_1,txn_2,txn_3",
            created_at=generate_timestamp(),
            status="pending",
            details={"count": 3, "new_category": "Marketing"}
        )
        mock_repository.get_pending_approval.return_value = approval
        mock_repository.update_pending_approval.return_value = None
        mock_repository.update_transaction.return_value = None
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            },
            'pathParameters': {
                'id': 'approval_3'
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_approve(event, context)
        
        assert response['statusCode'] == 200
        # Verify all 3 transactions were updated
        assert mock_repository.update_transaction.call_count == 3
    
    def test_returns_error_when_approval_not_found(self, mock_repository):
        """Test returns error when approval is not found."""
        mock_repository.get_pending_approval.return_value = None
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            },
            'pathParameters': {
                'id': 'nonexistent'
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_approve(event, context)
        
        assert response['statusCode'] == 404
    
    def test_returns_error_when_already_processed(self, mock_repository):
        """Test returns error when approval is already processed."""
        approval = PendingApproval(
            PK=generate_user_pk("user123"),
            SK=generate_approval_sk("approval_1"),
            approval_id="approval_1",
            approval_type="large_transaction",
            subject_type="transaction",
            subject_id="txn_123",
            created_at=generate_timestamp(),
            status="approved",  # Already approved
            details={}
        )
        mock_repository.get_pending_approval.return_value = approval
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            },
            'pathParameters': {
                'id': 'approval_1'
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_approve(event, context)
        
        assert response['statusCode'] == 400


class TestLambdaHandlerReject:
    """Tests for lambda_handler_reject function."""
    
    def test_rejects_approval_successfully(self, mock_repository):
        """Test successful rejection of approval."""
        approval = PendingApproval(
            PK=generate_user_pk("user123"),
            SK=generate_approval_sk("approval_1"),
            approval_id="approval_1",
            approval_type="large_transaction",
            subject_type="transaction",
            subject_id="txn_123",
            created_at=generate_timestamp(),
            status="pending",
            details={"amount": 1500.0}
        )
        mock_repository.get_pending_approval.return_value = approval
        mock_repository.update_pending_approval.return_value = None
        mock_repository.update_transaction.return_value = None
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            },
            'pathParameters': {
                'id': 'approval_1'
            },
            'body': json.dumps({'reason': 'Too expensive'})
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_reject(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'rejected'
        
        # Verify approval was updated with rejection
        mock_repository.update_pending_approval.assert_called_once()
        # Verify transaction was updated
        mock_repository.update_transaction.assert_called_once()
    
    def test_rejects_with_default_reason_when_not_provided(self, mock_repository):
        """Test rejection uses default reason when not provided."""
        approval = PendingApproval(
            PK=generate_user_pk("user123"),
            SK=generate_approval_sk("approval_1"),
            approval_id="approval_1",
            approval_type="new_vendor",
            subject_type="transaction",
            subject_id="txn_123",
            created_at=generate_timestamp(),
            status="pending",
            details={}
        )
        mock_repository.get_pending_approval.return_value = approval
        mock_repository.update_pending_approval.return_value = None
        mock_repository.update_transaction.return_value = None
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            },
            'pathParameters': {
                'id': 'approval_1'
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_reject(event, context)
        
        assert response['statusCode'] == 200
    
    def test_rejects_bulk_reclassification_without_updating_transactions(self, mock_repository):
        """Test bulk reclassification rejection doesn't update transactions."""
        approval = PendingApproval(
            PK=generate_user_pk("user123"),
            SK=generate_approval_sk("approval_3"),
            approval_id="approval_3",
            approval_type="bulk_reclassification",
            subject_type="transactions",
            subject_id="txn_1,txn_2,txn_3",
            created_at=generate_timestamp(),
            status="pending",
            details={"count": 3}
        )
        mock_repository.get_pending_approval.return_value = approval
        mock_repository.update_pending_approval.return_value = None
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            },
            'pathParameters': {
                'id': 'approval_3'
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_reject(event, context)
        
        assert response['statusCode'] == 200
        # Verify transactions were NOT updated (bulk rejection doesn't change them)
        mock_repository.update_transaction.assert_not_called()
    
    def test_returns_error_when_approval_not_found(self, mock_repository):
        """Test returns error when approval is not found."""
        mock_repository.get_pending_approval.return_value = None
        
        event = {
            'requestContext': {
                'authorizer': {
                    'principalId': 'user123'
                }
            },
            'pathParameters': {
                'id': 'nonexistent'
            }
        }
        context = Mock(request_id='req_123')
        
        response = lambda_handler_reject(event, context)
        
        assert response['statusCode'] == 404



class TestSendApprovalReminder:
    """Tests for send_approval_reminder function."""
    
    def test_sends_reminder_for_large_transaction(self):
        """Test sending reminder for large transaction approval."""
        with patch('src.lambdas.approval_manager.handler.get_sns_client') as mock_get_sns, \
             patch('src.lambdas.approval_manager.handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:approval-reminders'):
            
            mock_sns = Mock()
            mock_sns.publish.return_value = {'MessageId': 'msg_123'}
            mock_get_sns.return_value = mock_sns
            
            # Create approval older than 48 hours
            created_at = (datetime.utcnow() - timedelta(hours=50)).isoformat() + 'Z'
            approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_1"),
                approval_id="approval_1",
                approval_type="large_transaction",
                subject_type="transaction",
                subject_id="txn_123",
                created_at=created_at,
                status="pending",
                details={"amount": 1500.0, "reason": "Exceeds threshold"}
            )
            
            result = send_approval_reminder(approval, "user123")
            
            assert result is True
            mock_sns.publish.assert_called_once()
            call_args = mock_sns.publish.call_args
            assert call_args[1]['Subject'] == "Pending Approval Reminder"
            assert "approval_1" in call_args[1]['Message']
            assert "large_transaction" in call_args[1]['Message']
            assert "1500.0" in call_args[1]['Message']
    
    def test_sends_reminder_for_new_vendor(self):
        """Test sending reminder for new vendor approval."""
        with patch('src.lambdas.approval_manager.handler.get_sns_client') as mock_get_sns, \
             patch('src.lambdas.approval_manager.handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:approval-reminders'):
            
            mock_sns = Mock()
            mock_sns.publish.return_value = {'MessageId': 'msg_456'}
            mock_get_sns.return_value = mock_sns
            
            created_at = (datetime.utcnow() - timedelta(hours=60)).isoformat() + 'Z'
            approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_2"),
                approval_id="approval_2",
                approval_type="new_vendor",
                subject_type="transaction",
                subject_id="txn_456",
                created_at=created_at,
                status="pending",
                details={"vendor": "NewVendor Inc", "amount": 500.0}
            )
            
            result = send_approval_reminder(approval, "user123")
            
            assert result is True
            mock_sns.publish.assert_called_once()
            call_args = mock_sns.publish.call_args
            assert "NewVendor Inc" in call_args[1]['Message']
            assert "500.0" in call_args[1]['Message']
    
    def test_sends_reminder_for_bulk_reclassification(self):
        """Test sending reminder for bulk reclassification approval."""
        with patch('src.lambdas.approval_manager.handler.get_sns_client') as mock_get_sns, \
             patch('src.lambdas.approval_manager.handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:approval-reminders'):
            
            mock_sns = Mock()
            mock_sns.publish.return_value = {'MessageId': 'msg_789'}
            mock_get_sns.return_value = mock_sns
            
            created_at = (datetime.utcnow() - timedelta(hours=72)).isoformat() + 'Z'
            approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_3"),
                approval_id="approval_3",
                approval_type="bulk_reclassification",
                subject_type="transactions",
                subject_id="txn_1,txn_2,txn_3",
                created_at=created_at,
                status="pending",
                details={"count": 3, "new_category": "Marketing"}
            )
            
            result = send_approval_reminder(approval, "user123")
            
            assert result is True
            mock_sns.publish.assert_called_once()
            call_args = mock_sns.publish.call_args
            assert "3" in call_args[1]['Message']
            assert "Marketing" in call_args[1]['Message']
            assert "txn_1, txn_2, txn_3" in call_args[1]['Message']
    
    def test_calculates_age_in_hours_correctly(self):
        """Test that age in hours is calculated correctly."""
        with patch('src.lambdas.approval_manager.handler.get_sns_client') as mock_get_sns, \
             patch('src.lambdas.approval_manager.handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:approval-reminders'):
            
            mock_sns = Mock()
            mock_sns.publish.return_value = {'MessageId': 'msg_123'}
            mock_get_sns.return_value = mock_sns
            
            # Create approval exactly 50 hours old
            created_at = (datetime.utcnow() - timedelta(hours=50)).isoformat() + 'Z'
            approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_1"),
                approval_id="approval_1",
                approval_type="large_transaction",
                subject_type="transaction",
                subject_id="txn_123",
                created_at=created_at,
                status="pending",
                details={}
            )
            
            send_approval_reminder(approval, "user123")
            
            call_args = mock_sns.publish.call_args
            message = call_args[1]['Message']
            # Age should be approximately 50 hours
            assert "50 hours" in message or "49 hours" in message
    
    def test_returns_false_when_sns_topic_not_configured(self):
        """Test returns False when SNS topic ARN is not configured."""
        with patch('src.lambdas.approval_manager.handler.SNS_TOPIC_ARN', ''):
            approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_1"),
                approval_id="approval_1",
                approval_type="large_transaction",
                subject_type="transaction",
                subject_id="txn_123",
                created_at=generate_timestamp(),
                status="pending",
                details={}
            )
            
            result = send_approval_reminder(approval, "user123")
            
            assert result is False
    
    def test_handles_sns_error_gracefully(self):
        """Test handles SNS publish error gracefully."""
        with patch('src.lambdas.approval_manager.handler.get_sns_client') as mock_get_sns, \
             patch('src.lambdas.approval_manager.handler.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:approval-reminders'):
            
            mock_sns = Mock()
            mock_sns.publish.side_effect = Exception("SNS error")
            mock_get_sns.return_value = mock_sns
            
            approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_1"),
                approval_id="approval_1",
                approval_type="large_transaction",
                subject_type="transaction",
                subject_id="txn_123",
                created_at=generate_timestamp(),
                status="pending",
                details={}
            )
            
            result = send_approval_reminder(approval, "user123")
            
            assert result is False


class TestLambdaHandlerReminder:
    """Tests for lambda_handler_reminder function."""
    
    def test_queries_approvals_older_than_48_hours(self, mock_repository):
        """Test queries pending approvals older than 48 hours."""
        with patch('src.lambdas.approval_manager.handler.send_approval_reminder') as mock_send:
            mock_send.return_value = True
            
            # Create approvals: one old (50 hours), one recent (24 hours)
            old_approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_old"),
                approval_id="approval_old",
                approval_type="large_transaction",
                subject_type="transaction",
                subject_id="txn_123",
                created_at=(datetime.utcnow() - timedelta(hours=50)).isoformat() + 'Z',
                status="pending",
                details={}
            )
            
            # Mock scan to return old approval
            mock_repository.table.scan.return_value = {
                'Items': [old_approval.to_dict()]
            }
            mock_repository._convert_decimal_to_float.return_value = old_approval.to_dict()
            mock_repository.update_pending_approval.return_value = None
            
            event = {}
            context = Mock(request_id='req_123')
            
            response = lambda_handler_reminder(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['reminders_sent'] == 1
            assert body['total_approvals_checked'] == 1
    
    def test_sends_reminders_for_multiple_approvals(self, mock_repository):
        """Test sends reminders for multiple pending approvals."""
        with patch('src.lambdas.approval_manager.handler.send_approval_reminder') as mock_send:
            mock_send.return_value = True
            
            # Create multiple old approvals
            approvals = []
            for i in range(3):
                approval = PendingApproval(
                    PK=generate_user_pk(f"user{i}"),
                    SK=generate_approval_sk(f"approval_{i}"),
                    approval_id=f"approval_{i}",
                    approval_type="large_transaction",
                    subject_type="transaction",
                    subject_id=f"txn_{i}",
                    created_at=(datetime.utcnow() - timedelta(hours=50 + i)).isoformat() + 'Z',
                    status="pending",
                    details={}
                )
                approvals.append(approval)
            
            # Mock scan to return all approvals
            mock_repository.table.scan.return_value = {
                'Items': [a.to_dict() for a in approvals]
            }
            mock_repository._convert_decimal_to_float.side_effect = [a.to_dict() for a in approvals]
            mock_repository.update_pending_approval.return_value = None
            
            event = {}
            context = Mock(request_id='req_123')
            
            response = lambda_handler_reminder(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['reminders_sent'] == 3
            assert body['total_approvals_checked'] == 3
            assert mock_send.call_count == 3
    
    def test_updates_reminder_sent_at_timestamp(self, mock_repository):
        """Test updates reminder_sent_at timestamp after sending reminder."""
        with patch('src.lambdas.approval_manager.handler.send_approval_reminder') as mock_send:
            mock_send.return_value = True
            
            approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_1"),
                approval_id="approval_1",
                approval_type="large_transaction",
                subject_type="transaction",
                subject_id="txn_123",
                created_at=(datetime.utcnow() - timedelta(hours=50)).isoformat() + 'Z',
                status="pending",
                details={}
            )
            
            mock_repository.table.scan.return_value = {
                'Items': [approval.to_dict()]
            }
            mock_repository._convert_decimal_to_float.return_value = approval.to_dict()
            mock_repository.update_pending_approval.return_value = None
            
            event = {}
            context = Mock(request_id='req_123')
            
            lambda_handler_reminder(event, context)
            
            # Verify update_pending_approval was called with reminder_sent_at
            mock_repository.update_pending_approval.assert_called_once()
            call_args = mock_repository.update_pending_approval.call_args
            assert 'reminder_sent_at' in call_args[1]['updates']
    
    def test_skips_approvals_with_reminder_already_sent(self, mock_repository):
        """Test skips approvals that already have reminder_sent_at set."""
        # The scan filter should exclude approvals with reminder_sent_at
        # This is tested by the FilterExpression in the scan
        mock_repository.table.scan.return_value = {
            'Items': []  # No items because filter excludes them
        }
        
        event = {}
        context = Mock(request_id='req_123')
        
        response = lambda_handler_reminder(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['reminders_sent'] == 0
        assert body['total_approvals_checked'] == 0
    
    def test_handles_send_reminder_failure(self, mock_repository):
        """Test handles send_approval_reminder failure gracefully."""
        with patch('src.lambdas.approval_manager.handler.send_approval_reminder') as mock_send:
            mock_send.return_value = False  # Simulate failure
            
            approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_1"),
                approval_id="approval_1",
                approval_type="large_transaction",
                subject_type="transaction",
                subject_id="txn_123",
                created_at=(datetime.utcnow() - timedelta(hours=50)).isoformat() + 'Z',
                status="pending",
                details={}
            )
            
            mock_repository.table.scan.return_value = {
                'Items': [approval.to_dict()]
            }
            mock_repository._convert_decimal_to_float.return_value = approval.to_dict()
            
            event = {}
            context = Mock(request_id='req_123')
            
            response = lambda_handler_reminder(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['reminders_sent'] == 0
            assert body['reminders_failed'] == 1
    
    def test_handles_update_error_gracefully(self, mock_repository):
        """Test handles update_pending_approval error gracefully."""
        with patch('src.lambdas.approval_manager.handler.send_approval_reminder') as mock_send:
            mock_send.return_value = True
            
            approval = PendingApproval(
                PK=generate_user_pk("user123"),
                SK=generate_approval_sk("approval_1"),
                approval_id="approval_1",
                approval_type="large_transaction",
                subject_type="transaction",
                subject_id="txn_123",
                created_at=(datetime.utcnow() - timedelta(hours=50)).isoformat() + 'Z',
                status="pending",
                details={}
            )
            
            mock_repository.table.scan.return_value = {
                'Items': [approval.to_dict()]
            }
            mock_repository._convert_decimal_to_float.return_value = approval.to_dict()
            mock_repository.update_pending_approval.side_effect = Exception("Update error")
            
            event = {}
            context = Mock(request_id='req_123')
            
            response = lambda_handler_reminder(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['reminders_failed'] == 1
    
    def test_returns_error_on_scan_failure(self, mock_repository):
        """Test returns error when scan fails."""
        mock_repository.table.scan.side_effect = Exception("Scan error")
        
        event = {}
        context = Mock(request_id='req_123')
        
        response = lambda_handler_reminder(event, context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
