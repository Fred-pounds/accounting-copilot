"""
DynamoDB repository layer for AI Accounting Copilot.
Provides CRUD operations and query functions for all entity types.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from .models import (
    UserProfile, Document, Transaction, BankTransaction, AuditEntry,
    PendingApproval, ConversationMessage, CategoryStats,
    generate_user_pk, generate_document_sk, generate_transaction_sk,
    generate_bank_transaction_sk, generate_audit_sk, generate_approval_sk,
    generate_conversation_sk, generate_stats_sk,
    generate_category_gsi1pk, generate_date_gsi1sk,
    generate_status_gsi2pk, generate_date_gsi2sk,
    generate_timestamp, generate_id
)
from .exceptions import NotFoundError, ValidationError
from .logger import get_logger

logger = get_logger(__name__)


class DynamoDBRepository:
    """Repository for DynamoDB operations."""
    
    def __init__(self, table_name: str, dynamodb_resource=None):
        """
        Initialize repository.
        
        Args:
            table_name: Name of the DynamoDB table
            dynamodb_resource: Optional boto3 DynamoDB resource (for testing)
        """
        self.table_name = table_name
        if dynamodb_resource:
            self.dynamodb = dynamodb_resource
        else:
            self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Convert float values to Decimal for DynamoDB."""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        return obj
    
    def _convert_decimal_to_float(self, obj: Any) -> Any:
        """Convert Decimal values to float for application use."""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimal_to_float(item) for item in obj]
        return obj
    
    # User Profile operations
    def create_user_profile(self, user_id: str, email: str, business_name: str) -> UserProfile:
        """Create a new user profile."""
        profile = UserProfile(
            PK=generate_user_pk(user_id),
            SK="PROFILE",
            email=email,
            business_name=business_name,
            created_at=generate_timestamp()
        )
        
        item = self._convert_floats_to_decimal(profile.to_dict())
        
        try:
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(PK)'
            )
            logger.info(f"Created user profile for user_id={user_id}")
            return profile
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValidationError(f"User profile already exists for user_id={user_id}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user_id."""
        try:
            response = self.table.get_item(
                Key={
                    'PK': generate_user_pk(user_id),
                    'SK': 'PROFILE'
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = self._convert_decimal_to_float(response['Item'])
            return UserProfile(**item)
        except ClientError as e:
            logger.error(f"Error getting user profile: {e}")
            raise
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        """Update user profile."""
        pk = generate_user_pk(user_id)
        
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for i, (key, value) in enumerate(updates.items()):
            attr_name = f"#attr{i}"
            attr_value = f":val{i}"
            update_expr += f"{attr_name} = {attr_value}, "
            expr_attr_names[attr_name] = key
            expr_attr_values[attr_value] = self._convert_floats_to_decimal(value)
        
        update_expr = update_expr.rstrip(", ")
        
        try:
            response = self.table.update_item(
                Key={'PK': pk, 'SK': 'PROFILE'},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            
            item = self._convert_decimal_to_float(response['Attributes'])
            logger.info(f"Updated user profile for user_id={user_id}")
            return UserProfile(**item)
        except ClientError as e:
            logger.error(f"Error updating user profile: {e}")
            raise

    
    # Document operations
    def create_document(self, user_id: str, document: Document) -> Document:
        """Create a new document."""
        item = self._convert_floats_to_decimal(document.to_dict())
        
        try:
            self.table.put_item(Item=item)
            logger.info(f"Created document {document.document_id} for user_id={user_id}")
            return document
        except ClientError as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    def get_document(self, user_id: str, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        try:
            response = self.table.get_item(
                Key={
                    'PK': generate_user_pk(user_id),
                    'SK': generate_document_sk(document_id)
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = self._convert_decimal_to_float(response['Item'])
            return Document(**item)
        except ClientError as e:
            logger.error(f"Error getting document: {e}")
            raise
    
    def list_documents(self, user_id: str, limit: int = 50) -> List[Document]:
        """List documents for a user."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(generate_user_pk(user_id)) & 
                                     Key('SK').begins_with('DOC#'),
                Limit=limit
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [Document(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error listing documents: {e}")
            raise
    
    def update_document(self, user_id: str, document_id: str, updates: Dict[str, Any]) -> Document:
        """Update document."""
        pk = generate_user_pk(user_id)
        sk = generate_document_sk(document_id)
        
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for i, (key, value) in enumerate(updates.items()):
            attr_name = f"#attr{i}"
            attr_value = f":val{i}"
            update_expr += f"{attr_name} = {attr_value}, "
            expr_attr_names[attr_name] = key
            expr_attr_values[attr_value] = self._convert_floats_to_decimal(value)
        
        update_expr = update_expr.rstrip(", ")
        
        try:
            response = self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            
            item = self._convert_decimal_to_float(response['Attributes'])
            logger.info(f"Updated document {document_id}")
            return Document(**item)
        except ClientError as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    # Transaction operations
    def create_transaction(self, user_id: str, transaction: Transaction) -> Transaction:
        """Create a new transaction."""
        item = self._convert_floats_to_decimal(transaction.to_dict())
        
        try:
            self.table.put_item(Item=item)
            logger.info(f"Created transaction {transaction.transaction_id} for user_id={user_id}")
            return transaction
        except ClientError as e:
            logger.error(f"Error creating transaction: {e}")
            raise
    
    def get_transaction(self, user_id: str, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        try:
            response = self.table.get_item(
                Key={
                    'PK': generate_user_pk(user_id),
                    'SK': generate_transaction_sk(transaction_id)
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = self._convert_decimal_to_float(response['Item'])
            return Transaction(**item)
        except ClientError as e:
            logger.error(f"Error getting transaction: {e}")
            raise
    
    def list_transactions(self, user_id: str, limit: int = 50) -> List[Transaction]:
        """List transactions for a user."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(generate_user_pk(user_id)) & 
                                     Key('SK').begins_with('TXN#'),
                Limit=limit
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [Transaction(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error listing transactions: {e}")
            raise
    
    def query_transactions_by_category(self, user_id: str, category: str, 
                                      start_date: Optional[str] = None,
                                      end_date: Optional[str] = None,
                                      limit: int = 50) -> List[Transaction]:
        """Query transactions by category using GSI1."""
        try:
            gsi1pk = generate_category_gsi1pk(user_id, category)
            
            # Build key condition
            if start_date and end_date:
                key_condition = Key('GSI1PK').eq(gsi1pk) & \
                              Key('GSI1SK').between(
                                  generate_date_gsi1sk(start_date),
                                  generate_date_gsi1sk(end_date)
                              )
            elif start_date:
                key_condition = Key('GSI1PK').eq(gsi1pk) & \
                              Key('GSI1SK').gte(generate_date_gsi1sk(start_date))
            elif end_date:
                key_condition = Key('GSI1PK').eq(gsi1pk) & \
                              Key('GSI1SK').lte(generate_date_gsi1sk(end_date))
            else:
                key_condition = Key('GSI1PK').eq(gsi1pk)
            
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=key_condition,
                Limit=limit
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [Transaction(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error querying transactions by category: {e}")
            raise
    
    def query_transactions_by_date_range(self, user_id: str, start_date: str, 
                                        end_date: str, limit: int = 100) -> List[Transaction]:
        """Query transactions by date range."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(generate_user_pk(user_id)) & 
                                     Key('SK').begins_with('TXN#'),
                FilterExpression=Attr('date').between(start_date, end_date),
                Limit=limit
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [Transaction(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error querying transactions by date range: {e}")
            raise
    
    def query_transactions_by_status(self, user_id: str, status: str,
                                    start_date: Optional[str] = None,
                                    end_date: Optional[str] = None,
                                    limit: int = 50) -> List[Transaction]:
        """Query transactions by status using GSI2."""
        try:
            gsi2pk = generate_status_gsi2pk(user_id, status)
            
            # Build key condition
            if start_date and end_date:
                key_condition = Key('GSI2PK').eq(gsi2pk) & \
                              Key('GSI2SK').between(
                                  generate_date_gsi2sk(start_date),
                                  generate_date_gsi2sk(end_date)
                              )
            elif start_date:
                key_condition = Key('GSI2PK').eq(gsi2pk) & \
                              Key('GSI2SK').gte(generate_date_gsi2sk(start_date))
            elif end_date:
                key_condition = Key('GSI2PK').eq(gsi2pk) & \
                              Key('GSI2SK').lte(generate_date_gsi2sk(end_date))
            else:
                key_condition = Key('GSI2PK').eq(gsi2pk)
            
            response = self.table.query(
                IndexName='GSI2',
                KeyConditionExpression=key_condition,
                Limit=limit
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [Transaction(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error querying transactions by status: {e}")
            raise
    
    def update_transaction(self, user_id: str, transaction_id: str, 
                          updates: Dict[str, Any]) -> Transaction:
        """Update transaction."""
        pk = generate_user_pk(user_id)
        sk = generate_transaction_sk(transaction_id)
        
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for i, (key, value) in enumerate(updates.items()):
            attr_name = f"#attr{i}"
            attr_value = f":val{i}"
            update_expr += f"{attr_name} = {attr_value}, "
            expr_attr_names[attr_name] = key
            expr_attr_values[attr_value] = self._convert_floats_to_decimal(value)
        
        update_expr = update_expr.rstrip(", ")
        
        try:
            response = self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            
            item = self._convert_decimal_to_float(response['Attributes'])
            logger.info(f"Updated transaction {transaction_id}")
            return Transaction(**item)
        except ClientError as e:
            logger.error(f"Error updating transaction: {e}")
            raise
    
    def delete_transaction(self, user_id: str, transaction_id: str) -> None:
        """Delete transaction."""
        try:
            self.table.delete_item(
                Key={
                    'PK': generate_user_pk(user_id),
                    'SK': generate_transaction_sk(transaction_id)
                }
            )
            logger.info(f"Deleted transaction {transaction_id}")
        except ClientError as e:
            logger.error(f"Error deleting transaction: {e}")
            raise

    
    # Bank Transaction operations
    def create_bank_transaction(self, user_id: str, bank_transaction: BankTransaction) -> BankTransaction:
        """Create a new bank transaction."""
        item = self._convert_floats_to_decimal(bank_transaction.to_dict())
        
        try:
            self.table.put_item(Item=item)
            logger.info(f"Created bank transaction {bank_transaction.bank_transaction_id}")
            return bank_transaction
        except ClientError as e:
            logger.error(f"Error creating bank transaction: {e}")
            raise
    
    def get_bank_transaction(self, user_id: str, bank_transaction_id: str) -> Optional[BankTransaction]:
        """Get bank transaction by ID."""
        try:
            response = self.table.get_item(
                Key={
                    'PK': generate_user_pk(user_id),
                    'SK': generate_bank_transaction_sk(bank_transaction_id)
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = self._convert_decimal_to_float(response['Item'])
            return BankTransaction(**item)
        except ClientError as e:
            logger.error(f"Error getting bank transaction: {e}")
            raise
    
    def list_bank_transactions(self, user_id: str, limit: int = 50) -> List[BankTransaction]:
        """List bank transactions for a user."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(generate_user_pk(user_id)) & 
                                     Key('SK').begins_with('BANK#'),
                Limit=limit
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [BankTransaction(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error listing bank transactions: {e}")
            raise
    
    def update_bank_transaction(self, user_id: str, bank_transaction_id: str,
                               updates: Dict[str, Any]) -> BankTransaction:
        """Update bank transaction."""
        pk = generate_user_pk(user_id)
        sk = generate_bank_transaction_sk(bank_transaction_id)
        
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for i, (key, value) in enumerate(updates.items()):
            attr_name = f"#attr{i}"
            attr_value = f":val{i}"
            update_expr += f"{attr_name} = {attr_value}, "
            expr_attr_names[attr_name] = key
            expr_attr_values[attr_value] = self._convert_floats_to_decimal(value)
        
        update_expr = update_expr.rstrip(", ")
        
        try:
            response = self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            
            item = self._convert_decimal_to_float(response['Attributes'])
            logger.info(f"Updated bank transaction {bank_transaction_id}")
            return BankTransaction(**item)
        except ClientError as e:
            logger.error(f"Error updating bank transaction: {e}")
            raise
    
    # Audit Entry operations
    def create_audit_entry(self, user_id: str, audit_entry: AuditEntry) -> AuditEntry:
        """Create a new audit entry."""
        item = self._convert_floats_to_decimal(audit_entry.to_dict())
        
        try:
            self.table.put_item(Item=item)
            logger.info(f"Created audit entry {audit_entry.action_id}")
            return audit_entry
        except ClientError as e:
            logger.error(f"Error creating audit entry: {e}")
            raise
    
    def list_audit_entries(self, user_id: str, limit: int = 100) -> List[AuditEntry]:
        """List audit entries for a user."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(generate_user_pk(user_id)) & 
                                     Key('SK').begins_with('AUDIT#'),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [AuditEntry(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error listing audit entries: {e}")
            raise
    
    def query_audit_entries_by_date_range(self, user_id: str, start_date: str,
                                         end_date: str, limit: int = 100) -> List[AuditEntry]:
        """Query audit entries by date range."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(generate_user_pk(user_id)) & 
                                     Key('SK').begins_with('AUDIT#'),
                FilterExpression=Attr('timestamp').between(start_date, end_date),
                Limit=limit,
                ScanIndexForward=False
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [AuditEntry(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error querying audit entries: {e}")
            raise
    
    def query_audit_entries_by_action_type(self, user_id: str, action_type: str,
                                          limit: int = 100) -> List[AuditEntry]:
        """Query audit entries by action type."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(generate_user_pk(user_id)) & 
                                     Key('SK').begins_with('AUDIT#'),
                FilterExpression=Attr('action_type').eq(action_type),
                Limit=limit,
                ScanIndexForward=False
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [AuditEntry(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error querying audit entries by action type: {e}")
            raise
    
    # Pending Approval operations
    def create_pending_approval(self, user_id: str, approval: PendingApproval) -> PendingApproval:
        """Create a new pending approval."""
        item = self._convert_floats_to_decimal(approval.to_dict())
        
        try:
            self.table.put_item(Item=item)
            logger.info(f"Created pending approval {approval.approval_id}")
            return approval
        except ClientError as e:
            logger.error(f"Error creating pending approval: {e}")
            raise
    
    def get_pending_approval(self, user_id: str, approval_id: str) -> Optional[PendingApproval]:
        """Get pending approval by ID."""
        try:
            response = self.table.get_item(
                Key={
                    'PK': generate_user_pk(user_id),
                    'SK': generate_approval_sk(approval_id)
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = self._convert_decimal_to_float(response['Item'])
            return PendingApproval(**item)
        except ClientError as e:
            logger.error(f"Error getting pending approval: {e}")
            raise
    
    def list_pending_approvals(self, user_id: str, status: str = "pending",
                              limit: int = 50) -> List[PendingApproval]:
        """List pending approvals using GSI2."""
        try:
            gsi2pk = generate_status_gsi2pk(user_id, status)
            
            response = self.table.query(
                IndexName='GSI2',
                KeyConditionExpression=Key('GSI2PK').eq(gsi2pk),
                Limit=limit
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [PendingApproval(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error listing pending approvals: {e}")
            raise
    
    def update_pending_approval(self, user_id: str, approval_id: str,
                               updates: Dict[str, Any]) -> PendingApproval:
        """Update pending approval."""
        pk = generate_user_pk(user_id)
        sk = generate_approval_sk(approval_id)
        
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for i, (key, value) in enumerate(updates.items()):
            attr_name = f"#attr{i}"
            attr_value = f":val{i}"
            update_expr += f"{attr_name} = {attr_value}, "
            expr_attr_names[attr_name] = key
            expr_attr_values[attr_value] = self._convert_floats_to_decimal(value)
        
        update_expr = update_expr.rstrip(", ")
        
        try:
            response = self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            
            item = self._convert_decimal_to_float(response['Attributes'])
            logger.info(f"Updated pending approval {approval_id}")
            return PendingApproval(**item)
        except ClientError as e:
            logger.error(f"Error updating pending approval: {e}")
            raise
    
    # Conversation Message operations
    def create_conversation_message(self, user_id: str, message: ConversationMessage) -> ConversationMessage:
        """Create a new conversation message."""
        item = self._convert_floats_to_decimal(message.to_dict())
        
        try:
            self.table.put_item(Item=item)
            logger.info(f"Created conversation message {message.message_id}")
            return message
        except ClientError as e:
            logger.error(f"Error creating conversation message: {e}")
            raise
    
    def list_conversation_messages(self, user_id: str, conversation_id: str,
                                  limit: int = 50) -> List[ConversationMessage]:
        """List conversation messages."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(generate_user_pk(user_id)) & 
                                     Key('SK').begins_with(f'CONV#{conversation_id}#MSG#'),
                Limit=limit
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [ConversationMessage(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error listing conversation messages: {e}")
            raise
    
    # Category Stats operations
    def create_or_update_category_stats(self, user_id: str, stats: CategoryStats) -> CategoryStats:
        """Create or update category statistics."""
        item = self._convert_floats_to_decimal(stats.to_dict())
        
        try:
            self.table.put_item(Item=item)
            logger.info(f"Updated category stats for {stats.category} in {stats.month}")
            return stats
        except ClientError as e:
            logger.error(f"Error updating category stats: {e}")
            raise
    
    def get_category_stats(self, user_id: str, category: str, month: str) -> Optional[CategoryStats]:
        """Get category statistics."""
        try:
            response = self.table.get_item(
                Key={
                    'PK': generate_user_pk(user_id),
                    'SK': generate_stats_sk(category, month)
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = self._convert_decimal_to_float(response['Item'])
            return CategoryStats(**item)
        except ClientError as e:
            logger.error(f"Error getting category stats: {e}")
            raise
    
    def list_category_stats(self, user_id: str, month: str, limit: int = 50) -> List[CategoryStats]:
        """List all category statistics for a month."""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(generate_user_pk(user_id)) & 
                                     Key('SK').begins_with(f'STATS#'),
                FilterExpression=Attr('month').eq(month),
                Limit=limit
            )
            
            items = [self._convert_decimal_to_float(item) for item in response.get('Items', [])]
            return [CategoryStats(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error listing category stats: {e}")
            raise
    
    # Batch operations
    def batch_write_items(self, items: List[Dict[str, Any]]) -> None:
        """Batch write items to DynamoDB."""
        try:
            with self.table.batch_writer() as batch:
                for item in items:
                    converted_item = self._convert_floats_to_decimal(item)
                    batch.put_item(Item=converted_item)
            
            logger.info(f"Batch wrote {len(items)} items")
        except ClientError as e:
            logger.error(f"Error in batch write: {e}")
            raise
    
    def batch_delete_items(self, keys: List[Dict[str, str]]) -> None:
        """Batch delete items from DynamoDB."""
        try:
            with self.table.batch_writer() as batch:
                for key in keys:
                    batch.delete_item(Key=key)
            
            logger.info(f"Batch deleted {len(keys)} items")
        except ClientError as e:
            logger.error(f"Error in batch delete: {e}")
            raise
