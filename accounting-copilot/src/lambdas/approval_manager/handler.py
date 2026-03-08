"""
Approval management Lambda functions for AI Accounting Copilot.

This module implements approval detection logic and API endpoints for managing
pending approvals (large transactions, new vendors, bulk reclassifications).
"""

import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

from shared.models import (
    PendingApproval,
    Transaction,
    generate_user_pk,
    generate_approval_sk,
    generate_transaction_sk,
    generate_status_gsi2pk,
    generate_date_gsi2sk,
    generate_timestamp,
    generate_id
)
from shared.dynamodb_repository import DynamoDBRepository
from shared.response import success_response, error_response
from shared.lambda_auth import authorize_and_extract_user, log_write_access, verify_resource_access
from shared.exceptions import (
    AppError,
    ValidationError,
    NotFoundError
)
from shared.logger import get_logger
from shared.aws_clients import get_sns_client

logger = get_logger(__name__)

# Repository will be initialized lazily
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'AccountingCopilot')
SNS_TOPIC_ARN = os.environ.get('SNS_APPROVAL_REMINDERS_TOPIC_ARN', '')
_repository = None


def get_repository():
    """Get or create repository instance."""
    global _repository
    if _repository is None:
        _repository = DynamoDBRepository(TABLE_NAME)
    return _repository


