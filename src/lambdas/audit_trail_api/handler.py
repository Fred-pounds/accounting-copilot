"""
Lambda function: Audit Trail API
Provides audit trail query with filtering and pagination.
"""

import json
import csv
import io
import os
from typing import Dict, Any, Optional, List
from src.shared.response import success_response, error_response
from src.shared.auth import extract_token_from_event, get_user_id_from_token
from src.shared.lambda_auth import authorize_and_extract_user, log_write_access
from src.shared.exceptions import AppError, ValidationError
from src.shared.logger import setup_logger
from src.shared.repository import DynamoDBRepository
from src.shared.entities import AuditEntry

logger = setup_logger(__name__)

# Get table name from environment
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'AccountingCopilot')


def get_repository() -> DynamoDBRepository:
    """Get or create repository instance."""
    return DynamoDBRepository(TABLE_NAME)


def parse_query_parameters(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate query parameters from the event.
    
    Args:
        event: API Gateway event
        
    Returns:
        Dictionary of parsed parameters
        
    Raises:
        ValidationError: If parameters are invalid
    """
    query_params = event.get('queryStringParameters') or {}
    
    # Parse date range filters
    start_date = query_params.get('start_date')
    end_date = query_params.get('end_date')
    
    # Parse action type filter
    action_type = query_params.get('action_type')
    
    # Parse transaction ID filter
    transaction_id = query_params.get('transaction_id')
    
    # Parse pagination parameters
    limit_str = query_params.get('limit', '50')
    try:
        limit = int(limit_str)
        if limit < 1:
            raise ValidationError("Limit must be at least 1")
        if limit > 100:
            limit = 100  # Cap at maximum
    except ValueError:
        raise ValidationError(f"Invalid limit value: {limit_str}")
    
    last_evaluated_key = query_params.get('last_evaluated_key')
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'action_type': action_type,
        'transaction_id': transaction_id,
        'limit': limit,
        'last_evaluated_key': last_evaluated_key
    }


def query_audit_entries(
    user_id: str,
    repository: DynamoDBRepository,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action_type: Optional[str] = None,
    transaction_id: Optional[str] = None,
    limit: int = 50,
    last_evaluated_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query audit entries with filters and pagination.
    
    Args:
        user_id: User ID
        repository: Repository instance
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)
        action_type: Optional action type filter
        transaction_id: Optional transaction ID filter
        limit: Maximum number of entries to return
        last_evaluated_key: Pagination token
        
    Returns:
        Dictionary with audit entries and pagination info
    """
    # Query audit entries using repository
    # The repository method supports start_timestamp, end_timestamp, and action_type
    audit_entries = repository.query_audit_entries(
        user_id=user_id,
        start_timestamp=start_date,
        end_timestamp=end_date,
        action_type=action_type,
        limit=limit
    )
    
    # Apply transaction_id filter if specified (post-query filtering)
    if transaction_id:
        audit_entries = [
            entry for entry in audit_entries
            if entry.subject_id == transaction_id
        ]
    
    # Convert audit entries to dictionaries
    audit_entries_data = []
    for entry in audit_entries:
        entry_dict = {
            'action_id': entry.action_id,
            'timestamp': entry.timestamp,
            'action_type': entry.action_type,
            'actor': entry.actor,
            'subject_type': entry.subject_type,
            'subject_id': entry.subject_id,
            'result': entry.result
        }
        
        if entry.actor_details:
            entry_dict['actor_details'] = entry.actor_details
        if entry.action_details:
            entry_dict['action_details'] = entry.action_details
            
        audit_entries_data.append(entry_dict)
    
    # Prepare pagination info
    pagination = {
        'limit': limit
    }
    
    # If we got the full limit, there might be more results
    # In a real implementation, we'd use DynamoDB's LastEvaluatedKey
    # For now, we'll indicate if there are potentially more results
    if len(audit_entries) == limit:
        # Generate a simple pagination token (in production, use DynamoDB's LastEvaluatedKey)
        if audit_entries:
            last_entry = audit_entries[-1]
            pagination['last_evaluated_key'] = f"{last_entry.timestamp}#{last_entry.action_id}"
    
    return {
        'audit_entries': audit_entries_data,
        'pagination': pagination
    }


def format_audit_entries_as_csv(audit_entries: List[AuditEntry]) -> str:
    """
    Format audit entries as CSV string.
    
    Args:
        audit_entries: List of audit entry objects
        
    Returns:
        CSV formatted string
    """
    # Create CSV in memory
    output = io.StringIO()
    
    # Define CSV headers
    fieldnames = [
        'timestamp',
        'action_type',
        'actor',
        'subject_type',
        'subject_id',
        'result',
        'actor_details',
        'action_details'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Write each audit entry
    for entry in audit_entries:
        row = {
            'timestamp': entry.timestamp,
            'action_type': entry.action_type,
            'actor': entry.actor,
            'subject_type': entry.subject_type,
            'subject_id': entry.subject_id,
            'result': entry.result,
            'actor_details': entry.actor_details or '',
            'action_details': json.dumps(entry.action_details) if entry.action_details else ''
        }
        writer.writerow(row)
    
    # Get CSV string
    csv_content = output.getvalue()
    output.close()
    
    return csv_content


def export_audit_trail_csv(
    user_id: str,
    repository: DynamoDBRepository
) -> str:
    """
    Export all audit entries for a user as CSV.
    
    Args:
        user_id: User ID
        repository: Repository instance
        
    Returns:
        CSV formatted string with all audit entries
    """
    # Query all audit entries (no limit)
    audit_entries = repository.query_audit_entries(
        user_id=user_id,
        start_timestamp=None,
        end_timestamp=None,
        action_type=None,
        limit=None  # No limit - get all entries
    )
    
    # Format as CSV
    csv_content = format_audit_entries_as_csv(audit_entries)
    
    return csv_content


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET /audit-trail endpoint.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.request_id
    
    try:
        logger.info(f"Processing audit trail query: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Log audit trail access
        log_write_access(user_id, 'read', 'audit_trail', 'query')
        
        # Parse query parameters
        params = parse_query_parameters(event)
        
        logger.info(f"Query parameters: {params}")
        
        # Get repository
        repository = get_repository()
        
        # Query audit entries
        result = query_audit_entries(
            user_id=user_id,
            repository=repository,
            start_date=params['start_date'],
            end_date=params['end_date'],
            action_type=params['action_type'],
            transaction_id=params['transaction_id'],
            limit=params['limit'],
            last_evaluated_key=params['last_evaluated_key']
        )
        
        logger.info(f"Retrieved {len(result['audit_entries'])} audit entries for user {user_id}")
        
        return success_response({
            'status': 'success',
            'data': result
        })
        
    except AppError as e:
        logger.error(f"Audit trail query error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)


def lambda_handler_export(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET /audit-trail/export endpoint.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with CSV file
    """
    request_id = context.request_id
    
    try:
        logger.info(f"Processing audit trail CSV export: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Log audit trail export access
        log_write_access(user_id, 'export', 'audit_trail', 'csv')
        
        # Get repository
        repository = get_repository()
        
        # Export audit trail as CSV
        csv_content = export_audit_trail_csv(user_id, repository)
        
        logger.info(f"Exported audit trail CSV for user {user_id}")
        
        # Return CSV response with proper headers
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename="audit_trail.csv"',
                'Access-Control-Allow-Origin': '*'
            },
            'body': csv_content
        }
        
    except AppError as e:
        logger.error(f"Audit trail export error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)
