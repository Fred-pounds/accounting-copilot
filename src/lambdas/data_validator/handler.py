"""
Lambda function: Data Validator
Validates transactions for duplicates, outliers, and data quality issues.
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from shared.config import Config
from shared.aws_clients import get_dynamodb_table, sns_client
from shared.logger import setup_logger

logger = setup_logger(__name__)


def check_duplicate(table, user_id: str, transaction: Dict[str, Any], transaction_id: str) -> bool:
    """
    Check if transaction is a duplicate.
    Duplicate: same amount, vendor, and date within 24 hours.
    Requirements: 3.1
    """
    try:
        amount = float(transaction['amount']) if isinstance(transaction['amount'], Decimal) else transaction['amount']
        vendor = transaction.get('vendor', '')
        date_str = transaction.get('date', '')
        
        if not date_str or not vendor:
            return False
        
        # Parse transaction date
        if 'T' in date_str:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Calculate date range (24 hours before and after)
        date_before = (date - timedelta(days=1)).strftime('%Y-%m-%d')
        date_after = (date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Query all transactions for the user
        response = table.query(
            KeyConditionExpression=Key('PK').eq(f"USER#{user_id}") & Key('SK').begins_with('TXN#')
        )
        
        # Check each transaction for duplicate
        for item in response.get('Items', []):
            # Skip the current transaction
            if item.get('transaction_id') == transaction_id:
                continue
            
            item_amount = float(item.get('amount', 0)) if isinstance(item.get('amount'), Decimal) else item.get('amount', 0)
            item_vendor = item.get('vendor', '')
            item_date_str = item.get('date', '')
            
            # Check if amounts match
            if abs(item_amount - amount) < 0.01:  # Float comparison tolerance
                # Check if vendors match
                if item_vendor == vendor:
                    # Check if dates are within 24 hours
                    if item_date_str:
                        if 'T' in item_date_str:
                            item_date = datetime.fromisoformat(item_date_str.replace('Z', '+00:00'))
                        else:
                            item_date = datetime.strptime(item_date_str, '%Y-%m-%d')
                        
                        time_diff = abs((item_date - date).total_seconds())
                        if time_diff <= 86400:  # 24 hours in seconds
                            logger.info(f"Duplicate found: {item.get('transaction_id')} matches {transaction_id}")
                            return True
        
        return False
    except Exception as e:
        logger.error(f"Duplicate check failed: {str(e)}")
        return False


def check_outlier(table, user_id: str, transaction: Dict[str, Any]) -> bool:
    """
    Check if transaction is an outlier.
    Outlier: amount > 3 standard deviations from category average.
    Requirements: 3.3, 3.4
    """
    try:
        category = transaction.get('category', '')
        amount = float(transaction['amount']) if isinstance(transaction['amount'], Decimal) else transaction['amount']
        
        if not category:
            return False
        
        # Get category statistics for current month
        current_month = datetime.now().strftime('%Y-%m')
        response = table.get_item(
            Key={
                'PK': f"USER#{user_id}",
                'SK': f"STATS#{category}#{current_month}"
            }
        )
        
        if 'Item' in response:
            stats = response['Item']
            transaction_count = int(stats.get('transaction_count', 0))
            
            # Need at least 10 transactions for meaningful statistics
            if transaction_count < 10:
                return False
            
            avg = float(stats.get('average_amount', 0)) if isinstance(stats.get('average_amount'), Decimal) else stats.get('average_amount', 0)
            std_dev = float(stats.get('std_deviation', 0)) if isinstance(stats.get('std_deviation'), Decimal) else stats.get('std_deviation', 0)
            
            if std_dev > 0:
                z_score = abs((amount - avg) / std_dev)
                is_outlier = z_score > Config.OUTLIER_STD_DEVIATION
                if is_outlier:
                    logger.info(f"Outlier detected: amount={amount}, avg={avg}, std_dev={std_dev}, z_score={z_score}")
                return is_outlier
        
        return False
    except Exception as e:
        logger.error(f"Outlier check failed: {str(e)}")
        return False


def extract_invoice_number(description: str) -> Optional[int]:
    """
    Extract invoice number from transaction description.
    Looks for patterns like: INV-123, Invoice #456, #789, etc.
    """
    if not description:
        return None
    
    # Try various invoice number patterns
    patterns = [
        r'INV[-#\s]*(\d+)',
        r'Invoice[-#\s]*(\d+)',
        r'#(\d+)',
        r'No\.?\s*(\d+)',
        r'Number[-#\s]*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return None


def check_invoice_gaps(table, user_id: str, transaction: Dict[str, Any]) -> List[int]:
    """
    Check for missing sequential invoice numbers.
    Requirements: 3.5
    """
    try:
        vendor = transaction.get('vendor', '')
        description = transaction.get('description', '')
        
        if not vendor:
            return []
        
        # Extract invoice number from current transaction
        current_invoice = extract_invoice_number(description)
        if current_invoice is None:
            return []
        
        # Query all transactions for this vendor
        response = table.query(
            KeyConditionExpression=Key('PK').eq(f"USER#{user_id}") & Key('SK').begins_with('TXN#'),
            FilterExpression=Attr('vendor').eq(vendor)
        )
        
        # Extract all invoice numbers
        invoice_numbers = []
        for item in response.get('Items', []):
            item_desc = item.get('description', '')
            invoice_num = extract_invoice_number(item_desc)
            if invoice_num is not None:
                invoice_numbers.append(invoice_num)
        
        # Add current invoice number
        invoice_numbers.append(current_invoice)
        
        # Need at least 2 invoices to detect gaps
        if len(invoice_numbers) < 2:
            return []
        
        # Sort and find gaps
        invoice_numbers = sorted(set(invoice_numbers))
        gaps = []
        
        for i in range(len(invoice_numbers) - 1):
            current = invoice_numbers[i]
            next_num = invoice_numbers[i + 1]
            
            # Check for gaps (missing numbers in sequence)
            if next_num - current > 1:
                # Add all missing numbers
                for missing in range(current + 1, next_num):
                    gaps.append(missing)
        
        if gaps:
            logger.info(f"Invoice gaps detected for vendor {vendor}: {gaps}")
        
        return gaps
    except Exception as e:
        logger.error(f"Invoice gap check failed: {str(e)}")
        return []


def send_notification(topic_arn: str, subject: str, message: str) -> None:
    """
    Send SNS notification.
    Requirements: 3.2, 3.6
    """
    try:
        if not topic_arn:
            logger.warning(f"SNS topic ARN not configured for: {subject}")
            return
        
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        logger.info(f"Notification sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Validate transaction data.
    
    Args:
        event: Step Functions event containing transaction_id and user_id
        context: Lambda context
        
    Returns:
        Validation result with issues found
    """
    try:
        logger.info(f"Processing validation request: {json.dumps(event)}")
        
        transaction_id = event.get('transaction_id')
        user_id = event.get('user_id')
        
        if not transaction_id or not user_id:
            raise ValueError("Missing required fields: transaction_id or user_id")
        
        # Get transaction
        table = get_dynamodb_table()
        response = table.get_item(
            Key={
                'PK': f"USER#{user_id}",
                'SK': f"TXN#{transaction_id}"
            }
        )
        
        if 'Item' not in response:
            raise ValueError(f"Transaction not found: {transaction_id}")
        
        transaction = response['Item']
        issues = []
        notification_messages = []
        
        # Check for duplicate (Requirement 3.1)
        if check_duplicate(table, user_id, transaction, transaction_id):
            issues.append('duplicate_detected')
            logger.warning(f"Duplicate transaction detected: {transaction_id}")
            notification_messages.append(
                f"Duplicate transaction detected:\n"
                f"Transaction ID: {transaction_id}\n"
                f"Amount: {transaction.get('amount')}\n"
                f"Vendor: {transaction.get('vendor')}\n"
                f"Date: {transaction.get('date')}"
            )
        
        # Check for outlier (Requirements 3.3, 3.4)
        if check_outlier(table, user_id, transaction):
            issues.append('outlier_detected')
            logger.warning(f"Outlier transaction detected: {transaction_id}")
            notification_messages.append(
                f"Unusual transaction amount detected:\n"
                f"Transaction ID: {transaction_id}\n"
                f"Amount: {transaction.get('amount')}\n"
                f"Category: {transaction.get('category')}\n"
                f"This amount is more than 3 standard deviations from the category average."
            )
        
        # Check for invoice gaps (Requirement 3.5)
        invoice_gaps = check_invoice_gaps(table, user_id, transaction)
        if invoice_gaps:
            issues.append('invoice_gap_detected')
            logger.warning(f"Invoice gaps detected for transaction {transaction_id}: {invoice_gaps}")
            notification_messages.append(
                f"Missing invoice numbers detected:\n"
                f"Vendor: {transaction.get('vendor')}\n"
                f"Missing invoice numbers: {', '.join(map(str, invoice_gaps))}\n"
                f"Please verify these invoices exist."
            )
        
        # Update transaction with validation issues
        if issues:
            table.update_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': f"TXN#{transaction_id}"
                },
                UpdateExpression='SET validation_issues = :issues, flagged_for_review = :flagged',
                ExpressionAttributeValues={
                    ':issues': issues,
                    ':flagged': True
                }
            )
            
            # Send notifications (Requirements 3.2, 3.6)
            for msg in notification_messages:
                send_notification(
                    Config.SNS_PENDING_APPROVALS,
                    "Transaction Validation Issue Detected",
                    msg
                )
        
        logger.info(f"Validation completed: {len(issues)} issues found")
        
        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'validation_issues': issues,
            'has_issues': len(issues) > 0,
            'invoice_gaps': invoice_gaps if invoice_gaps else []
        }
        
    except Exception as e:
        logger.exception("Unhandled exception in validator")
        return {
            'status': 'error',
            'error': str(e),
            'transaction_id': event.get('transaction_id'),
            'validation_issues': [],
            'has_issues': False
        }
