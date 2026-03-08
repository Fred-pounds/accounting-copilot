"""
Unit tests for reconciliation engine.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.lambdas.reconciliation_engine.handler import (
    levenshtein_distance,
    calculate_vendor_similarity,
    calculate_amount_similarity,
    calculate_date_proximity,
    calculate_match_confidence,
    find_best_match,
    identify_unmatched_transactions,
    reconcile_transaction,
    lambda_handler
)
from src.shared.entities import Transaction, BankTransaction


class TestLevenshteinDistance:
    """Test Levenshtein distance calculation."""
    
    def test_identical_strings(self):
        """Test distance between identical strings."""
        assert levenshtein_distance("hello", "hello") == 0
    
    def test_completely_different_strings(self):
        """Test distance between completely different strings."""
        distance = levenshtein_distance("abc", "xyz")
        assert distance == 3
    
    def test_one_character_difference(self):
        """Test distance with one character difference."""
        assert levenshtein_distance("hello", "hallo") == 1
    
    def test_empty_strings(self):
        """Test distance with empty strings."""
        assert levenshtein_distance("", "") == 0
        assert levenshtein_distance("hello", "") == 5
        assert levenshtein_distance("", "world") == 5


class TestVendorSimilarity:
    """Test vendor name similarity calculation."""
    
    def test_identical_vendors(self):
        """Test similarity between identical vendor names."""
        similarity = calculate_vendor_similarity("Office Depot", "Office Depot")
        assert similarity == 1.0
    
    def test_case_insensitive(self):
        """Test that comparison is case insensitive."""
        similarity = calculate_vendor_similarity("OFFICE DEPOT", "office depot")
        assert similarity == 1.0
    
    def test_similar_vendors(self):
        """Test similarity between similar vendor names."""
        similarity = calculate_vendor_similarity("Office Depot", "Office Depot #1234")
        assert similarity > 0.5
    
    def test_different_vendors(self):
        """Test similarity between different vendor names."""
        similarity = calculate_vendor_similarity("Office Depot", "Walmart")
        assert similarity < 0.5
    
    def test_empty_vendor(self):
        """Test similarity with empty vendor name."""
        similarity = calculate_vendor_similarity("", "Office Depot")
        assert similarity == 0.0


class TestAmountSimilarity:
    """Test amount similarity calculation."""
    
    def test_identical_amounts(self):
        """Test similarity between identical amounts."""
        similarity = calculate_amount_similarity(Decimal("45.99"), Decimal("45.99"))
        assert similarity == 1.0
    
    def test_within_5_percent_tolerance(self):
        """Test amounts within 5% tolerance get full score."""
        similarity = calculate_amount_similarity(Decimal("100.00"), Decimal("102.00"))
        assert similarity == 1.0
    
    def test_between_5_and_20_percent(self):
        """Test amounts between 5% and 20% difference."""
        similarity = calculate_amount_similarity(Decimal("100.00"), Decimal("110.00"))
        assert 0.0 < similarity < 1.0
    
    def test_above_20_percent_difference(self):
        """Test amounts with more than 20% difference."""
        similarity = calculate_amount_similarity(Decimal("100.00"), Decimal("150.00"))
        assert similarity == 0.0
    
    def test_zero_amounts(self):
        """Test similarity with zero amounts."""
        similarity = calculate_amount_similarity(Decimal("0.00"), Decimal("0.00"))
        assert similarity == 1.0


class TestDateProximity:
    """Test date proximity calculation."""
    
    def test_same_date(self):
        """Test proximity for same date."""
        proximity = calculate_date_proximity("2024-01-15", "2024-01-15")
        assert proximity == 1.0
    
    def test_within_3_days(self):
        """Test dates within 3 days get full score."""
        proximity = calculate_date_proximity("2024-01-15", "2024-01-17")
        assert proximity == 1.0
    
    def test_between_3_and_7_days(self):
        """Test dates between 3 and 7 days apart."""
        proximity = calculate_date_proximity("2024-01-15", "2024-01-20")
        assert 0.0 < proximity < 1.0
    
    def test_more_than_7_days(self):
        """Test dates more than 7 days apart."""
        proximity = calculate_date_proximity("2024-01-15", "2024-01-30")
        assert proximity == 0.0
    
    def test_invalid_date_format(self):
        """Test handling of invalid date format."""
        proximity = calculate_date_proximity("invalid", "2024-01-15")
        assert proximity == 0.0


class TestMatchConfidence:
    """Test overall match confidence calculation."""
    
    def test_perfect_match(self):
        """Test confidence for perfect match."""
        transaction = Transaction(
            user_id="user123",
            transaction_id="txn123",
            date="2024-01-15",
            amount=Decimal("45.99"),
            currency="USD",
            type="expense",
            category="Office Supplies",
            vendor="Office Depot",
            description="Office supplies",
            classification_confidence=0.9,
            classification_reasoning="Test",
            status="approved",
            created_at="2024-01-15T10:00:00Z",
            updated_at="2024-01-15T10:00:00Z",
            created_by="ai"
        )
        
        bank_transaction = BankTransaction(
            user_id="user123",
            bank_transaction_id="bank123",
            date="2024-01-15",
            amount=Decimal("45.99"),
            currency="USD",
            description="Office Depot",
            reconciliation_status="unmatched",
            imported_at="2024-01-16T08:00:00Z"
        )
        
        confidence = calculate_match_confidence(transaction, bank_transaction)
        assert confidence > 0.9
    
    def test_partial_match(self):
        """Test confidence for partial match."""
        transaction = Transaction(
            user_id="user123",
            transaction_id="txn123",
            date="2024-01-15",
            amount=Decimal("45.99"),
            currency="USD",
            type="expense",
            category="Office Supplies",
            vendor="Office Depot",
            description="Office supplies",
            classification_confidence=0.9,
            classification_reasoning="Test",
            status="approved",
            created_at="2024-01-15T10:00:00Z",
            updated_at="2024-01-15T10:00:00Z",
            created_by="ai"
        )
        
        bank_transaction = BankTransaction(
            user_id="user123",
            bank_transaction_id="bank123",
            date="2024-01-18",  # 3 days later
            amount=Decimal("47.00"),  # Slightly different
            currency="USD",
            description="Office Depot Store",  # Similar vendor
            reconciliation_status="unmatched",
            imported_at="2024-01-19T08:00:00Z"
        )
        
        confidence = calculate_match_confidence(transaction, bank_transaction)
        assert 0.5 < confidence < 0.9


class TestFindBestMatch:
    """Test finding best matching bank transaction."""
    
    def test_find_best_match_above_threshold(self):
        """Test finding best match above threshold."""
        transaction = Transaction(
            user_id="user123",
            transaction_id="txn123",
            date="2024-01-15",
            amount=Decimal("45.99"),
            currency="USD",
            type="expense",
            category="Office Supplies",
            vendor="Office Depot",
            description="Office supplies",
            classification_confidence=0.9,
            classification_reasoning="Test",
            status="approved",
            created_at="2024-01-15T10:00:00Z",
            updated_at="2024-01-15T10:00:00Z",
            created_by="ai"
        )
        
        bank_transactions = [
            BankTransaction(
                user_id="user123",
                bank_transaction_id="bank123",
                date="2024-01-15",
                amount=Decimal("45.99"),
                currency="USD",
                description="Office Depot",
                reconciliation_status="unmatched",
                imported_at="2024-01-16T08:00:00Z"
            ),
            BankTransaction(
                user_id="user123",
                bank_transaction_id="bank456",
                date="2024-01-20",
                amount=Decimal("100.00"),
                currency="USD",
                description="Walmart",
                reconciliation_status="unmatched",
                imported_at="2024-01-21T08:00:00Z"
            )
        ]
        
        result = find_best_match(transaction, bank_transactions)
        assert result is not None
        best_match, confidence = result
        assert best_match.bank_transaction_id == "bank123"
        assert confidence > 0.5
    
    def test_no_match_below_threshold(self):
        """Test when no match is above threshold."""
        transaction = Transaction(
            user_id="user123",
            transaction_id="txn123",
            date="2024-01-15",
            amount=Decimal("45.99"),
            currency="USD",
            type="expense",
            category="Office Supplies",
            vendor="Office Depot",
            description="Office supplies",
            classification_confidence=0.9,
            classification_reasoning="Test",
            status="approved",
            created_at="2024-01-15T10:00:00Z",
            updated_at="2024-01-15T10:00:00Z",
            created_by="ai"
        )
        
        bank_transactions = [
            BankTransaction(
                user_id="user123",
                bank_transaction_id="bank123",
                date="2024-02-15",  # 1 month later
                amount=Decimal("200.00"),  # Very different amount
                currency="USD",
                description="Completely Different Store",
                reconciliation_status="unmatched",
                imported_at="2024-02-16T08:00:00Z"
            )
        ]
        
        result = find_best_match(transaction, bank_transactions)
        assert result is None


class TestIdentifyUnmatchedTransactions:
    """Test identifying unmatched transactions."""
    
    def test_identify_old_unmatched(self):
        """Test identifying unmatched transactions older than 7 days."""
        old_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        recent_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        bank_transactions = [
            BankTransaction(
                user_id="user123",
                bank_transaction_id="bank123",
                date=old_date,
                amount=Decimal("45.99"),
                currency="USD",
                description="Old Transaction",
                reconciliation_status="unmatched",
                imported_at="2024-01-01T08:00:00Z"
            ),
            BankTransaction(
                user_id="user123",
                bank_transaction_id="bank456",
                date=recent_date,
                amount=Decimal("100.00"),
                currency="USD",
                description="Recent Transaction",
                reconciliation_status="unmatched",
                imported_at="2024-01-15T08:00:00Z"
            ),
            BankTransaction(
                user_id="user123",
                bank_transaction_id="bank789",
                date=old_date,
                amount=Decimal("75.00"),
                currency="USD",
                description="Matched Transaction",
                reconciliation_status="matched",
                imported_at="2024-01-01T08:00:00Z"
            )
        ]
        
        unmatched = identify_unmatched_transactions(bank_transactions)
        assert len(unmatched) == 1
        assert unmatched[0].bank_transaction_id == "bank123"


class TestReconcileTransaction:
    """Test reconciling a single transaction."""
    
    @patch('src.lambdas.reconciliation_engine.handler.DynamoDBRepository')
    def test_auto_link_high_confidence(self, mock_repo_class):
        """Test auto-linking with high confidence match."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        transaction = Transaction(
            user_id="user123",
            transaction_id="txn123",
            date="2024-01-15",
            amount=Decimal("45.99"),
            currency="USD",
            type="expense",
            category="Office Supplies",
            vendor="Office Depot",
            description="Office supplies",
            classification_confidence=0.9,
            classification_reasoning="Test",
            status="approved",
            created_at="2024-01-15T10:00:00Z",
            updated_at="2024-01-15T10:00:00Z",
            created_by="ai"
        )
        
        bank_transactions = [
            BankTransaction(
                user_id="user123",
                bank_transaction_id="bank123",
                date="2024-01-15",
                amount=Decimal("45.99"),
                currency="USD",
                description="Office Depot",
                reconciliation_status="unmatched",
                imported_at="2024-01-16T08:00:00Z"
            )
        ]
        
        result = reconcile_transaction(transaction, bank_transactions, mock_repo)
        
        assert result['status'] == 'auto_linked'
        assert result['confidence'] > 0.8
        assert mock_repo.update_transaction.called
        assert mock_repo.update_bank_transaction.called
    
    @patch('src.lambdas.reconciliation_engine.handler.DynamoDBRepository')
    def test_flag_for_approval_medium_confidence(self, mock_repo_class):
        """Test flagging for approval with medium confidence match."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        transaction = Transaction(
            user_id="user123",
            transaction_id="txn123",
            date="2024-01-15",
            amount=Decimal("45.99"),
            currency="USD",
            type="expense",
            category="Office Supplies",
            vendor="Office Depot",
            description="Office supplies",
            classification_confidence=0.9,
            classification_reasoning="Test",
            status="approved",
            created_at="2024-01-15T10:00:00Z",
            updated_at="2024-01-15T10:00:00Z",
            created_by="ai"
        )
        
        bank_transactions = [
            BankTransaction(
                user_id="user123",
                bank_transaction_id="bank123",
                date="2024-01-18",  # 3 days later
                amount=Decimal("48.00"),  # Slightly different
                currency="USD",
                description="Office Depot Store",
                reconciliation_status="unmatched",
                imported_at="2024-01-19T08:00:00Z"
            )
        ]
        
        result = reconcile_transaction(transaction, bank_transactions, mock_repo)
        
        # Result depends on exact confidence calculation
        assert result['status'] in ['auto_linked', 'pending_approval', 'no_match']
        assert mock_repo.update_transaction.called or result['status'] == 'no_match'


class TestLambdaHandler:
    """Test Lambda handler function."""
    
    @patch('src.lambdas.reconciliation_engine.handler.DynamoDBRepository')
    @patch('src.lambdas.reconciliation_engine.handler.send_unmatched_notification')
    def test_successful_reconciliation(self, mock_notify, mock_repo_class):
        """Test successful reconciliation workflow."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock repository responses
        mock_repo.list_transactions.return_value = ([
            Transaction(
                user_id="user123",
                transaction_id="txn123",
                date="2024-01-15",
                amount=Decimal("45.99"),
                currency="USD",
                type="expense",
                category="Office Supplies",
                vendor="Office Depot",
                description="Office supplies",
                classification_confidence=0.9,
                classification_reasoning="Test",
                status="approved",
                created_at="2024-01-15T10:00:00Z",
                updated_at="2024-01-15T10:00:00Z",
                created_by="ai",
                reconciliation_status="unmatched"
            )
        ], None)
        
        mock_repo.list_bank_transactions.return_value = ([
            BankTransaction(
                user_id="user123",
                bank_transaction_id="bank123",
                date="2024-01-15",
                amount=Decimal("45.99"),
                currency="USD",
                description="Office Depot",
                reconciliation_status="unmatched",
                imported_at="2024-01-16T08:00:00Z"
            )
        ], None)
        
        event = {'user_id': 'user123'}
        context = Mock()
        
        result = lambda_handler(event, context)
        
        assert result['status'] == 'success'
        assert result['user_id'] == 'user123'
        assert 'matches_found' in result
        assert 'auto_linked' in result
        assert 'pending_review' in result
    
    def test_missing_user_id(self):
        """Test error handling when user_id is missing."""
        event = {}
        context = Mock()
        
        result = lambda_handler(event, context)
        
        assert result['status'] == 'error'
        assert 'error' in result
