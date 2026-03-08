"""
Lambda function: Audit Logger
Logs all AI and human actions to audit trail.
"""

import json
from typing import Dict, Any, List
from shared.aws_clients import get_dynamodb_table
from shared.models import generate_id, generate_timestamp
from shared.logger import setup_logger

logger = setup_logger(__name__)


def create_audit_entry(
    user_id: str,
    action_type: str,
    actor: str = 'ai',
    actor_details: str = 'system',
    subject_type: str = '',
    subject_id: str = '',
    action_details: Dict[str, Any] = None,
    result: str = 'success'
) -> Dict[str, Any]:
    """
    Create an audit entry dictionary.
    
    Args:
        user_id: User ID
        action_type: Type of action (classification, reconciliation, etc.)
        actor: Who performed the action (ai, user)
        actor_details: Additional actor information
        subject_type: Type of subject (transaction, document, etc.)
        subject_id: ID of the subject
        action_details: Additional action details (confidence, reasoning, etc.)
        result: Result of the action (success, error)
        
    Returns:
        Audit entry dictionary
    """
    action_id = generate_id('audit')
    timestamp = generate_timestamp()
    
    return {
        'PK': f"USER#{user_id}",
        'SK': f"AUDIT#{timestamp}#{action_id}",
        'entity_type': 'audit_entry',
        'action_id': action_id,
        'timestamp': timestamp,
        'action_type': action_type,
        'actor': actor,
        'actor_details': actor_details,
        'subject_type': subject_type,
        'subject_id': subject_id,
        'action_details': action_details or {},
        'result': result
    }


def log_single_entry(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log a single audit entry.
    
    Args:
        event: Audit event data
        
    Returns:
        Result with action_id and timestamp
    """
    user_id = event['user_id']
    action_type = event['action_type']
    
    # Create audit entry
    audit_entry = create_audit_entry(
        user_id=user_id,
        action_type=action_type,
        actor=event.get('actor', 'ai'),
        actor_details=event.get('actor_details', 'system'),
        subject_type=event.get('subject_type', ''),
        subject_id=event.get('subject_id', ''),
        action_details=event.get('action_details', {}),
        result=event.get('result', 'success')
    )
    
    # Save to DynamoDB
    table = get_dynamodb_table()
    table.put_item(Item=audit_entry)
    
    logger.info(f"Audit entry created: {audit_entry['action_id']}")
    
    return {
        'status': 'success',
        'action_id': audit_entry['action_id'],
        'timestamp': audit_entry['timestamp']
    }


def log_batch_entries(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Log multiple audit entries in batch.
    
    Args:
        entries: List of audit event data
        
    Returns:
        Result with count of successful entries
    """
    table = get_dynamodb_table()
    audit_entries = []
    
    # Create all audit entries
    for entry in entries:
        audit_entry = create_audit_entry(
            user_id=entry['user_id'],
            action_type=entry['action_type'],
            actor=entry.get('actor', 'ai'),
            actor_details=entry.get('actor_details', 'system'),
            subject_type=entry.get('subject_type', ''),
            subject_id=entry.get('subject_id', ''),
            action_details=entry.get('action_details', {}),
            result=entry.get('result', 'success')
        )
        audit_entries.append(audit_entry)
    
    # Batch write to DynamoDB (max 25 items per batch)
    success_count = 0
    for i in range(0, len(audit_entries), 25):
        batch = audit_entries[i:i+25]
        
        with table.batch_writer() as writer:
            for audit_entry in batch:
                writer.put_item(Item=audit_entry)
                success_count += 1
    
    logger.info(f"Batch audit entries created: {success_count}")
    
    return {
        'status': 'success',
        'entries_logged': success_count
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Log audit trail entry or entries.
    
    Supports both single entry and batch entry logging.
    
    Args:
        event: Audit event data or list of events
        context: Lambda context
        
    Returns:
        Result
    """
    try:
        logger.info(f"Logging audit entry: {json.dumps(event)}")
        
        # Check if batch mode
        if 'entries' in event:
            # Batch mode
            entries = event['entries']
            if not isinstance(entries, list):
                raise ValueError("entries must be a list")
            
            return log_batch_entries(entries)
        else:
            # Single entry mode
            return log_single_entry(event)
        
    except Exception as e:
        logger.exception("Failed to log audit entry")
        return {
            'status': 'error',
            'error': str(e)
        }
