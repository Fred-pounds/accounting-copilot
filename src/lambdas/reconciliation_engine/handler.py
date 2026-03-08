"""
Lambda function: Reconciliation Engine
Matches receipts with bank transactions using fuzzy matching.
"""

import json
import os
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from shared.logger import setup_logger
from shared.repository import DynamoDBRepository
from shared.entities import Transaction, BankTransaction
from shared.exceptions import AppError
from shared.aws_clients import get_sns_client
from shared.audit import log_reconciliation_audit

logger = setup_logger(__name__)

# Configuration
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'AccountingCopilot')
REGION = os.environ.get('AWS_REGION', 'us-east-1')
SNS_TOPIC_ARN = os.environ.get('UNMATCHED_TRANSACTIONS_TOPIC_ARN', '')

# Matching thresholds
AUTO_LINK_THRESHOLD = 0.8
APPROVAL_THRESHOLD_MIN = 0.5
APPROVAL_THRESHOLD_MAX = 0.8
UNMATCHED_DAYS_THRESHOLD = 7

# Matching weights
AMOUNT_WEIGHT = 0.4
DATE_WEIGHT = 0.3
VENDOR_WEIGHT = 0.3


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Levenshtein distance
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def calculate_vendor_similarity(vendor1: str, vendor2: str) -> float:
    """
    Calculate vendor name similarity using Levenshtein distance.
    
    Args:
        vendor1: First vendor name
        vendor2: Second vendor name
        
    Returns:
        Similarity score between 0 and 1
    """
    # Normalize: lowercase and strip whitespace
    v1 = vendor1.lower().strip()
    v2 = vendor2.lower().strip()
    
    if not v1 or not v2:
        return 0.0
    
    # Calculate Levenshtein distance
    distance = levenshtein_distance(v1, v2)
    max_len = max(len(v1), len(v2))
    
    # Convert to similarity score (1 - normalized distance)
    similarity = 1.0 - (distance / max_len)
    
    return max(0.0, min(1.0, similarity))


def calculate_amount_similarity(amount1: Decimal, amount2: Decimal) -> float:
    """
    Calculate amount similarity with ±5% tolerance.
    
    Args:
        amount1: First amount
        amount2: Second amount
        
    Returns:
        Similarity score between 0 and 1
    """
    if amount1 == 0 or amount2 == 0:
        return 1.0 if amount1 == amount2 else 0.0
    
    # Calculate percentage difference
    diff = abs(amount1 - amount2)
    avg = (amount1 + amount2) / 2
    percent_diff = float(diff / avg)
    
    # Within 5% tolerance gets full score
    if percent_diff <= 0.05:
        return 1.0
    
    # Linear decay from 5% to 20% difference
    if percent_diff <= 0.20:
        return 1.0 - ((percent_diff - 0.05) / 0.15)
    
    return 0.0


def calculate_date_proximity(date1: str, date2: str) -> float:
    """
    Calculate date proximity with ±3 days tolerance.
    
    Args:
        date1: First date (YYYY-MM-DD)
        date2: Second date (YYYY-MM-DD)
        
    Returns:
        Similarity score between 0 and 1
    """
    try:
        d1 = datetime.strptime(date1, '%Y-%m-%d')
        d2 = datetime.strptime(date2, '%Y-%m-%d')
        
        days_diff = abs((d1 - d2).days)
        
        # Within 3 days gets full score
        if days_diff <= 3:
            return 1.0
        
        # Linear decay from 3 to 7 days
        if days_diff <= 7:
            return 1.0 - ((days_diff - 3) / 4)
        
        return 0.0
        
    except ValueError:
        logger.warning(f"Invalid date format: {date1} or {date2}")
        return 0.0


def calculate_match_confidence(
    transaction: Transaction,
    bank_transaction: BankTransaction
) -> float:
    """
    Calculate overall match confidence score.
    
    Args:
        transaction: Receipt transaction
        bank_transaction: Bank transaction
        
    Returns:
        Confidence score between 0 and 1
    """
    # Calculate individual similarities
    amount_sim = calculate_amount_similarity(transaction.amount, bank_transaction.amount)
    date_sim = calculate_date_proximity(transaction.date, bank_transaction.date)
    vendor_sim = calculate_vendor_similarity(transaction.vendor, bank_transaction.description)
    
    # Weighted average
    confidence = (
        amount_sim * AMOUNT_WEIGHT +
        date_sim * DATE_WEIGHT +
        vendor_sim * VENDOR_WEIGHT
    )
    
    logger.info(
        f"Match confidence: {confidence:.2f} "
        f"(amount: {amount_sim:.2f}, date: {date_sim:.2f}, vendor: {vendor_sim:.2f})"
    )
    
    return confidence


