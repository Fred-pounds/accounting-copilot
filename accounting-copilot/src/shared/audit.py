"""
Audit logging utilities for Lambda functions.
"""

import json
import boto3
from typing import Dict, Any, Optional
from shared.logger import setup_logger

logger = setup_logger(__name__)

# Lambda client for invoking audit logger (lazy-loaded)
_lambda_client = None

# Audit logger function name (from environment or default)
import os
AUDIT_LOGGER_FUNCTION = os.environ.get('AUDIT_LOGGER_FUNCTION', 'AuditLogger')


def get_lambda_client():
    """Get or create Lambda client."""
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client('lambda')
    return _lambda_client


def log_audit_entry(
    user_id: str,
    action_type: str,
    actor: str = 'ai',
    actor_details: str = 'system',
    subject_type: str = '',
    subject_id: str = '',
    action_details: Optional[Dict[str, Any]] = None,
    result: str = 'success',
    async_invoke: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Log an audit trail entry by invoking the audit logger Lambda.
    
    Args:
        user_id: User ID
        action_type: Type of action (classification, reconciliation, assistant_query, etc.)
        actor: Who performed the action (ai, user)
        actor_details: Additional actor information (e.g., bedrock model ID)
        subject_type: Type of subject (transaction, document, etc.)
        subject_id: ID of the subject
        action_details: Additional action details (confidence, reasoning, etc.)
        result: Result of the action (success, error)
        async_invoke: If True, invoke asynchronously (fire and forget)
        
    Returns:
        Response from audit logger (None if async_invoke=True)
    """
    try:
        payload = {
            'user_id': user_id,
            'action_type': action_type,
            'actor': actor,
            'actor_details': actor_details,
            'subject_type': subject_type,
            'subject_id': subject_id,
            'action_details': action_details or {},
            'result': result
        }
        
        invocation_type = 'Event' if async_invoke else 'RequestResponse'
        
        lambda_client = get_lambda_client()
        response = lambda_client.invoke(
            FunctionName=AUDIT_LOGGER_FUNCTION,
            InvocationType=invocation_type,
            Payload=json.dumps(payload)
        )
        
        if async_invoke:
            logger.info(f"Audit entry logged asynchronously: {action_type}")
            return None
        else:
            result = json.loads(response['Payload'].read())
            logger.info(f"Audit entry logged: {result.get('action_id')}")
            return result
            
    except Exception as e:
        # Don't fail the main operation if audit logging fails
        logger.error(f"Failed to log audit entry: {e}")
        return None


def log_classification_audit(
    user_id: str,
    transaction_id: str,
    category: str,
    confidence: float,
    reasoning: str,
    actor_details: str = 'bedrock:claude-3-haiku'
) -> None:
    """
    Log a classification action to the audit trail.
    
    Args:
        user_id: User ID
        transaction_id: Transaction ID
        category: Assigned category
        confidence: Classification confidence score
        reasoning: Classification reasoning
        actor_details: AI model used for classification
    """
    log_audit_entry(
        user_id=user_id,
        action_type='classification',
        actor='ai',
        actor_details=actor_details,
        subject_type='transaction',
        subject_id=transaction_id,
        action_details={
            'category': category,
            'confidence': confidence,
            'reasoning': reasoning
        },
        result='success'
    )


def log_reconciliation_audit(
    user_id: str,
    transaction_id: str,
    bank_transaction_id: str,
    match_confidence: float,
    match_status: str
) -> None:
    """
    Log a reconciliation action to the audit trail.
    
    Args:
        user_id: User ID
        transaction_id: Receipt transaction ID
        bank_transaction_id: Bank transaction ID
        match_confidence: Match confidence score
        match_status: Match status (auto_linked, pending_approval, no_match)
    """
    log_audit_entry(
        user_id=user_id,
        action_type='reconciliation',
        actor='ai',
        actor_details='reconciliation_engine',
        subject_type='transaction',
        subject_id=transaction_id,
        action_details={
            'bank_transaction_id': bank_transaction_id,
            'match_confidence': match_confidence,
            'match_status': match_status
        },
        result='success'
    )


def log_assistant_query_audit(
    user_id: str,
    question: str,
    answer: str,
    confidence: float,
    citations: list,
    actor_details: str = 'bedrock:claude-3-haiku'
) -> None:
    """
    Log a financial assistant query to the audit trail.
    
    Args:
        user_id: User ID
        question: User's question
        answer: Assistant's answer
        confidence: Answer confidence score
        citations: List of cited transaction IDs or data points
        actor_details: AI model used for answering
    """
    log_audit_entry(
        user_id=user_id,
        action_type='assistant_query',
        actor='ai',
        actor_details=actor_details,
        subject_type='conversation',
        subject_id='',
        action_details={
            'question': question,
            'answer': answer[:500],  # Truncate long answers
            'confidence': confidence,
            'citations': citations
        },
        result='success'
    )


def log_approval_audit(
    user_id: str,
    subject_type: str,
    subject_id: str,
    approval_action: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a human approval action to the audit trail.
    
    Args:
        user_id: User ID
        subject_type: Type of subject being approved (transaction, vendor, etc.)
        subject_id: ID of the subject
        approval_action: Action taken (approved, rejected, corrected)
        details: Additional details about the approval
    """
    log_audit_entry(
        user_id=user_id,
        action_type='approval',
        actor='user',
        actor_details=user_id,
        subject_type=subject_type,
        subject_id=subject_id,
        action_details=details or {'action': approval_action},
        result='success'
    )


def log_correction_audit(
    user_id: str,
    transaction_id: str,
    original_category: str,
    corrected_category: str,
    original_confidence: float
) -> None:
    """
    Log a classification correction to the audit trail.
    
    Args:
        user_id: User ID
        transaction_id: Transaction ID
        original_category: Original AI-assigned category
        corrected_category: User-corrected category
        original_confidence: Original classification confidence
    """
    log_audit_entry(
        user_id=user_id,
        action_type='correction',
        actor='user',
        actor_details=user_id,
        subject_type='transaction',
        subject_id=transaction_id,
        action_details={
            'original_category': original_category,
            'corrected_category': corrected_category,
            'original_confidence': original_confidence
        },
        result='success'
    )
