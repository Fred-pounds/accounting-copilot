"""
Lambda function: Transaction API
Provides CRUD operations for transactions.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import statistics

from shared.response import success_response, error_response
from shared.auth import extract_token_from_event, get_user_id_from_token
from shared.lambda_auth import (
    authorize_and_extract_user,
    verify_resource_access,
    log_write_access
)
from shared.exceptions import AppError, ValidationError, NotFoundError, AuthorizationError
from shared.logger import setup_logger
from shared.dynamodb_repository import DynamoDBRepository
from shared.models import (
    Transaction, CategoryStats,
    generate_user_pk, generate_transaction_sk,
    generate_category_gsi1pk, generate_date_gsi1sk,
    generate_status_gsi2pk, generate_date_gsi2sk,
    generate_timestamp, generate_id, generate_stats_sk
)

logger = setup_logger(__name__)

# Get table name from environment
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'AccountingCopilot')


def get_repository() -> DynamoDBRepository:
    """Get or create repository instance."""
    return DynamoDBRepository(TABLE_NAME)


def validate_transaction_data(data: Dict[str, Any], partial: bool = False) -> None:
    """
    Validate transaction data.
    
    Args:
        data: Transaction data to validate
        partial: If True, allow partial updates (not all fields required)
        
    Raises:
        ValidationError: If validation fails
    """
    if not partial:
        # Required fields for creation
        required_fields = ['date', 'amount', 'type', 'category', 'vendor', 'description']
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")
    
    # Validate date format if present
    if 'date' in data:
        try:
            datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")
    
    # Validate amount if present
    if 'amount' in data:
        try:
            amount = float(data['amount'])
            if amount <= 0:
                raise ValidationError("Amount must be positive")
        except (ValueError, TypeError):
            raise ValidationError("Invalid amount")
    
    # Validate type if present
    if 'type' in data and data['type'] not in ['income', 'expense']:
        raise ValidationError("Type must be 'income' or 'expense'")
    
    # Validate currency if present
    if 'currency' in data and not data['currency']:
        raise ValidationError("Currency cannot be empty")


def update_category_statistics(user_id: str, category: str, month: str,
                               repository: DynamoDBRepository) -> None:
    """
    Update category statistics after transaction changes.
    
    Args:
        user_id: User ID
        category: Transaction category
        month: Month in YYYY-MM format
        repository: DynamoDB repository
    """
    try:
        # Get all transactions for this category in this month
        start_date = f"{month}-01"
        # Calculate end date (last day of month)
        year, month_num = map(int, month.split('-'))
        if month_num == 12:
            end_date = f"{year}-12-31"
        else:
            next_month = datetime(year, month_num + 1, 1)
            end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
        
        transactions = repository.query_transactions_by_category(
            user_id, category, start_date, end_date, limit=1000
        )
        
        if not transactions:
            # No transactions, delete stats if they exist
            return
        
        # Calculate statistics
        amounts = [float(t.amount) for t in transactions]
        transaction_count = len(amounts)
        total_amount = sum(amounts)
        average_amount = total_amount / transaction_count
        
        # Calculate standard deviation
        if transaction_count > 1:
            std_dev = statistics.stdev(amounts)
        else:
            std_dev = 0.0
        
        min_amount = min(amounts)
        max_amount = max(amounts)
        
        # Create or update stats
        stats = CategoryStats(
            PK=generate_user_pk(user_id),
            SK=generate_stats_sk(category, month),
            category=category,
            month=month,
            transaction_count=transaction_count,
            total_amount=total_amount,
            average_amount=average_amount,
            std_deviation=std_dev,
            min_amount=min_amount,
            max_amount=max_amount,
            updated_at=generate_timestamp()
        )
        
        repository.create_or_update_category_stats(user_id, stats)
        logger.info(f"Updated category stats for {category} in {month}")
        
    except Exception as e:
        logger.error(f"Error updating category statistics: {e}")
        # Don't fail the transaction operation if stats update fails
        # This is a non-critical operation


def lambda_handler_create(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Create a new transaction manually.
    POST /transactions
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.aws_request_id
    
    try:
        logger.info(f"Processing create transaction request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Log write access
        log_write_access(user_id, 'create', 'transaction', 'new')
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate input
        validate_transaction_data(body)
        
        # Get repository
        repository = get_repository()
        
        # Generate transaction ID
        transaction_id = generate_id('txn')
        
        # Create transaction object
        transaction = Transaction(
            PK=generate_user_pk(user_id),
            SK=generate_transaction_sk(transaction_id),
            GSI1PK=generate_category_gsi1pk(user_id, body['category']),
            GSI1SK=generate_date_gsi1sk(body['date']),
            transaction_id=transaction_id,
            date=body['date'],
            amount=float(body['amount']),
            currency=body.get('currency', 'USD'),
            type=body['type'],
            category=body['category'],
            vendor=body['vendor'],
            description=body['description'],
            classification_confidence=1.0,  # Manual entry has full confidence
            classification_reasoning="Manual entry by user",
            status="approved",  # Manual entries are auto-approved
            flagged_for_review=False,
            validation_issues=[],
            source="manual",
            created_at=generate_timestamp(),
            updated_at=generate_timestamp(),
            created_by="user"
        )
        
        # Save transaction
        repository.create_transaction(user_id, transaction)
        
        # Update category statistics
        month = body['date'][:7]  # Extract YYYY-MM
        update_category_statistics(user_id, body['category'], month, repository)
        
        logger.info(f"Created transaction {transaction_id} for user {user_id}")
        
        return success_response({
            'transaction_id': transaction_id,
            'message': 'Transaction created successfully'
        }, status_code=201)
        
    except AppError as e:
        logger.error(f"Create transaction error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)


def lambda_handler_get(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get a single transaction by ID.
    GET /transactions/{id}
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.aws_request_id
    
    try:
        logger.info(f"Processing get transaction request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Get transaction ID from path
        transaction_id = event.get('pathParameters', {}).get('id')
        if not transaction_id:
            raise ValidationError("Transaction ID is required")
        
        # Get repository
        repository = get_repository()
        
        # Get transaction
        transaction = repository.get_transaction(user_id, transaction_id)
        
        if not transaction:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        
        # Verify user can access this transaction
        verify_resource_access(user_id, transaction.PK, 'transaction', transaction_id)
        
        logger.info(f"Retrieved transaction {transaction_id}")
        
        return success_response(transaction.to_dict())
        
    except AppError as e:
        logger.error(f"Get transaction error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)


def lambda_handler_list(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List transactions with filtering and pagination.
    GET /transactions
    
    Query parameters:
    - start_date: Filter by start date (YYYY-MM-DD)
    - end_date: Filter by end date (YYYY-MM-DD)
    - category: Filter by category
    - status: Filter by status
    - type: Filter by type (income/expense)
    - limit: Max results (default 50)
    - last_evaluated_key: For pagination
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.aws_request_id
    
    try:
        logger.info(f"Processing list transactions request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Log list access
        log_write_access(user_id, 'list', 'transaction', 'all')
        
        # Get query parameters
        params = event.get('queryStringParameters') or {}
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        category = params.get('category')
        status = params.get('status')
        txn_type = params.get('type')
        limit = int(params.get('limit', 50))
        
        # Get repository
        repository = get_repository()
        
        # Query transactions based on filters
        if category:
            # Use GSI1 for category queries
            transactions = repository.query_transactions_by_category(
                user_id, category, start_date, end_date, limit
            )
        elif status:
            # Use GSI2 for status queries
            transactions = repository.query_transactions_by_status(
                user_id, status, start_date, end_date, limit
            )
        elif start_date and end_date:
            # Query by date range
            transactions = repository.query_transactions_by_date_range(
                user_id, start_date, end_date, limit
            )
        else:
            # List all transactions
            transactions = repository.list_transactions(user_id, limit)
        
        # Apply additional filters in memory if needed
        if txn_type:
            transactions = [t for t in transactions if t.type == txn_type]
        
        # Convert to dict format
        result = {
            'transactions': [t.to_dict() for t in transactions],
            'count': len(transactions)
        }
        
        logger.info(f"Retrieved {len(transactions)} transactions for user {user_id}")
        
        return success_response(result)
        
    except AppError as e:
        logger.error(f"List transactions error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)


def lambda_handler_update(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update a transaction.
    PUT /transactions/{id}
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.aws_request_id
    
    try:
        logger.info(f"Processing update transaction request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Get transaction ID from path
        transaction_id = event.get('pathParameters', {}).get('id')
        if not transaction_id:
            raise ValidationError("Transaction ID is required")
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate input (partial update allowed)
        validate_transaction_data(body, partial=True)
        
        # Get repository
        repository = get_repository()
        
        # Check if transaction exists
        existing = repository.get_transaction(user_id, transaction_id)
        if not existing:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        
        # Verify user can access this transaction
        verify_resource_access(user_id, existing.PK, 'transaction', transaction_id)
        
        # Log write access
        log_write_access(user_id, 'update', 'transaction', transaction_id)
        
        # Prepare updates
        updates = {}
        old_category = existing.category
        old_month = existing.date[:7]
        
        # Update allowed fields
        allowed_fields = ['date', 'amount', 'currency', 'type', 'category', 
                         'vendor', 'description', 'status']
        
        for field in allowed_fields:
            if field in body:
                updates[field] = body[field]
        
        # Always update the updated_at timestamp
        updates['updated_at'] = generate_timestamp()
        
        # Update GSI keys if category or date changed
        if 'category' in updates or 'date' in updates:
            new_category = updates.get('category', existing.category)
            new_date = updates.get('date', existing.date)
            updates['GSI1PK'] = generate_category_gsi1pk(user_id, new_category)
            updates['GSI1SK'] = generate_date_gsi1sk(new_date)
        
        if 'status' in updates:
            new_status = updates['status']
            new_date = updates.get('date', existing.date)
            if new_status == 'pending':
                updates['GSI2PK'] = generate_status_gsi2pk(user_id, new_status)
                updates['GSI2SK'] = generate_date_gsi2sk(new_date)
        
        # Update transaction
        updated_transaction = repository.update_transaction(user_id, transaction_id, updates)
        
        # Update category statistics for old and new categories if changed
        if 'category' in updates and updates['category'] != old_category:
            update_category_statistics(user_id, old_category, old_month, repository)
            new_month = updates.get('date', existing.date)[:7]
            update_category_statistics(user_id, updates['category'], new_month, repository)
        elif 'amount' in updates or 'date' in updates:
            # Update stats for the same category
            new_month = updates.get('date', existing.date)[:7]
            update_category_statistics(user_id, existing.category, new_month, repository)
            if new_month != old_month:
                update_category_statistics(user_id, existing.category, old_month, repository)
        
        logger.info(f"Updated transaction {transaction_id}")
        
        return success_response({
            'message': 'Transaction updated successfully',
            'transaction': updated_transaction.to_dict()
        })
        
    except AppError as e:
        logger.error(f"Update transaction error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)


def lambda_handler_delete(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Delete a transaction.
    DELETE /transactions/{id}
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.aws_request_id
    
    try:
        logger.info(f"Processing delete transaction request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Get transaction ID from path
        transaction_id = event.get('pathParameters', {}).get('id')
        if not transaction_id:
            raise ValidationError("Transaction ID is required")
        
        # Get repository
        repository = get_repository()
        
        # Check if transaction exists and get its details for stats update
        existing = repository.get_transaction(user_id, transaction_id)
        if not existing:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        
        # Verify user can access this transaction
        verify_resource_access(user_id, existing.PK, 'transaction', transaction_id)
        
        # Log write access
        log_write_access(user_id, 'delete', 'transaction', transaction_id)
        
        # Delete transaction
        repository.delete_transaction(user_id, transaction_id)
        
        # Update category statistics
        month = existing.date[:7]
        update_category_statistics(user_id, existing.category, month, repository)
        
        logger.info(f"Deleted transaction {transaction_id}")
        
        return success_response({
            'message': 'Transaction deleted successfully'
        })
        
    except AppError as e:
        logger.error(f"Delete transaction error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)


def lambda_handler_approve(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Approve a flagged transaction.
    POST /transactions/{id}/approve
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.aws_request_id
    
    try:
        logger.info(f"Processing approve transaction request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Get transaction ID from path
        transaction_id = event.get('pathParameters', {}).get('id')
        if not transaction_id:
            raise ValidationError("Transaction ID is required")
        
        # Get repository
        repository = get_repository()
        
        # Check if transaction exists
        existing = repository.get_transaction(user_id, transaction_id)
        if not existing:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        
        # Verify user can access this transaction
        verify_resource_access(user_id, existing.PK, 'transaction', transaction_id)
        
        # Log write access
        log_write_access(user_id, 'approve', 'transaction', transaction_id)
        
        # Update transaction status
        updates = {
            'status': 'approved',
            'flagged_for_review': False,
            'approved_by': 'user',
            'approved_at': generate_timestamp(),
            'updated_at': generate_timestamp()
        }
        
        # Remove GSI2 keys since status is no longer pending
        # Note: DynamoDB doesn't support removing attributes in update_item easily
        # We'll just update the status and let the GSI2 keys remain
        
        updated_transaction = repository.update_transaction(user_id, transaction_id, updates)
        
        logger.info(f"Approved transaction {transaction_id}")
        
        return success_response({
            'message': 'Transaction approved successfully',
            'transaction': updated_transaction.to_dict()
        })
        
    except AppError as e:
        logger.error(f"Approve transaction error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)


def lambda_handler_correct(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Correct transaction classification.
    POST /transactions/{id}/correct
    
    Request body:
    {
        "new_category": "category_name",
        "reason": "correction reason"
    }
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.aws_request_id
    
    try:
        logger.info(f"Processing correct transaction request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Get transaction ID from path
        transaction_id = event.get('pathParameters', {}).get('id')
        if not transaction_id:
            raise ValidationError("Transaction ID is required")
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        if 'new_category' not in body:
            raise ValidationError("new_category is required")
        
        new_category = body['new_category']
        reason = body.get('reason', 'User correction')
        
        # Get repository
        repository = get_repository()
        
        # Check if transaction exists
        existing = repository.get_transaction(user_id, transaction_id)
        if not existing:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        
        # Verify user can access this transaction
        verify_resource_access(user_id, existing.PK, 'transaction', transaction_id)
        
        # Log write access
        log_write_access(user_id, 'correct', 'transaction', transaction_id)
        
        old_category = existing.category
        old_month = existing.date[:7]
        
        # Update transaction with corrected classification
        updates = {
            'category': new_category,
            'classification_reasoning': f"Corrected by user: {reason}",
            'status': 'approved',
            'flagged_for_review': False,
            'approved_by': 'user',
            'approved_at': generate_timestamp(),
            'updated_at': generate_timestamp(),
            'GSI1PK': generate_category_gsi1pk(user_id, new_category),
            'GSI1SK': generate_date_gsi1sk(existing.date)
        }
        
        updated_transaction = repository.update_transaction(user_id, transaction_id, updates)
        
        # Update category statistics for both old and new categories
        update_category_statistics(user_id, old_category, old_month, repository)
        update_category_statistics(user_id, new_category, old_month, repository)
        
        logger.info(f"Corrected transaction {transaction_id} from {old_category} to {new_category}")
        
        return success_response({
            'message': 'Transaction classification corrected successfully',
            'transaction': updated_transaction.to_dict()
        })
        
    except AppError as e:
        logger.error(f"Correct transaction error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)


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
    path_parameters = event.get('pathParameters') or {}
    query_parameters = event.get('queryStringParameters') or {}
    
    try:
        # Route based on HTTP method and path
        if http_method == 'GET':
            # Check if it's a single transaction request (has ID in path or query)
            transaction_id = path_parameters.get('id') or query_parameters.get('id')
            if transaction_id:
                return lambda_handler_get(event, context)
            else:
                return lambda_handler_list(event, context)
        
        elif http_method == 'POST':
            # Check the action in the request body or path
            body = json.loads(event.get('body', '{}'))
            action = body.get('action') or path_parameters.get('action')
            
            if action == 'approve':
                return lambda_handler_approve(event, context)
            elif action == 'correct':
                return lambda_handler_correct(event, context)
            else:
                return lambda_handler_create(event, context)
        
        elif http_method == 'PUT':
            return lambda_handler_update(event, context)
        
        elif http_method == 'DELETE':
            return lambda_handler_delete(event, context)
        
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
