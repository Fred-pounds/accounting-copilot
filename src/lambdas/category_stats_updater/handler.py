"""
Lambda function: Category Statistics Updater
Maintains category statistics for outlier detection.
Triggered by:
1. DynamoDB Streams on transaction create/update/delete
2. EventBridge scheduled job (daily) for full recalculation
Requirements: 3.3, 3.4
"""

import json
import statistics
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from shared.config import Config
from shared.aws_clients import get_dynamodb_table
from shared.logger import setup_logger
from shared.models import CategoryStats, generate_user_pk, generate_stats_sk, generate_timestamp

logger = setup_logger(__name__)


def calculate_category_statistics(
    user_id: str,
    category: str,
    month: str,
    table
) -> Optional[CategoryStats]:
    """
    Calculate statistics for a category in a given month.
    
    Args:
        user_id: User ID
        category: Transaction category
        month: Month in YYYY-MM format
        table: DynamoDB table resource
        
    Returns:
        CategoryStats object with calculated statistics
    """
    try:
        # Query all transactions for this user, category, and month
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(f"USER#{user_id}#CAT#{category}") & 
                                   Key('GSI1SK').begins_with(f"DATE#{month}")
        )
        
        transactions = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq(f"USER#{user_id}#CAT#{category}") & 
                                       Key('GSI1SK').begins_with(f"DATE#{month}"),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            transactions.extend(response.get('Items', []))
        
        if not transactions:
            logger.info(f"No transactions found for category {category} in month {month}")
            return None
        
        # Extract amounts and convert Decimal to float
        amounts = []
        for txn in transactions:
            amount = txn.get('amount')
            if amount is not None:
                if isinstance(amount, Decimal):
                    amounts.append(float(amount))
                else:
                    amounts.append(float(amount))
        
        if not amounts:
            logger.warning(f"No valid amounts found for category {category} in month {month}")
            return None
        
        # Calculate statistics
        count = len(amounts)
        total = sum(amounts)
        average = statistics.mean(amounts)
        min_amount = min(amounts)
        max_amount = max(amounts)
        
        # Calculate standard deviation (need at least 2 values)
        if count >= 2:
            std_dev = statistics.stdev(amounts)
        else:
            std_dev = 0.0
        
        # Create CategoryStats object
        stats = CategoryStats(
            PK=generate_user_pk(user_id),
            SK=generate_stats_sk(category, month),
            category=category,
            month=month,
            transaction_count=count,
            total_amount=total,
            average_amount=average,
            std_deviation=std_dev,
            min_amount=min_amount,
            max_amount=max_amount,
            updated_at=generate_timestamp()
        )
        
        logger.info(
            f"Calculated stats for {category} in {month}: "
            f"count={count}, avg={average:.2f}, std_dev={std_dev:.2f}"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to calculate statistics for {category} in {month}: {str(e)}")
        return None


def update_category_stats(user_id: str, category: str, month: str, table) -> None:
    """
    Update category statistics in DynamoDB.
    
    Args:
        user_id: User ID
        category: Transaction category
        month: Month in YYYY-MM format
        table: DynamoDB table resource
    """
    try:
        stats = calculate_category_statistics(user_id, category, month, table)
        
        if stats:
            # Convert to DynamoDB format
            item = stats.to_dict()
            
            # Convert floats to Decimal for DynamoDB
            for key, value in item.items():
                if isinstance(value, float):
                    item[key] = Decimal(str(value))
            
            # Put item in DynamoDB
            table.put_item(Item=item)
            
            logger.info(f"Updated category stats for {category} in {month}")
        else:
            # No transactions found, delete stats if they exist
            try:
                table.delete_item(
                    Key={
                        'PK': generate_user_pk(user_id),
                        'SK': generate_stats_sk(category, month)
                    }
                )
                logger.info(f"Deleted empty category stats for {category} in {month}")
            except Exception as e:
                logger.debug(f"No stats to delete for {category} in {month}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Failed to update category stats: {str(e)}")


def process_stream_record(record: Dict[str, Any], table) -> None:
    """
    Process a single DynamoDB Stream record.
    
    Args:
        record: DynamoDB Stream record
        table: DynamoDB table resource
    """
    try:
        event_name = record.get('eventName')
        
        # Only process transaction records
        if event_name in ['INSERT', 'MODIFY', 'REMOVE']:
            # Get the transaction data
            if event_name == 'REMOVE':
                # For DELETE, use OldImage
                image = record.get('dynamodb', {}).get('OldImage', {})
            else:
                # For INSERT/MODIFY, use NewImage
                image = record.get('dynamodb', {}).get('NewImage', {})
            
            # Check if this is a transaction record
            sk = image.get('SK', {}).get('S', '')
            if not sk.startswith('TXN#'):
                return
            
            # Extract user_id, category, and date
            pk = image.get('PK', {}).get('S', '')
            user_id = pk.replace('USER#', '') if pk.startswith('USER#') else None
            
            category = image.get('category', {}).get('S', '')
            date_str = image.get('date', {}).get('S', '')
            
            if not user_id or not category or not date_str:
                logger.warning(f"Missing required fields in stream record: {record}")
                return
            
            # Extract month from date (YYYY-MM)
            if 'T' in date_str:
                month = date_str[:7]  # YYYY-MM from ISO format
            else:
                month = date_str[:7]  # YYYY-MM from YYYY-MM-DD format
            
            logger.info(f"Processing {event_name} for category {category} in month {month}")
            
            # Update statistics for this category and month
            update_category_stats(user_id, category, month, table)
            
    except Exception as e:
        logger.error(f"Failed to process stream record: {str(e)}")


def lambda_handler_stream(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for DynamoDB Stream events.
    Triggered when transactions are created, updated, or deleted.
    
    Args:
        event: DynamoDB Stream event
        context: Lambda context
        
    Returns:
        Processing result
    """
    try:
        logger.info(f"Processing {len(event.get('Records', []))} stream records")
        
        table = get_dynamodb_table()
        
        # Process each record
        for record in event.get('Records', []):
            process_stream_record(record, table)
        
        logger.info("Stream processing completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Statistics updated successfully',
                'records_processed': len(event.get('Records', []))
            })
        }
        
    except Exception as e:
        logger.exception("Unhandled exception in stream handler")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def recalculate_all_statistics(user_id: str, table) -> Dict[str, int]:
    """
    Recalculate all category statistics for a user.
    Used by the scheduled job to ensure data consistency.
    
    Args:
        user_id: User ID
        table: DynamoDB table resource
        
    Returns:
        Dictionary with counts of categories and months processed
    """
    try:
        # Query all transactions for this user
        response = table.query(
            KeyConditionExpression=Key('PK').eq(f"USER#{user_id}") & Key('SK').begins_with('TXN#')
        )
        
        transactions = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression=Key('PK').eq(f"USER#{user_id}") & Key('SK').begins_with('TXN#'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            transactions.extend(response.get('Items', []))
        
        # Collect unique (category, month) combinations
        category_months = set()
        for txn in transactions:
            category = txn.get('category')
            date_str = txn.get('date')
            
            if category and date_str:
                # Extract month from date
                if 'T' in date_str:
                    month = date_str[:7]
                else:
                    month = date_str[:7]
                
                category_months.add((category, month))
        
        logger.info(f"Found {len(category_months)} unique category-month combinations for user {user_id}")
        
        # Update statistics for each combination
        for category, month in category_months:
            update_category_stats(user_id, category, month, table)
        
        return {
            'categories_processed': len(set(cat for cat, _ in category_months)),
            'months_processed': len(set(mon for _, mon in category_months)),
            'total_combinations': len(category_months)
        }
        
    except Exception as e:
        logger.error(f"Failed to recalculate all statistics for user {user_id}: {str(e)}")
        return {
            'categories_processed': 0,
            'months_processed': 0,
            'total_combinations': 0,
            'error': str(e)
        }


def lambda_handler_scheduled(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for scheduled job (runs daily via EventBridge).
    Recalculates all category statistics for all users to ensure consistency.
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context
        
    Returns:
        Processing result
    """
    try:
        logger.info("Starting scheduled category statistics recalculation")
        
        table = get_dynamodb_table()
        
        # Scan for all user profiles (SK='PROFILE')
        logger.info("Scanning for all user profiles")
        response = table.scan(
            FilterExpression=Attr('SK').eq('PROFILE')
        )
        
        users = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('SK').eq('PROFILE'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            users.extend(response.get('Items', []))
        
        logger.info(f"Found {len(users)} users to process")
        
        total_stats = {
            'users_processed': 0,
            'total_categories': 0,
            'total_months': 0,
            'total_combinations': 0,
            'errors': []
        }
        
        # Process each user
        for user in users:
            pk = user.get('PK', '')
            user_id = pk.replace('USER#', '') if pk.startswith('USER#') else None
            
            if not user_id:
                continue
            
            logger.info(f"Processing statistics for user {user_id}")
            
            result = recalculate_all_statistics(user_id, table)
            
            total_stats['users_processed'] += 1
            total_stats['total_categories'] += result.get('categories_processed', 0)
            total_stats['total_months'] += result.get('months_processed', 0)
            total_stats['total_combinations'] += result.get('total_combinations', 0)
            
            if 'error' in result:
                total_stats['errors'].append({
                    'user_id': user_id,
                    'error': result['error']
                })
        
        logger.info(f"Scheduled recalculation completed: {json.dumps(total_stats)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Scheduled recalculation completed',
                'statistics': total_stats
            })
        }
        
    except Exception as e:
        logger.exception("Unhandled exception in scheduled handler")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


# Default handler (can route to either stream or scheduled based on event type)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler that routes to appropriate sub-handler.
    
    Args:
        event: Lambda event (DynamoDB Stream or EventBridge)
        context: Lambda context
        
    Returns:
        Processing result
    """
    try:
        # Check if this is a DynamoDB Stream event
        if 'Records' in event and event['Records']:
            first_record = event['Records'][0]
            if 'dynamodb' in first_record:
                logger.info("Routing to stream handler")
                return lambda_handler_stream(event, context)
        
        # Check if this is an EventBridge scheduled event
        if 'source' in event and event['source'] == 'aws.events':
            logger.info("Routing to scheduled handler")
            return lambda_handler_scheduled(event, context)
        
        # Default to scheduled handler for manual invocations
        logger.info("Routing to scheduled handler (default)")
        return lambda_handler_scheduled(event, context)
        
    except Exception as e:
        logger.exception("Unhandled exception in main handler")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
