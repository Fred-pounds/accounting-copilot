"""
DynamoDB entity models for the AI Accounting Copilot.

This module defines entity classes for all data types stored in DynamoDB,
along with serialization/deserialization functions and key generation utilities.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal


@dataclass
class UserProfile:
    """User profile entity."""
    user_id: str
    email: str
    business_name: str
    created_at: str
    custom_categories: List[str] = field(default_factory=list)
    notification_preferences: Dict[str, bool] = field(default_factory=lambda: {
        "email": True,
        "approval_reminders": True
    })
    
    def to_dynamodb(self) -> Dict[str, Any]:
        """Serialize to DynamoDB format."""
        return {
            "PK": f"USER#{self.user_id}",
            "SK": "PROFILE",
            "entity_type": "user_profile",
            "user_id": self.user_id,
            "email": self.email,
            "business_name": self.business_name,
            "created_at": self.created_at,
            "custom_categories": self.custom_categories,
            "notification_preferences": self.notification_preferences
        }
    
    @staticmethod
    def from_dynamodb(item: Dict[str, Any]) -> 'UserProfile':
        """Deserialize from DynamoDB format."""
        return UserProfile(
            user_id=item["user_id"],
            email=item["email"],
            business_name=item["business_name"],
            created_at=item["created_at"],
            custom_categories=item.get("custom_categories", []),
            notification_preferences=item.get("notification_preferences", {
                "email": True,
                "approval_reminders": True
            })
        )


@dataclass
class Document:
    """Financial document entity."""
    user_id: str
    document_id: str
    s3_key: str
    s3_bucket: str
    upload_timestamp: str
    document_type: str
    ocr_status: str
    extracted_text: Optional[str] = None
    parsed_fields: Optional[Dict[str, Any]] = None
    processing_duration_ms: Optional[int] = None
    
    def to_dynamodb(self) -> Dict[str, Any]:
        """Serialize to DynamoDB format."""
        item = {
            "PK": f"USER#{self.user_id}",
            "SK": f"DOC#{self.document_id}",
            "entity_type": "document",
            "user_id": self.user_id,
            "document_id": self.document_id,
            "s3_key": self.s3_key,
            "s3_bucket": self.s3_bucket,
            "upload_timestamp": self.upload_timestamp,
            "document_type": self.document_type,
            "ocr_status": self.ocr_status
        }
        
        if self.extracted_text is not None:
            item["extracted_text"] = self.extracted_text
        if self.parsed_fields is not None:
            item["parsed_fields"] = self.parsed_fields
        if self.processing_duration_ms is not None:
            item["processing_duration_ms"] = self.processing_duration_ms
            
        return item
    
    @staticmethod
    def from_dynamodb(item: Dict[str, Any]) -> 'Document':
        """Deserialize from DynamoDB format."""
        return Document(
            user_id=item["user_id"],
            document_id=item["document_id"],
            s3_key=item["s3_key"],
            s3_bucket=item["s3_bucket"],
            upload_timestamp=item["upload_timestamp"],
            document_type=item["document_type"],
            ocr_status=item["ocr_status"],
            extracted_text=item.get("extracted_text"),
            parsed_fields=item.get("parsed_fields"),
            processing_duration_ms=item.get("processing_duration_ms")
        )


@dataclass
class Transaction:
    """Transaction entity."""
    user_id: str
    transaction_id: str
    date: str
    amount: Decimal
    currency: str
    type: str  # "income" or "expense"
    category: str
    vendor: str
    description: str
    classification_confidence: float
    classification_reasoning: str
    status: str
    created_at: str
    updated_at: str
    created_by: str
    flagged_for_review: bool = False
    validation_issues: List[str] = field(default_factory=list)
    source: Optional[str] = None
    document_id: Optional[str] = None
    reconciliation_status: Optional[str] = None
    matched_bank_transaction_id: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    
    def to_dynamodb(self) -> Dict[str, Any]:
        """Serialize to DynamoDB format."""
        item = {
            "PK": f"USER#{self.user_id}",
            "SK": f"TXN#{self.transaction_id}",
            "GSI1PK": f"USER#{self.user_id}#CAT#{self.category}",
            "GSI1SK": f"DATE#{self.date}",
            "entity_type": "transaction",
            "user_id": self.user_id,
            "transaction_id": self.transaction_id,
            "date": self.date,
            "amount": str(self.amount),  # Store as string to preserve precision
            "currency": self.currency,
            "type": self.type,
            "category": self.category,
            "vendor": self.vendor,
            "description": self.description,
            "classification_confidence": str(self.classification_confidence),
            "classification_reasoning": self.classification_reasoning,
            "status": self.status,
            "flagged_for_review": self.flagged_for_review,
            "validation_issues": self.validation_issues,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by
        }
        
        # Add GSI2 keys if status is pending
        if self.status == "pending":
            item["GSI2PK"] = f"USER#{self.user_id}#STATUS#pending"
            item["GSI2SK"] = f"DATE#{self.date}"
        
        # Add optional fields
        if self.source:
            item["source"] = self.source
        if self.document_id:
            item["document_id"] = self.document_id
        if self.reconciliation_status:
            item["reconciliation_status"] = self.reconciliation_status
        if self.matched_bank_transaction_id:
            item["matched_bank_transaction_id"] = self.matched_bank_transaction_id
        if self.approved_by:
            item["approved_by"] = self.approved_by
        if self.approved_at:
            item["approved_at"] = self.approved_at
            
        return item
    
    @staticmethod
    def from_dynamodb(item: Dict[str, Any]) -> 'Transaction':
        """Deserialize from DynamoDB format."""
        return Transaction(
            user_id=item["user_id"],
            transaction_id=item["transaction_id"],
            date=item["date"],
            amount=Decimal(item["amount"]),
            currency=item["currency"],
            type=item["type"],
            category=item["category"],
            vendor=item["vendor"],
            description=item["description"],
            classification_confidence=float(item["classification_confidence"]),
            classification_reasoning=item["classification_reasoning"],
            status=item["status"],
            flagged_for_review=item.get("flagged_for_review", False),
            validation_issues=item.get("validation_issues", []),
            source=item.get("source"),
            document_id=item.get("document_id"),
            reconciliation_status=item.get("reconciliation_status"),
            matched_bank_transaction_id=item.get("matched_bank_transaction_id"),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            created_by=item["created_by"],
            approved_by=item.get("approved_by"),
            approved_at=item.get("approved_at")
        )


@dataclass
class BankTransaction:
    """Bank transaction entity."""
    user_id: str
    bank_transaction_id: str
    date: str
    amount: Decimal
    currency: str
    description: str
    reconciliation_status: str
    imported_at: str
    matched_transaction_id: Optional[str] = None
    match_confidence: Optional[float] = None
    
    def to_dynamodb(self) -> Dict[str, Any]:
        """Serialize to DynamoDB format."""
        item = {
            "PK": f"USER#{self.user_id}",
            "SK": f"BANK#{self.bank_transaction_id}",
            "entity_type": "bank_transaction",
            "user_id": self.user_id,
            "bank_transaction_id": self.bank_transaction_id,
            "date": self.date,
            "amount": str(self.amount),
            "currency": self.currency,
            "description": self.description,
            "reconciliation_status": self.reconciliation_status,
            "imported_at": self.imported_at
        }
        
        if self.matched_transaction_id:
            item["matched_transaction_id"] = self.matched_transaction_id
        if self.match_confidence is not None:
            item["match_confidence"] = str(self.match_confidence)
            
        return item
    
    @staticmethod
    def from_dynamodb(item: Dict[str, Any]) -> 'BankTransaction':
        """Deserialize from DynamoDB format."""
        return BankTransaction(
            user_id=item["user_id"],
            bank_transaction_id=item["bank_transaction_id"],
            date=item["date"],
            amount=Decimal(item["amount"]),
            currency=item["currency"],
            description=item["description"],
            reconciliation_status=item["reconciliation_status"],
            imported_at=item["imported_at"],
            matched_transaction_id=item.get("matched_transaction_id"),
            match_confidence=float(item["match_confidence"]) if item.get("match_confidence") else None
        )


@dataclass
class AuditEntry:
    """Audit trail entry entity."""
    user_id: str
    action_id: str
    timestamp: str
    action_type: str
    actor: str
    subject_type: str
    subject_id: str
    result: str
    actor_details: Optional[str] = None
    action_details: Optional[Dict[str, Any]] = None
    
    def to_dynamodb(self) -> Dict[str, Any]:
        """Serialize to DynamoDB format."""
        item = {
            "PK": f"USER#{self.user_id}",
            "SK": f"AUDIT#{self.timestamp}#{self.action_id}",
            "entity_type": "audit_entry",
            "user_id": self.user_id,
            "action_id": self.action_id,
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "actor": self.actor,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "result": self.result
        }
        
        if self.actor_details:
            item["actor_details"] = self.actor_details
        if self.action_details:
            item["action_details"] = self.action_details
            
        return item
    
    @staticmethod
    def from_dynamodb(item: Dict[str, Any]) -> 'AuditEntry':
        """Deserialize from DynamoDB format."""
        return AuditEntry(
            user_id=item["user_id"],
            action_id=item["action_id"],
            timestamp=item["timestamp"],
            action_type=item["action_type"],
            actor=item["actor"],
            subject_type=item["subject_type"],
            subject_id=item["subject_id"],
            result=item["result"],
            actor_details=item.get("actor_details"),
            action_details=item.get("action_details")
        )


@dataclass
class PendingApproval:
    """Pending approval entity."""
    user_id: str
    approval_id: str
    approval_type: str
    subject_type: str
    subject_id: str
    created_at: str
    status: str
    details: Dict[str, Any]
    reminder_sent_at: Optional[str] = None
    
    def to_dynamodb(self) -> Dict[str, Any]:
        """Serialize to DynamoDB format."""
        item = {
            "PK": f"USER#{self.user_id}",
            "SK": f"APPROVAL#{self.approval_id}",
            "entity_type": "pending_approval",
            "user_id": self.user_id,
            "approval_id": self.approval_id,
            "approval_type": self.approval_type,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "created_at": self.created_at,
            "status": self.status,
            "details": self.details
        }
        
        # Add GSI2 keys if status is pending
        if self.status == "pending":
            item["GSI2PK"] = f"USER#{self.user_id}#STATUS#pending"
            item["GSI2SK"] = f"DATE#{self.created_at}"
        
        if self.reminder_sent_at:
            item["reminder_sent_at"] = self.reminder_sent_at
            
        return item
    
    @staticmethod
    def from_dynamodb(item: Dict[str, Any]) -> 'PendingApproval':
        """Deserialize from DynamoDB format."""
        return PendingApproval(
            user_id=item["user_id"],
            approval_id=item["approval_id"],
            approval_type=item["approval_type"],
            subject_type=item["subject_type"],
            subject_id=item["subject_id"],
            created_at=item["created_at"],
            status=item["status"],
            details=item["details"],
            reminder_sent_at=item.get("reminder_sent_at")
        )


@dataclass
class ConversationMessage:
    """Conversation message entity."""
    user_id: str
    conversation_id: str
    message_id: str
    timestamp: str
    role: str  # "user" or "assistant"
    content: str
    response: Optional[Dict[str, Any]] = None
    
    def to_dynamodb(self) -> Dict[str, Any]:
        """Serialize to DynamoDB format."""
        item = {
            "PK": f"USER#{self.user_id}",
            "SK": f"CONV#{self.conversation_id}#MSG#{self.message_id}",
            "entity_type": "conversation_message",
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "role": self.role,
            "content": self.content
        }
        
        if self.response:
            item["response"] = self.response
            
        return item
    
    @staticmethod
    def from_dynamodb(item: Dict[str, Any]) -> 'ConversationMessage':
        """Deserialize from DynamoDB format."""
        return ConversationMessage(
            user_id=item["user_id"],
            conversation_id=item["conversation_id"],
            message_id=item["message_id"],
            timestamp=item["timestamp"],
            role=item["role"],
            content=item["content"],
            response=item.get("response")
        )


@dataclass
class CategoryStats:
    """Category statistics entity."""
    user_id: str
    category: str
    month: str
    transaction_count: int
    total_amount: Decimal
    average_amount: Decimal
    std_deviation: Decimal
    min_amount: Decimal
    max_amount: Decimal
    updated_at: str
    
    def to_dynamodb(self) -> Dict[str, Any]:
        """Serialize to DynamoDB format."""
        return {
            "PK": f"USER#{self.user_id}",
            "SK": f"STATS#{self.category}#{self.month}",
            "entity_type": "category_stats",
            "user_id": self.user_id,
            "category": self.category,
            "month": self.month,
            "transaction_count": self.transaction_count,
            "total_amount": str(self.total_amount),
            "average_amount": str(self.average_amount),
            "std_deviation": str(self.std_deviation),
            "min_amount": str(self.min_amount),
            "max_amount": str(self.max_amount),
            "updated_at": self.updated_at
        }
    
    @staticmethod
    def from_dynamodb(item: Dict[str, Any]) -> 'CategoryStats':
        """Deserialize from DynamoDB format."""
        return CategoryStats(
            user_id=item["user_id"],
            category=item["category"],
            month=item["month"],
            transaction_count=item["transaction_count"],
            total_amount=Decimal(item["total_amount"]),
            average_amount=Decimal(item["average_amount"]),
            std_deviation=Decimal(item["std_deviation"]),
            min_amount=Decimal(item["min_amount"]),
            max_amount=Decimal(item["max_amount"]),
            updated_at=item["updated_at"]
        )


# Key generation utility functions

def generate_user_pk(user_id: str) -> str:
    """Generate partition key for user entities."""
    return f"USER#{user_id}"


def generate_document_sk(document_id: str) -> str:
    """Generate sort key for document entities."""
    return f"DOC#{document_id}"


def generate_transaction_sk(transaction_id: str) -> str:
    """Generate sort key for transaction entities."""
    return f"TXN#{transaction_id}"


def generate_bank_transaction_sk(bank_transaction_id: str) -> str:
    """Generate sort key for bank transaction entities."""
    return f"BANK#{bank_transaction_id}"


def generate_audit_sk(timestamp: str, action_id: str) -> str:
    """Generate sort key for audit entries."""
    return f"AUDIT#{timestamp}#{action_id}"


def generate_approval_sk(approval_id: str) -> str:
    """Generate sort key for approval entities."""
    return f"APPROVAL#{approval_id}"


def generate_conversation_sk(conversation_id: str, message_id: str) -> str:
    """Generate sort key for conversation messages."""
    return f"CONV#{conversation_id}#MSG#{message_id}"


def generate_stats_sk(category: str, month: str) -> str:
    """Generate sort key for category statistics."""
    return f"STATS#{category}#{month}"


# GSI key generation functions

def generate_category_gsi_pk(user_id: str, category: str) -> str:
    """Generate GSI1 partition key for category queries."""
    return f"USER#{user_id}#CAT#{category}"


def generate_date_gsi_sk(date: str) -> str:
    """Generate GSI1 sort key for date queries."""
    return f"DATE#{date}"


def generate_status_gsi_pk(user_id: str, status: str) -> str:
    """Generate GSI2 partition key for status queries."""
    return f"USER#{user_id}#STATUS#{status}"