def find_best_match(
    transaction: Transaction,
    bank_transactions: List[BankTransaction]
) -> Optional[Tuple[BankTransaction, float]]:
    """
    Find the best matching bank transaction for a receipt.
    
    Args:
        transaction: Receipt transaction
        bank_transactions: List of unmatched bank transactions
        
    Returns:
        Tuple of (best match, confidence) or None if no match above threshold
    """
    best_match = None
    best_confidence = 0.0
    
    for bank_txn in bank_transactions:
        # Skip already matched transactions
        if bank_txn.reconciliation_status == 'matched':
            continue
        
        confidence = calculate_match_confidence(transaction, bank_txn)
        
        if confidence > best_confidence and confidence >= APPROVAL_THRESHOLD_MIN:
            best_match = bank_txn
            best_confidence = confidence
    
    if best_match:
        return (best_match, best_confidence)
    
    return None


def identify_unmatched_transactions(
    bank_transactions: List[BankTransaction]
) -> List[BankTransaction]:
    """
    Identify unmatched bank transactions older than 7 days.
    
    Args:
        bank_transactions: List of bank transactions
        
    Returns:
        List of unmatched transactions older than threshold
    """
    # Calculate threshold date (strip time to compare dates only)
    threshold_date = (datetime.now() - timedelta(days=UNMATCHED_DAYS_THRESHOLD)).replace(hour=0, minute=0, second=0, microsecond=0)
    unmatched = []
    
    for bank_txn in bank_transactions:
        if bank_txn.reconciliation_status != 'unmatched':
            continue
        
        try:
            txn_date = datetime.strptime(bank_txn.date, '%Y-%m-%d')
            # Only include transactions strictly older than threshold (> 7 days, not >= 7 days)
            if txn_date < threshold_date:
                unmatched.append(bank_txn)
        except ValueError:
            logger.warning(f"Invalid date format for bank transaction: {bank_txn.bank_transaction_id}")
    
    return unmatched


def send_unmatched_notification(unmatched_transactions: List[BankTransaction]) -> None:
    """
    Send SNS notification for unmatched transactions.
    
    Args:
        unmatched_transactions: List of unmatched transactions
    """
    if not unmatched_transactions or not SNS_TOPIC_ARN:
        return
    
    try:
        sns = get_sns_client()
        
        message = f"Found {len(unmatched_transactions)} unmatched bank transactions older than {UNMATCHED_DAYS_THRESHOLD} days:\n\n"
        
        for txn in unmatched_transactions[:10]:  # Limit to first 10
            message += f"- {txn.date}: ${txn.amount} - {txn.description}\n"
        
        if len(unmatched_transactions) > 10:
            message += f"\n... and {len(unmatched_transactions) - 10} more"
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Unmatched Bank Transactions Require Attention",
            Message=message
        )
        
        logger.info(f"Sent notification for {len(unmatched_transactions)} unmatched transactions")
        
    except Exception as e:
        logger.error(f"Failed to send SNS notification: {e}")


