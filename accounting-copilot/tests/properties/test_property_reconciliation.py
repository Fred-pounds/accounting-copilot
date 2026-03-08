"""
Property-based tests for reconciliation engine.

These tests verify universal properties that should hold across all valid inputs.
"""

import pytest
from hypothesis import given, settings, strategies as st
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.lambdas.reconciliation_engine.handler import (
    calculate_match_confidence,
    reconcile_transaction,
    identify_unmatched_transactions
)
from src.shared.entities import Transaction, BankTransaction


# Custom strategies for generating test data
@st.composite
def transaction_strategy(draw):
    """Generate a valid Transaction entity."""
    date = draw(st.dates(min_value=datetime(2020, 1, 1).date(), max_value=datetime(2025, 12, 31).date()))
    amount = draw(st.decimals(min_value=Decimal("0.01"), max_value=Decimal("10000.00"), places=2))
    vendor = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    
    return Transaction(
        user_id="test_user",
        transaction_id=f"txn_{draw(st.integers(min_value=1, max_value=999999))}",
        date=date.strftime('%Y-%m-%d'),
        amount=amount,
        currency="USD",
        type="expense",
        category="Test Category",
        vendor=vendor,
        description=draw(st.text(max_size=200)),
        classification_confidence=draw(st.floats(min_value=0.0, max_value=1.0)),
        classification_reasoning="Test reasoning",
        status="approved",
        created_at=datetime.utcnow().isoformat() + 'Z',
        updated_at=datetime.utcnow().isoformat() + 'Z',
        created_by="ai",
        reconciliation_status="unmatched"
    )


@st.composite
def bank_transaction_strategy(draw):
    """Generate a valid BankTransaction entity."""
    date = draw(st.dates(min_value=datetime(2020, 1, 1).date(), max_value=datetime(2025, 12, 31).date()))
    amount = draw(st.decimals(min_value=Decimal("0.01"), max_value=Decimal("10000.00"), places=2))
    description = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    
    return BankTransaction(
        user_id="test_user",
        bank_transaction_id=f"bank_{draw(st.integers(min_value=1, max_value=999999))}",
        date=date.strftime('%Y-%m-%d'),
        amount=amount,
        currency="USD",
        description=description,
        reconciliation_status="unmatched",
        imported_at=datetime.utcnow().isoformat() + 'Z'
    )


@st.composite
def matching_pair_strategy(draw):
    """Generate a matching transaction and bank transaction pair."""
    date = draw(st.dates(min_value=datetime(2020, 1, 1).date(), max_value=datetime(2025, 12, 31).date()))
    amount = draw(st.decimals(min_value=Decimal("0.01"), max_value=Decimal("10000.00"), places=2))
    vendor = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))))
    
    # Create transaction
    transaction = Transaction(
        user_id="test_user",
        transaction_id=f"txn_{draw(st.integers(min_value=1, max_value=999999))}",
        date=date.strftime('%Y-%m-%d'),
        amount=amount,
        currency="USD",
        type="expense",
        category="Test Category",
        vendor=vendor,
        description="Test transaction",
        classification_confidence=0.9,
        classification_reasoning="Test reasoning",
        status="approved",
        created_at=datetime.utcnow().isoformat() + 'Z',
        updated_at=datetime.utcnow().isoformat() + 'Z',
        created_by="ai",
        reconciliation_status="unmatched"
    )
    
    # Create matching bank transaction with same date, amount, and similar vendor
    bank_transaction = BankTransaction(
        user_id="test_user",
        bank_transaction_id=f"bank_{draw(st.integers(min_value=1, max_value=999999))}",
        date=date.strftime('%Y-%m-%d'),
        amount=amount,
        currency="USD",
        description=vendor,  # Exact match for high confidence
        reconciliation_status="unmatched",
        imported_at=datetime.utcnow().isoformat() + 'Z'
    )
    
    return transaction, bank_transaction


class TestProperty11HighConfidenceAutoMatching:
    """
    Property 11: High Confidence Auto-Matching
    
    For any bank transaction and receipt pair with a match confidence score above 0.8,
    the system should automatically link them without requiring approval.
    
    Validates: Requirements 4.2
    """
    
    @settings(max_examples=100, deadline=None)
    @given(pair=matching_pair_strategy())
    @patch('src.lambdas.reconciliation_engine.handler.DynamoDBRepository')
    def test_property_high_confidence_auto_link(self, mock_repo_class, pair):
        """
        **Validates: Requirements 4.2**
        
        For any matching pair with high confidence (> 0.8), the system should auto-link.
        """
        transaction, bank_transaction = pair
        
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Calculate confidence
        confidence = calculate_match_confidence(transaction, bank_transaction)
        
        # If confidence > 0.8, reconciliation should auto-link
        if confidence > 0.8:
            result = reconcile_transaction(transaction, [bank_transaction], mock_repo)
            
            # Verify auto-linking behavior
            assert result['status'] == 'auto_linked', \
                f"Expected auto_linked for confidence {confidence:.2f}, got {result['status']}"
            assert result['confidence'] > 0.8
            assert mock_repo.update_transaction.called, \
                "Transaction should be updated when auto-linking"
            assert mock_repo.update_bank_transaction.called, \
                "Bank transaction should be updated when auto-linking"
            
            # Verify the transaction was updated with correct status
            updated_txn = mock_repo.update_transaction.call_args[0][0]
            assert updated_txn.reconciliation_status == 'matched'
            assert updated_txn.matched_bank_transaction_id == bank_transaction.bank_transaction_id