def detect_large_transaction(user_id: str, amount: Decimal, transaction_date: str) -> bool:
    """
    Detect if transaction exceeds 10% of average monthly expenses.
    
    Args:
        user_id: User ID
        amount: Transaction amount
        transaction_date: Transaction date (YYYY-MM-DD)
        
    Returns:
        True if transaction is large (> 10% of average monthly expenses)
    """
    try:
        # Calculate date range for last 3 months
        txn_date = datetime.fromisoformat(transaction_date)
        three_months_ago = txn_date - timedelta(days=90)
        start_date = three_months_ago.strftime('%Y-%m-%d')
        end_date = transaction_date
        
        # Query transactions for the last 3 months
        transactions = get_repository().query_transactions_by_date_range(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        # Filter expense transactions only
        expense_transactions = [
            t for t in transactions 
            if t.type == "expense" and t.status == "approved"
        ]
        
        if not expense_transactions:
            # No historical data, consider any transaction > $1000 as large
            return float(amount) > 1000.0
        
        # Calculate average monthly expenses
        total_expenses = sum(float(t.amount) for t in expense_transactions)
        num_months = 3  # We're looking at 3 months
        average_monthly_expenses = total_expenses / num_months
        
        # Check if transaction exceeds 10% of average
        threshold = average_monthly_expenses * 0.10
        is_large = float(amount) > threshold
        
        logger.info(
            f"Large transaction check: amount={amount}, "
            f"avg_monthly={average_monthly_expenses:.2f}, "
            f"threshold={threshold:.2f}, is_large={is_large}"
        )
        
        return is_large
        
    except Exception as e:
        logger.error(f"Error detecting large transaction: {e}")
        # Default to not requiring approval on error
        return False


def detect_new_vendor(user_id: str, vendor: str, transaction_date: str) -> bool:
    """
    Detect if vendor is new (not seen in last 90 days).
    
    Args:
        user_id: User ID
        vendor: Vendor name
        transaction_date: Transaction date (YYYY-MM-DD)
        
    Returns:
        True if vendor is new
    """
    try:
        # Calculate date range for last 90 days
        txn_date = datetime.fromisoformat(transaction_date)
        ninety_days_ago = txn_date - timedelta(days=90)
        start_date = ninety_days_ago.strftime('%Y-%m-%d')
        end_date = transaction_date
        
        # Query transactions for the last 90 days
        transactions = get_repository().query_transactions_by_date_range(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        # Check if vendor exists in historical transactions
        vendor_lower = vendor.lower().strip()
        for txn in transactions:
            if txn.vendor.lower().strip() == vendor_lower:
                logger.info(f"Vendor '{vendor}' found in historical transactions")
                return False
        
        logger.info(f"Vendor '{vendor}' is new (not found in last 90 days)")
        return True
        
    except Exception as e:
        logger.error(f"Error detecting new vendor: {e}")
        # Default to not requiring approval on error
        return False


def detect_bulk_reclassification(transaction_ids: List[str]) -> bool:
    """
    Detect if bulk reclassification operation (>= 2 transactions).
    
    Args:
        transaction_ids: List of transaction IDs being reclassified
        
    Returns:
        True if bulk operation (>= 2 transactions)
    """
    is_bulk = len(transaction_ids) >= 2
    logger.info(f"Bulk reclassification check: count={len(transaction_ids)}, is_bulk={is_bulk}")
    return is_bulk


def create_pending_approval(
    user_id: str,
    approval_type: str,
    subject_type: str,
    subject_id: str,
    details: Dict[str, Any]
) -> PendingApproval:
    """
    Create a pending approval record in DynamoDB.
    
    Args:
        user_id: User ID
        approval_type: Type of approval (large_transaction, new_vendor, bulk_reclassification)
        subject_type: Type of subject (transaction, transactions)
        subject_id: ID of subject (transaction_id or comma-separated IDs)
        details: Additional details about the approval
        
    Returns:
        Created PendingApproval entity
    """
    try:
        approval_id = generate_id("approval")
        created_at = generate_timestamp()
        
        approval = PendingApproval(
            PK=generate_user_pk(user_id),
            SK=generate_approval_sk(approval_id),
            GSI2PK=generate_status_gsi2pk(user_id, "pending"),
            GSI2SK=generate_date_gsi2sk(created_at),
            approval_id=approval_id,
            approval_type=approval_type,
            subject_type=subject_type,
            subject_id=subject_id,
            created_at=created_at,
            status="pending",
            details=details
        )
        
        get_repository().create_pending_approval(user_id, approval)
        logger.info(f"Created pending approval {approval_id} for user {user_id}")
        
        return approval
        
    except Exception as e:
        logger.error(f"Error creating pending approval: {e}")
        raise


def lambda_handler_list_pending(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for GET /approvals/pending endpoint.
    Lists all pending approvals for the authenticated user.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Log list access
        log_write_access(user_id, 'list', 'pending_approval', 'all')
        
        # Query pending approvals using GSI2
        approvals = get_repository().list_pending_approvals(
            user_id=user_id,
            status="pending",
            limit=100
        )
        
        # Convert to response format
        approval_list = []
        for approval in approvals:
            approval_dict = approval.to_dict()
            # Remove internal keys
            approval_dict.pop('PK', None)
            approval_dict.pop('SK', None)
            approval_dict.pop('GSI2PK', None)
            approval_dict.pop('GSI2SK', None)
            approval_list.append(approval_dict)
        
        logger.info(f"Retrieved {len(approval_list)} pending approvals for user {user_id}")
        
        return success_response({
            'approvals': approval_list,
            'count': len(approval_list)
        })
        
    except AppError as e:
        logger.error(f"Application error: {e.message}")
        return error_response(e, context.aws_request_id)
    except Exception as e:
        logger.exception("Unexpected error in list_pending handler")
        error = AppError(f"Internal server error: {str(e)}", status_code=500)
        return error_response(error, context.aws_request_id)


def lambda_handler_approve(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for POST /approvals/{id}/approve endpoint.
    Approves a pending approval and updates related transactions.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Extract approval_id from path parameters
        approval_id = event.get('pathParameters', {}).get('id')
        if not approval_id:
            raise ValidationError("Approval ID is required")
        
        # Get the pending approval
        approval = get_repository().get_pending_approval(user_id, approval_id)
        if not approval:
            raise NotFoundError(f"Approval {approval_id} not found")
        
        # Verify user can access this approval
        verify_resource_access(user_id, approval.PK, 'pending_approval', approval_id)
        
        # Log approve access
        log_write_access(user_id, 'approve', 'pending_approval', approval_id)
        
        # Check if already processed
        if approval.status != "pending":
            raise ValidationError(f"Approval {approval_id} has already been {approval.status}")
        
        # Update approval status
        now = generate_timestamp()
        get_repository().update_pending_approval(
            user_id=user_id,
            approval_id=approval_id,
            updates={
                'status': 'approved',
                'reviewed_at': now,
                'reviewed_by': user_id,
                'GSI2PK': '',  # Remove from pending index
                'GSI2SK': ''
            }
        )
        
        # Update related transactions based on approval type
        if approval.approval_type in ['large_transaction', 'new_vendor']:
            # Single transaction approval
            transaction_id = approval.subject_id
            get_repository().update_transaction(
                user_id=user_id,
                transaction_id=transaction_id,
                updates={
                    'status': 'approved',
                    'approved_by': user_id,
                    'approved_at': now,
                    'flagged_for_review': False,
                    'updated_at': now
                }
            )
            logger.info(f"Approved transaction {transaction_id}")
            
        elif approval.approval_type == 'bulk_reclassification':
            # Multiple transactions approval
            transaction_ids = approval.subject_id.split(',')
            new_category = approval.details.get('new_category', '')
            
            for txn_id in transaction_ids:
                get_repository().update_transaction(
                    user_id=user_id,
                    transaction_id=txn_id.strip(),
                    updates={
                        'category': new_category,
                        'status': 'approved',
                        'approved_by': user_id,
                        'approved_at': now,
                        'updated_at': now
                    }
                )
            logger.info(f"Approved bulk reclassification of {len(transaction_ids)} transactions")
        
        logger.info(f"Approved approval {approval_id} for user {user_id}")
        
        return success_response({
            'message': 'Approval processed successfully',
            'approval_id': approval_id,
            'status': 'approved'
        })
        
    except AppError as e:
        logger.error(f"Application error: {e.message}")
        return error_response(e, context.aws_request_id)
    except Exception as e:
        logger.exception("Unexpected error in approve handler")
        error = AppError(f"Internal server error: {str(e)}", status_code=500)
        return error_response(error, context.aws_request_id)


def lambda_handler_reject(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for POST /approvals/{id}/reject endpoint.
    Rejects a pending approval and updates related transactions.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Extract approval_id from path parameters
        approval_id = event.get('pathParameters', {}).get('id')
        if not approval_id:
            raise ValidationError("Approval ID is required")
        
        # Parse request body for rejection reason (optional)
        body = {}
        if event.get('body'):
            body = json.loads(event['body'])
        rejection_reason = body.get('reason', 'Rejected by user')
        
        # Get the pending approval
        approval = get_repository().get_pending_approval(user_id, approval_id)
        if not approval:
            raise NotFoundError(f"Approval {approval_id} not found")
        
        # Verify user can access this approval
        verify_resource_access(user_id, approval.PK, 'pending_approval', approval_id)
        
        # Log reject access
        log_write_access(user_id, 'reject', 'pending_approval', approval_id)
        
        # Check if already processed
        if approval.status != "pending":
            raise ValidationError(f"Approval {approval_id} has already been {approval.status}")
        
        # Update approval status
        now = generate_timestamp()
        get_repository().update_pending_approval(
            user_id=user_id,
            approval_id=approval_id,
            updates={
                'status': 'rejected',
                'reviewed_at': now,
                'reviewed_by': user_id,
                'rejection_reason': rejection_reason,
                'GSI2PK': '',  # Remove from pending index
                'GSI2SK': ''
            }
        )
        
        # Update related transactions based on approval type
        if approval.approval_type in ['large_transaction', 'new_vendor']:
            # Single transaction rejection
            transaction_id = approval.subject_id
            get_repository().update_transaction(
                user_id=user_id,
                transaction_id=transaction_id,
                updates={
                    'status': 'rejected',
                    'flagged_for_review': False,
                    'updated_at': now
                }
            )
            logger.info(f"Rejected transaction {transaction_id}")
            
        elif approval.approval_type == 'bulk_reclassification':
            # Multiple transactions rejection - no changes needed
            transaction_ids = approval.subject_id.split(',')
            logger.info(f"Rejected bulk reclassification of {len(transaction_ids)} transactions")
        
        logger.info(f"Rejected approval {approval_id} for user {user_id}")
        
        return success_response({
            'message': 'Approval rejected successfully',
            'approval_id': approval_id,
            'status': 'rejected'
        })
        
    except AppError as e:
        logger.error(f"Application error: {e.message}")
        return error_response(e, context.aws_request_id)
    except Exception as e:
        logger.exception("Unexpected error in reject handler")
        error = AppError(f"Internal server error: {str(e)}", status_code=500)
        return error_response(error, context.aws_request_id)


def send_approval_reminder(approval: PendingApproval, user_id: str) -> bool:
    """
    Send SNS reminder notification for a pending approval.
    
    Args:
        approval: PendingApproval entity
        user_id: User ID
        
    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        # Calculate age in hours
        created_at_str = approval.created_at.replace('Z', '')
        created_at = datetime.fromisoformat(created_at_str)
        now = datetime.utcnow()
        age_hours = int((now - created_at).total_seconds() / 3600)
        
        # Build notification message
        message = f"""Pending Approval Reminder

Approval ID: {approval.approval_id}
Type: {approval.approval_type}
Created: {approval.created_at}
Age: {age_hours} hours

Details:
"""
        
        # Add type-specific details
        if approval.approval_type == 'large_transaction':
            amount = approval.details.get('amount', 'N/A')
            reason = approval.details.get('reason', 'N/A')
            message += f"- Amount: ${amount}\n- Reason: {reason}\n"
        elif approval.approval_type == 'new_vendor':
            vendor = approval.details.get('vendor', 'N/A')
            amount = approval.details.get('amount', 'N/A')
            message += f"- Vendor: {vendor}\n- Amount: ${amount}\n"
        elif approval.approval_type == 'bulk_reclassification':
            count = approval.details.get('count', 0)
            new_category = approval.details.get('new_category', 'N/A')
            message += f"- Transaction Count: {count}\n- New Category: {new_category}\n"
        
        # Add transaction IDs
        if approval.subject_type == 'transaction':
            message += f"\nTransaction ID: {approval.subject_id}"
        elif approval.subject_type == 'transactions':
            transaction_ids = approval.subject_id.split(',')
            message += f"\nTransaction IDs: {', '.join(transaction_ids)}"
        
        # Send SNS notification
        sns_client = get_sns_client()
        
        if not SNS_TOPIC_ARN:
            logger.warning("SNS_APPROVAL_REMINDERS_TOPIC_ARN not configured, skipping notification")
            return False
        
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Pending Approval Reminder",
            Message=message
        )
        
        logger.info(f"Sent reminder notification for approval {approval.approval_id}, MessageId: {response.get('MessageId')}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending approval reminder: {e}")
        return False


def lambda_handler_reminder(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for scheduled approval reminder job (runs daily via EventBridge).
    Queries pending approvals older than 48 hours and sends reminder notifications.
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context
        
    Returns:
        Summary of reminders sent
    """
    try:
        logger.info("Starting approval reminder job")
        
        # Calculate cutoff time (48 hours ago)
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=48)
        cutoff_timestamp = cutoff_time.isoformat() + 'Z'
        
        logger.info(f"Querying approvals created before {cutoff_timestamp}")
        
        # Query all pending approvals
        # Note: We need to query all users' pending approvals
        # In a real implementation, we'd need to iterate through users or use a different query pattern
        # For now, we'll assume the event contains user_ids or we query all pending approvals
        
        # Get all pending approvals (this is a simplified approach)
        # In production, you'd want to scan the GSI2 index or maintain a list of active users
        all_approvals = []
        reminders_sent = 0
        reminders_failed = 0
        
        # For this implementation, we'll query by scanning the GSI2 index
        # This assumes we have a way to get all pending approvals across all users
        try:
            response = get_repository().table.scan(
                FilterExpression='entity_type = :entity_type AND #status = :status AND created_at < :cutoff AND (attribute_not_exists(reminder_sent_at) OR reminder_sent_at = :null)',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':entity_type': 'pending_approval',
                    ':status': 'pending',
                    ':cutoff': cutoff_timestamp,
                    ':null': ''
                }
            )
            
            items = response.get('Items', [])
            all_approvals = [PendingApproval(**get_repository()._convert_decimal_to_float(item)) for item in items]
            
            logger.info(f"Found {len(all_approvals)} approvals requiring reminders")
            
            # Send reminders for each approval
            for approval in all_approvals:
                # Extract user_id from PK
                user_id = approval.PK.replace('USER#', '')
                
                # Send reminder
                if send_approval_reminder(approval, user_id):
                    # Update reminder_sent_at timestamp
                    try:
                        get_repository().update_pending_approval(
                            user_id=user_id,
                            approval_id=approval.approval_id,
                            updates={
                                'reminder_sent_at': generate_timestamp()
                            }
                        )
                        reminders_sent += 1
                    except Exception as e:
                        logger.error(f"Error updating reminder_sent_at for approval {approval.approval_id}: {e}")
                        reminders_failed += 1
                else:
                    reminders_failed += 1
            
        except Exception as e:
            logger.error(f"Error scanning for pending approvals: {e}")
            raise
        
        summary = {
            'reminders_sent': reminders_sent,
            'reminders_failed': reminders_failed,
            'total_approvals_checked': len(all_approvals),
            'cutoff_time': cutoff_timestamp
        }
        
        logger.info(f"Approval reminder job completed: {summary}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(summary)
        }
        
    except Exception as e:
        logger.exception("Unexpected error in reminder handler")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }



def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler that routes requests to appropriate handlers.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    try:
        # Check if this is an EventBridge scheduled event for reminders
        if event.get('source') == 'aws.events':
            return lambda_handler_reminder(event, context)
        
        # Route based on HTTP method
        if http_method == 'GET':
            return lambda_handler_list_pending(event, context)
        
        elif http_method == 'POST':
            # Check the action in the request body
            body = json.loads(event.get('body', '{}'))
            action = body.get('action', '')
            
            if action == 'approve':
                return lambda_handler_approve(event, context)
            elif action == 'reject':
                return lambda_handler_reject(event, context)
            else:
                return error_response(
                    AppError(f"Unknown action: {action}. Use 'approve' or 'reject'", status_code=400),
                    context.aws_request_id
                )
        
        else:
            return error_response(
                AppError(f"Unsupported HTTP method: {http_method}", status_code=405),
                context.aws_request_id
            )
    
    except Exception as e:
        logger.exception("Unhandled exception in router")
        return error_response(
            AppError("Internal server error", status_code=500),
            context.aws_request_id
        )
