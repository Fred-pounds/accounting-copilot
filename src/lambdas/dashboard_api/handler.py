"""
Lambda function: Dashboard API
Provides dashboard data and financial summaries.
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
from shared.response import success_response, error_response
from shared.auth import extract_token_from_event, get_user_id_from_token
from shared.lambda_auth import authorize_and_extract_user, log_write_access
from shared.exceptions import AppError, AuthenticationError, AuthorizationError
from shared.logger import setup_logger
from shared.dynamodb_repository import DynamoDBRepository

logger = setup_logger(__name__)

# Get table name from environment
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'AccountingCopilot')


def get_repository() -> DynamoDBRepository:
    """Get or create repository instance."""
    return DynamoDBRepository(TABLE_NAME)


def calculate_dashboard_data(user_id: str, repository: DynamoDBRepository = None) -> Dict[str, Any]:
    """
    Calculate dashboard data for a user.
    
    Args:
        user_id: User ID
        repository: Optional DynamoDBRepository instance (for testing)
        
    Returns:
        Dashboard data dictionary
    """
    # Use provided repository or create new one
    if repository is None:
        repository = get_repository()
    
    # Get current date and calculate date ranges
    now = datetime.utcnow()
    current_month_start = now.replace(day=1).strftime('%Y-%m-%d')
    # Get last day of current month
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    current_month_end = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Calculate start date for 6 months ago
    six_months_ago = now - timedelta(days=180)
    six_months_start = six_months_ago.replace(day=1).strftime('%Y-%m-%d')
    
    # Query all transactions (we'll filter in memory for simplicity)
    # In production, you might want to use date range queries for better performance
    all_transactions = repository.list_transactions(user_id, limit=1000)
    
    # Calculate cash balance (all time)
    cash_balance = Decimal('0')
    for txn in all_transactions:
        if txn.type == 'income':
            cash_balance += Decimal(str(txn.amount))
        elif txn.type == 'expense':
            cash_balance -= Decimal(str(txn.amount))
    
    # Calculate current month income and expenses
    current_month_income = Decimal('0')
    current_month_expenses = Decimal('0')
    current_month_category_totals = defaultdict(Decimal)
    
    for txn in all_transactions:
        if txn.date >= current_month_start and txn.date <= current_month_end:
            if txn.type == 'income':
                current_month_income += Decimal(str(txn.amount))
            elif txn.type == 'expense':
                current_month_expenses += Decimal(str(txn.amount))
                current_month_category_totals[txn.category] += Decimal(str(txn.amount))
    
    # Calculate monthly profit for last 6 months
    monthly_data = defaultdict(lambda: {'income': Decimal('0'), 'expenses': Decimal('0')})
    
    for txn in all_transactions:
        if txn.date >= six_months_start:
            # Extract year-month from date
            month_key = txn.date[:7]  # YYYY-MM format
            
            if txn.type == 'income':
                monthly_data[month_key]['income'] += Decimal(str(txn.amount))
            elif txn.type == 'expense':
                monthly_data[month_key]['expenses'] += Decimal(str(txn.amount))
    
    # Generate profit trend for last 6 months
    profit_trend = []
    for i in range(6):
        month_date = now - timedelta(days=30 * i)
        month_key = month_date.strftime('%Y-%m')
        
        income = monthly_data[month_key]['income']
        expenses = monthly_data[month_key]['expenses']
        profit = income - expenses
        
        profit_trend.append({
            'month': month_key,
            'income': float(income),
            'expenses': float(expenses),
            'profit': float(profit)
        })
    
    # Reverse to get chronological order (oldest to newest)
    profit_trend.reverse()
    
    # Get top 5 expense categories for current month
    top_categories = sorted(
        [{'category': cat, 'total': float(total)} 
         for cat, total in current_month_category_totals.items()],
        key=lambda x: x['total'],
        reverse=True
    )[:5]
    
    return {
        'cash_balance': float(cash_balance),
        'total_income': float(current_month_income),
        'total_expenses': float(current_month_expenses),
        'profit_trend': profit_trend,
        'top_categories': top_categories
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get dashboard data.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.request_id
    
    try:
        logger.info(f"Processing dashboard request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Log dashboard access
        log_write_access(user_id, 'read', 'dashboard', 'summary')
        
        # Get repository
        repository = get_repository()
        
        # Calculate dashboard data
        dashboard_data = calculate_dashboard_data(user_id, repository)
        
        logger.info(f"Dashboard data calculated for user {user_id}")
        return success_response(dashboard_data)
        
    except AppError as e:
        logger.error(f"Dashboard error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)