class TestProperty12MediumConfidenceApprovalRequirement:
    """
    Property 12: Medium Confidence Approval Requirement
    
    For any bank transaction and receipt pair with a match confidence score between 0.5 and 0.8,
    the system should flag the match for SME owner approval rather than auto-linking.
    
    Validates: Requirements 4.3
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        transaction=transaction_strategy(),
        bank_transaction=bank_transaction_strategy()
    )
    @patch('src.lambdas.reconciliation_engine.handler.DynamoDBRepository')
    def test_property_medium_confidence_requires_approval(self, mock_repo_class, transaction, bank_transaction):
        """
        **Validates: Requirements 4.3**
        
        For any pair with medium confidence (0.5 <= confidence <= 0.8),
        the system should flag for approval.
        """
        # Setup mock repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Calculate confidence
        confidence = calculate_match_confidence(transaction, bank_transaction)
        
        # If confidence is in the approval range, should flag for review
        if 0.5 <= confidence <= 0.8:
            result = reconcile_transaction(transaction, [bank_transaction], mock_repo)
            
            # Verify flagging behavior
            assert result['status'] == 'pending_approval', \
                f"Expected pending_approval for confidence {confidence:.2f}, got {result['status']}"
            assert 0.5 <= result['confidence'] <= 0.8
            assert mock_repo.update_transaction.called, \
                "Transaction should be updated when flagging for approval"
            
            # Verify the transaction was updated with correct status
            updated_txn = mock_repo.update_transaction.call_args[0][0]
            assert updated_txn.reconciliation_status == 'pending_review'
            
            # Bank transaction should NOT be updated (waiting for approval)
            assert not mock_repo.update_bank_transaction.called, \
                "Bank transaction should not be updated when flagging for approval"


class TestProperty13UnmatchedTransactionIdentification:
    """
    Property 13: Unmatched Transaction Identification
    
    For any bank transaction that remains unmatched for more than 7 days,
    the system should identify it as requiring attention.
    
    Validates: Requirements 4.4
    """
    
    @settings(max_examples=100)
    @given(
        days_old=st.integers(min_value=0, max_value=30),
        amount=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("10000.00"), places=2),
        description=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))
    )
    def test_property_unmatched_identification(self, days_old, amount, description):
        """
        **Validates: Requirements 4.4**
        
        For any unmatched bank transaction older than 7 days,
        the system should identify it as requiring attention.
        """
        # Create bank transaction with specified age
        transaction_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
        
        bank_transaction = BankTransaction(
            user_id="test_user",
            bank_transaction_id="bank_test",
            date=transaction_date,
            amount=amount,
            currency="USD",
            description=description,
            reconciliation_status="unmatched",
            imported_at=datetime.utcnow().isoformat() + 'Z'
        )
        
        # Identify unmatched transactions
        unmatched = identify_unmatched_transactions([bank_transaction])
        
        # Verify identification logic
        # Requirement 4.4: unmatched transactions > 7 days old
        if days_old > 7:
            assert len(unmatched) == 1, \
                f"Transaction {days_old} days old should be identified as unmatched"
            assert unmatched[0].bank_transaction_id == bank_transaction.bank_transaction_id
        elif days_old == 7:
            # Exactly 7 days is a boundary - not "more than 7 days"
            assert len(unmatched) == 0, \
                f"Transaction exactly 7 days old should NOT be identified (requirement says > 7 days)"
        else:
            assert len(unmatched) == 0, \
                f"Transaction {days_old} days old should NOT be identified as unmatched"
    
    @settings(max_examples=100)
    @given(
        days_old=st.integers(min_value=8, max_value=30),
        reconciliation_status=st.sampled_from(['unmatched', 'matched', 'pending_review'])
    )
    def test_property_only_unmatched_status_identified(self, days_old, reconciliation_status):
        """
        **Validates: Requirements 4.4**
        
        Only transactions with 'unmatched' status should be identified,
        regardless of age.
        """
        transaction_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
        
        bank_transaction = BankTransaction(
            user_id="test_user",
            bank_transaction_id="bank_test",
            date=transaction_date,
            amount=Decimal("100.00"),
            currency="USD",
            description="Test transaction",
            reconciliation_status=reconciliation_status,
            imported_at=datetime.utcnow().isoformat() + 'Z'
        )
        
        # Identify unmatched transactions
        unmatched = identify_unmatched_transactions([bank_transaction])
        
        # Only unmatched status should be identified
        if reconciliation_status == 'unmatched':
            assert len(unmatched) == 1, \
                "Unmatched transaction older than 7 days should be identified"
        else:
            assert len(unmatched) == 0, \
                f"Transaction with status '{reconciliation_status}' should not be identified"


class TestConfidenceScoreProperties:
    """Additional properties for confidence score calculation."""
    
    @settings(max_examples=100)
    @given(
        transaction=transaction_strategy(),
        bank_transaction=bank_transaction_strategy()
    )
    def test_confidence_score_range(self, transaction, bank_transaction):
        """
        Confidence score should always be between 0 and 1.
        """
        confidence = calculate_match_confidence(transaction, bank_transaction)
        
        assert 0.0 <= confidence <= 1.0, \
            f"Confidence score {confidence} is outside valid range [0, 1]"
    
    @settings(max_examples=100)
    @given(pair=matching_pair_strategy())
    def test_identical_match_high_confidence(self, pair):
        """
        Identical matches (same date, amount, vendor) should have high confidence.
        """
        transaction, bank_transaction = pair
        
        confidence = calculate_match_confidence(transaction, bank_transaction)
        
        # Identical matches should have confidence > 0.8
        assert confidence > 0.8, \
            f"Identical match should have high confidence, got {confidence:.2f}"