def reconcile_transaction(
    transaction: Transaction,
    bank_transactions: List[BankTransaction],
    repository: DynamoDBRepository
) -> Dict[str, Any]:
    """
    Reconcile a single transaction with bank transactions.
    
    Args:
        transaction: Receipt transaction to reconcile
        bank_transactions: List of bank transactions
        repository: DynamoDB repository
        
    Returns:
        Reconciliation result
    """
    # Find best match
    match_result = find_best_match(transaction, bank_transactions)
    
    if not match_result:
        return {
            'transaction_id': transaction.transaction_id,
            'status': 'no_match',
            'confidence': 0.0
        }
    
    bank_txn, confidence = match_result
    
    # Auto-link if confidence > 0.8
    if confidence > AUTO_LINK_THRESHOLD:
        transaction.reconciliation_status = 'matched'
        transaction.matched_bank_transaction_id = bank_txn.bank_transaction_id
        transaction.updated_at = datetime.utcnow().isoformat() + 'Z'
        
        bank_txn.reconciliation_status = 'matched'
        bank_txn.matched_transaction_id = transaction.transaction_id
        bank_txn.match_confidence = confidence
        
        repository.update_transaction(transaction)
        repository.update_bank_transaction(bank_txn)
        
        logger.info(
            f"Auto-linked transaction {transaction.transaction_id} "
            f"with bank transaction {bank_txn.bank_transaction_id} "
            f"(confidence: {confidence:.2f})"
        )
        
        # Log to audit trail
        log_reconciliation_audit(
            user_id=transaction.user_id,
            transaction_id=transaction.transaction_id,
            bank_transaction_id=bank_txn.bank_transaction_id,
            match_confidence=confidence,
            match_status='auto_linked'
        )
        
        return {
            'transaction_id': transaction.transaction_id,
            'bank_transaction_id': bank_txn.bank_transaction_id,
            'status': 'auto_linked',
            'confidence': confidence
        }
    
    # Flag for approval if confidence between 0.5 and 0.8
    elif APPROVAL_THRESHOLD_MIN <= confidence <= APPROVAL_THRESHOLD_MAX:
        transaction.reconciliation_status = 'pending_review'
        transaction.updated_at = datetime.utcnow().isoformat() + 'Z'
        
        repository.update_transaction(transaction)
        
        logger.info(
            f"Flagged transaction {transaction.transaction_id} "
            f"for approval with bank transaction {bank_txn.bank_transaction_id} "
            f"(confidence: {confidence:.2f})"
        )
        
        # Log to audit trail
        log_reconciliation_audit(
            user_id=transaction.user_id,
            transaction_id=transaction.transaction_id,
            bank_transaction_id=bank_txn.bank_transaction_id,
            match_confidence=confidence,
            match_status='pending_approval'
        )
        
        return {
            'transaction_id': transaction.transaction_id,
            'bank_transaction_id': bank_txn.bank_transaction_id,
            'status': 'pending_approval',
            'confidence': confidence
        }
    
    return {
        'transaction_id': transaction.transaction_id,
        'status': 'no_match',
        'confidence': confidence
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Reconcile receipts with bank transactions.
    
    Args:
        event: Step Functions event containing user_id and optional transaction_id
        context: Lambda context
        
    Returns:
        Reconciliation result
    """
    try:
        logger.info(f"Processing reconciliation request: {json.dumps(event)}")
        
        user_id = event.get('user_id')
        if not user_id:
            raise AppError("user_id is required")
        
        repository = DynamoDBRepository(TABLE_NAME, REGION)
        
        # Get unmatched transactions (receipts)
        transactions, _ = repository.list_transactions(user_id, limit=100)
        unmatched_transactions = [
            t for t in transactions
            if t.reconciliation_status in ['unmatched', None]
        ]
        
        # Get bank transactions
        bank_transactions, _ = repository.list_bank_transactions(user_id, limit=100)
        
        logger.info(
            f"Found {len(unmatched_transactions)} unmatched transactions "
            f"and {len(bank_transactions)} bank transactions"
        )
        
        # Reconcile each transaction
        results = []
        auto_linked = 0
        pending_review = 0
        
        for transaction in unmatched_transactions:
            result = reconcile_transaction(transaction, bank_transactions, repository)
            results.append(result)
            
            if result['status'] == 'auto_linked':
                auto_linked += 1
            elif result['status'] == 'pending_approval':
                pending_review += 1
        
        # Identify and notify about old unmatched bank transactions
        unmatched_bank_txns = identify_unmatched_transactions(bank_transactions)
        if unmatched_bank_txns:
            send_unmatched_notification(unmatched_bank_txns)
        
        response = {
            'status': 'success',
            'user_id': user_id,
            'matches_found': auto_linked + pending_review,
            'auto_linked': auto_linked,
            'pending_review': pending_review,
            'unmatched_old_transactions': len(unmatched_bank_txns),
            'results': results
        }
        
        logger.info(f"Reconciliation completed: {json.dumps(response)}")
        return response
        
    except AppError as e:
        logger.error(f"Application error: {e.message}")
        return {
            'status': 'error',
            'error': e.message,
            'error_code': e.status_code
        }
    except Exception as e:
        logger.exception("Reconciliation failed")
        return {
            'status': 'error',
            'error': str(e)
        }
