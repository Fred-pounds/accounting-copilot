"""
DynamoDB repository layer for the AI Accounting Copilot.

This module provides CRUD operations and query functions for all entity types,
with error handling for throttling and conditional check failures.
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time

from .entities import (
    UserProfile, Document, Transaction, BankTransaction,
    AuditEntry, PendingApproval, ConversationMessage, CategoryStats
)
from .exceptions import (
    RepositoryError, ThrottlingError, ConditionalCheckError, NotFoundError
)


class DynamoDBRepository:
    """Repository for DynamoDB operations."""
    
    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        """
        Initialize the repository.
        
        Args:
            table_name: Name of the DynamoDB table
            region_name: AWS region name
        """
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name
    
    # User Profile operations
    
    def create_user_profile(self, profile: UserProfile) -> None:
        """
        Create a new user profile.
        
        Args:
            profile: UserProfile entity to create
            
        Raises:
            ConditionalCheckError: If user already exists
            ThrottlingError: If request is throttled
            RepositoryError: For other errors
        """
        try:
            self.table.put_item(
                Item=profile.to_dynamodb(),
                ConditionExpression="attribute_not_exists(PK)"
            )
        except ClientError as e:
            self._handle_error(e)
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get a user profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile if found, None otherwise
            
        Raises:
            ThrottlingError: If request is throttled
            RepositoryError: For other errors
        """
        try:
            response = self.table.get_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": "PROFILE"
                }
            )
            
            if "Item" in response:
                return UserProfile.from_dynamodb(response["Item"])
            return None
            
        except ClientError as e:
            self._handle_error(e)
    
    def update_user_profile(self, profile: UserProfile) -> None:
        """
        Update an existing user profile.
        
        Args:
            profile: UserProfile entity to update
            
        Raises:
            NotFoundError: If user doesn't exist
            ThrottlingError: If request is throttled
            RepositoryError: For other errors
        """
        try:
            self.table.put_item(
                Item=profile.to_dynamodb(),
                ConditionExpression="attribute_exists(PK)"
            )
        except ClientError as e:
            self._handle_error(e)
    
    # Document operations
    
    def create_document(self, document: Document) -> None:
        """Create a new document."""
        try:
            self.table.put_item(Item=document.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def get_document(self, user_id: str, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        try:
            response = self.table.get_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"DOC#{document_id}"
                }
            )
            
            if "Item" in response:
                return Document.from_dynamodb(response["Item"])
            return None
            
        except ClientError as e:
            self._handle_error(e)
    
    def update_document(self, document: Document) -> None:
        """Update an existing document."""
        try:
            self.table.put_item(Item=document.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def list_documents(
        self, 
        user_id: str, 
        limit: int = 50,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Document], Optional[Dict[str, Any]]]:
        """
        List documents for a user with pagination.
        
        Args:
            user_id: User ID
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token from previous query
            
        Returns:
            Tuple of (list of documents, next pagination token)
        """
        try:
            query_params = {
                "KeyConditionExpression": Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("DOC#"),
                "Limit": limit
            }
            
            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key
            
            response = self.table.query(**query_params)
            
            documents = [Document.from_dynamodb(item) for item in response.get("Items", [])]
            next_key = response.get("LastEvaluatedKey")
            
            return documents, next_key
            
        except ClientError as e:
            self._handle_error(e)
    
    # Transaction operations
    
    def create_transaction(self, transaction: Transaction) -> None:
        """Create a new transaction."""
        try:
            self.table.put_item(Item=transaction.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def get_transaction(self, user_id: str, transaction_id: str) -> Optional[Transaction]:
        """Get a transaction by ID."""
        try:
            response = self.table.get_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"TXN#{transaction_id}"
                }
            )
            
            if "Item" in response:
                return Transaction.from_dynamodb(response["Item"])
            return None
            
        except ClientError as e:
            self._handle_error(e)
    
    def update_transaction(self, transaction: Transaction) -> None:
        """Update an existing transaction."""
        try:
            self.table.put_item(Item=transaction.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def delete_transaction(self, user_id: str, transaction_id: str) -> None:
        """Delete a transaction."""
        try:
            self.table.delete_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"TXN#{transaction_id}"
                }
            )
        except ClientError as e:
            self._handle_error(e)
    
    def list_transactions(
        self,
        user_id: str,
        limit: int = 50,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Transaction], Optional[Dict[str, Any]]]:
        """List transactions for a user with pagination."""
        try:
            query_params = {
                "KeyConditionExpression": Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("TXN#"),
                "Limit": limit
            }
            
            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key
            
            response = self.table.query(**query_params)
            
            transactions = [Transaction.from_dynamodb(item) for item in response.get("Items", [])]
            next_key = response.get("LastEvaluatedKey")
            
            return transactions, next_key
            
        except ClientError as e:
            self._handle_error(e)
    
    def query_transactions_by_category(
        self,
        user_id: str,
        category: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Transaction]:
        """
        Query transactions by category and optional date range using GSI1.
        
        Args:
            user_id: User ID
            category: Transaction category
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum number of items to return
            
        Returns:
            List of transactions
        """
        try:
            gsi1_pk = f"USER#{user_id}#CAT#{category}"
            
            if start_date and end_date:
                key_condition = Key("GSI1PK").eq(gsi1_pk) & Key("GSI1SK").between(
                    f"DATE#{start_date}",
                    f"DATE#{end_date}"
                )
            elif start_date:
                key_condition = Key("GSI1PK").eq(gsi1_pk) & Key("GSI1SK").gte(f"DATE#{start_date}")
            elif end_date:
                key_condition = Key("GSI1PK").eq(gsi1_pk) & Key("GSI1SK").lte(f"DATE#{end_date}")
            else:
                key_condition = Key("GSI1PK").eq(gsi1_pk)
            
            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression=key_condition,
                Limit=limit
            )
            
            return [Transaction.from_dynamodb(item) for item in response.get("Items", [])]
            
        except ClientError as e:
            self._handle_error(e)
    
    def query_transactions_by_date_range(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        limit: int = 100
    ) -> List[Transaction]:
        """
        Query transactions by date range.
        
        Args:
            user_id: User ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of items to return
            
        Returns:
            List of transactions
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("TXN#"),
                FilterExpression=Attr("date").between(start_date, end_date),
                Limit=limit
            )
            
            return [Transaction.from_dynamodb(item) for item in response.get("Items", [])]
            
        except ClientError as e:
            self._handle_error(e)
    
    def query_pending_transactions(self, user_id: str, limit: int = 50) -> List[Transaction]:
        """Query transactions with pending status using GSI2."""
        try:
            response = self.table.query(
                IndexName="GSI2",
                KeyConditionExpression=Key("GSI2PK").eq(f"USER#{user_id}#STATUS#pending"),
                Limit=limit
            )
            
            return [Transaction.from_dynamodb(item) for item in response.get("Items", [])]
            
        except ClientError as e:
            self._handle_error(e)
    
    # Bank Transaction operations
    
    def create_bank_transaction(self, bank_transaction: BankTransaction) -> None:
        """Create a new bank transaction."""
        try:
            self.table.put_item(Item=bank_transaction.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def get_bank_transaction(self, user_id: str, bank_transaction_id: str) -> Optional[BankTransaction]:
        """Get a bank transaction by ID."""
        try:
            response = self.table.get_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"BANK#{bank_transaction_id}"
                }
            )
            
            if "Item" in response:
                return BankTransaction.from_dynamodb(response["Item"])
            return None
            
        except ClientError as e:
            self._handle_error(e)
    
    def update_bank_transaction(self, bank_transaction: BankTransaction) -> None:
        """Update an existing bank transaction."""
        try:
            self.table.put_item(Item=bank_transaction.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def list_bank_transactions(
        self,
        user_id: str,
        limit: int = 50,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> tuple[List[BankTransaction], Optional[Dict[str, Any]]]:
        """List bank transactions for a user with pagination."""
        try:
            query_params = {
                "KeyConditionExpression": Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("BANK#"),
                "Limit": limit
            }
            
            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key
            
            response = self.table.query(**query_params)
            
            bank_transactions = [BankTransaction.from_dynamodb(item) for item in response.get("Items", [])]
            next_key = response.get("LastEvaluatedKey")
            
            return bank_transactions, next_key
            
        except ClientError as e:
            self._handle_error(e)
    
    # Audit Entry operations
    
    def create_audit_entry(self, audit_entry: AuditEntry) -> None:
        """Create a new audit entry."""
        try:
            self.table.put_item(Item=audit_entry.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def batch_create_audit_entries(self, audit_entries: List[AuditEntry]) -> None:
        """
        Batch create audit entries for performance.
        
        Args:
            audit_entries: List of audit entries to create
            
        Note:
            DynamoDB batch write supports up to 25 items per request.
            This method automatically chunks larger batches.
        """
        try:
            # Process in chunks of 25 (DynamoDB limit)
            for i in range(0, len(audit_entries), 25):
                chunk = audit_entries[i:i + 25]
                
                with self.table.batch_writer() as batch:
                    for entry in chunk:
                        batch.put_item(Item=entry.to_dynamodb())
                        
        except ClientError as e:
            self._handle_error(e)
    
    def query_audit_entries(
        self,
        user_id: str,
        start_timestamp: Optional[str] = None,
        end_timestamp: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> List[AuditEntry]:
        """
        Query audit entries with optional filters.
        
        Args:
            user_id: User ID
            start_timestamp: Optional start timestamp
            end_timestamp: Optional end timestamp
            action_type: Optional action type filter
            limit: Maximum number of items to return (None for unlimited)
            
        Returns:
            List of audit entries
        """
        try:
            if start_timestamp and end_timestamp:
                key_condition = Key("PK").eq(f"USER#{user_id}") & Key("SK").between(
                    f"AUDIT#{start_timestamp}#",
                    f"AUDIT#{end_timestamp}#~"  # ~ is high in ASCII sort order
                )
            elif start_timestamp:
                key_condition = Key("PK").eq(f"USER#{user_id}") & Key("SK").gte(f"AUDIT#{start_timestamp}#")
            else:
                key_condition = Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("AUDIT#")
            
            query_params = {
                "KeyConditionExpression": key_condition,
                "ScanIndexForward": False  # Most recent first
            }
            
            # Only add Limit if specified
            if limit is not None:
                query_params["Limit"] = limit
            
            if action_type:
                query_params["FilterExpression"] = Attr("action_type").eq(action_type)
            
            # Handle pagination for unlimited queries
            all_items = []
            last_evaluated_key = None
            
            while True:
                if last_evaluated_key:
                    query_params["ExclusiveStartKey"] = last_evaluated_key
                
                response = self.table.query(**query_params)
                all_items.extend(response.get("Items", []))
                
                last_evaluated_key = response.get("LastEvaluatedKey")
                
                # If limit is specified or no more results, break
                if limit is not None or not last_evaluated_key:
                    break
            
            return [AuditEntry.from_dynamodb(item) for item in all_items]
            
        except ClientError as e:
            self._handle_error(e)
    
    # Pending Approval operations
    
    def create_pending_approval(self, approval: PendingApproval) -> None:
        """Create a new pending approval."""
        try:
            self.table.put_item(Item=approval.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def get_pending_approval(self, user_id: str, approval_id: str) -> Optional[PendingApproval]:
        """Get a pending approval by ID."""
        try:
            response = self.table.get_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"APPROVAL#{approval_id}"
                }
            )
            
            if "Item" in response:
                return PendingApproval.from_dynamodb(response["Item"])
            return None
            
        except ClientError as e:
            self._handle_error(e)
    
    def update_pending_approval(self, approval: PendingApproval) -> None:
        """Update an existing pending approval."""
        try:
            self.table.put_item(Item=approval.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def query_pending_approvals(self, user_id: str, limit: int = 50) -> List[PendingApproval]:
        """Query pending approvals using GSI2."""
        try:
            response = self.table.query(
                IndexName="GSI2",
                KeyConditionExpression=Key("GSI2PK").eq(f"USER#{user_id}#STATUS#pending"),
                Limit=limit
            )
            
            return [PendingApproval.from_dynamodb(item) for item in response.get("Items", [])]
            
        except ClientError as e:
            self._handle_error(e)
    
    # Conversation Message operations
    
    def create_conversation_message(self, message: ConversationMessage) -> None:
        """Create a new conversation message."""
        try:
            self.table.put_item(Item=message.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def query_conversation_history(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 10
    ) -> List[ConversationMessage]:
        """
        Query conversation history.
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            limit: Maximum number of messages to return
            
        Returns:
            List of conversation messages (most recent first)
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with(f"CONV#{conversation_id}#MSG#"),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            return [ConversationMessage.from_dynamodb(item) for item in response.get("Items", [])]
            
        except ClientError as e:
            self._handle_error(e)
    
    # Category Statistics operations
    
    def create_category_stats(self, stats: CategoryStats) -> None:
        """Create or update category statistics."""
        try:
            self.table.put_item(Item=stats.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    def get_category_stats(self, user_id: str, category: str, month: str) -> Optional[CategoryStats]:
        """Get category statistics for a specific month."""
        try:
            response = self.table.get_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"STATS#{category}#{month}"
                }
            )
            
            if "Item" in response:
                return CategoryStats.from_dynamodb(response["Item"])
            return None
            
        except ClientError as e:
            self._handle_error(e)
    
    def update_category_stats(self, stats: CategoryStats) -> None:
        """Update category statistics."""
        try:
            self.table.put_item(Item=stats.to_dynamodb())
        except ClientError as e:
            self._handle_error(e)
    
    # Batch operations
    
    def batch_write_items(self, items: List[Dict[str, Any]]) -> None:
        """
        Batch write items to DynamoDB.
        
        Args:
            items: List of items in DynamoDB format
            
        Note:
            Automatically chunks into batches of 25 items.
        """
        try:
            for i in range(0, len(items), 25):
                chunk = items[i:i + 25]
                
                with self.table.batch_writer() as batch:
                    for item in chunk:
                        batch.put_item(Item=item)
                        
        except ClientError as e:
            self._handle_error(e)
    
    # Error handling
    
    def _handle_error(self, error: ClientError) -> None:
        """
        Handle DynamoDB client errors.
        
        Args:
            error: ClientError from boto3
            
        Raises:
            ThrottlingError: For throttling errors
            ConditionalCheckError: For conditional check failures
            NotFoundError: For resource not found errors
            RepositoryError: For other errors
        """
        error_code = error.response['Error']['Code']
        error_message = error.response['Error']['Message']
        
        if error_code in ['ProvisionedThroughputExceededException', 'ThrottlingException']:
            raise ThrottlingError(f"Request throttled: {error_message}")
        elif error_code == 'ConditionalCheckFailedException':
            raise ConditionalCheckError(f"Conditional check failed: {error_message}")
        elif error_code == 'ResourceNotFoundException':
            raise NotFoundError(f"Resource not found: {error_message}")
        else:
            raise RepositoryError(f"DynamoDB error ({error_code}): {error_message}")
