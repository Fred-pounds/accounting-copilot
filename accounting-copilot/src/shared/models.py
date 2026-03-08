"""
Data models for AI Accounting Copilot.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class EntityType(str, Enum):
    """DynamoDB entity types."""
    USER_PROFILE = "user_profile"
    DOCUMENT = "document"
    TRANSACTION = "transaction"
    BANK_TRANSACTION = "bank_transaction"
    AUDIT_ENTRY = "audit_entry"
    PENDING_APPROVAL = "pending_approval"
    CONVERSATION_MESSAGE = "conversation_message"
    CATEGORY_STATS = "category_stats"


class TransactionType(str, Enum):
    """Transaction types."""
    INCOME = "income"
    EXPENSE = "expense"


class TransactionStatus(str, Enum):
    """Transaction status."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class DocumentType(str, Enum):
    """Document types."""
    RECEIPT = "receipt"
    INVOICE = "invoice"
    BANK_STATEMENT = "bank_statement"


class OCRStatus(str, Enum):
    """OCR processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReconciliationStatus(str, Enum):
    """Reconciliation status."""
    UNMATCHED = "unmatched"
    MATCHED = "matched"
    PENDING_REVIEW = "pending_review"


@dataclass
class LineItem:
    """Line item in a document."""
    description: str
    amount: float


@dataclass
class ParsedFields:
    """Parsed fields from a document."""
    date: str
    amount: float
    currency: str
    vendor: str
    line_items: List[LineItem]


@dataclass
class Document:
    """Financial document."""
    PK: str  # USER#<user_id>
    SK: str  # DOC#<document_id>
    entity_type: str = EntityType.DOCUMENT.value
    document_id: str = ""
    s3_key: str = ""
    s3_bucket: str = ""
    upload_timestamp: str = ""
    document_type: str = ""
    ocr_status: str = OCRStatus.PENDING.value
    extracted_text: str = ""
    parsed_fields: Optional[Dict[str, Any]] = None
    processing_duration_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Transaction:
    """Financial transaction."""
    PK: str  # USER#<user_id>
    SK: str  # TXN#<transaction_id>
    GSI1PK: str = ""  # USER#<user_id>#CAT#<category>
    GSI1SK: str = ""  # DATE#<date>
    GSI2PK: str = ""  # USER#<user_id>#STATUS#<status>
    GSI2SK: str = ""  # DATE#<date>
    entity_type: str = EntityType.TRANSACTION.value
    transaction_id: str = ""
    date: str = ""
    amount: float = 0.0
    currency: str = "USD"
    type: str = TransactionType.EXPENSE.value
    category: str = ""
    vendor: str = ""
    description: str = ""
    classification_confidence: float = 0.0
    classification_reasoning: str = ""
    status: str = TransactionStatus.PENDING_REVIEW.value
    flagged_for_review: bool = False
    validation_issues: List[str] = None
    source: str = ""
    document_id: str = ""
    reconciliation_status: str = ReconciliationStatus.UNMATCHED.value
    matched_bank_transaction_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    created_by: str = "ai"
    approved_by: str = ""
    approved_at: str = ""
    
    def __post_init__(self):
        if self.validation_issues is None:
            self.validation_issues = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB."""
        return {k: v for k, v in asdict(self).items() if v is not None and v != ""}


@dataclass
class AuditEntry:
    """Audit trail entry."""
    PK: str  # USER#<user_id>
    SK: str  # AUDIT#<timestamp>#<action_id>
    entity_type: str = EntityType.AUDIT_ENTRY.value
    action_id: str = ""
    timestamp: str = ""
    action_type: str = ""
    actor: str = ""  # "ai" or "user"
    actor_details: str = ""
    subject_type: str = ""
    subject_id: str = ""
    action_details: Dict[str, Any] = None
    result: str = ""
    
    def __post_init__(self):
        if self.action_details is None:
            self.action_details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB."""
        return {k: v for k, v in asdict(self).items() if v is not None and v != ""}


@dataclass
class BankTransaction:
    """Bank transaction."""
    PK: str  # USER#<user_id>
    SK: str  # BANK#<bank_transaction_id>
    entity_type: str = EntityType.BANK_TRANSACTION.value
    bank_transaction_id: str = ""
    date: str = ""
    amount: float = 0.0
    currency: str = "USD"
    description: str = ""
    reconciliation_status: str = ReconciliationStatus.UNMATCHED.value
    matched_transaction_id: str = ""
    match_confidence: float = 0.0
    imported_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB."""
        return {k: v for k, v in asdict(self).items() if v is not None and v != ""}


@dataclass
class PendingApproval:
    """Pending approval."""
    PK: str  # USER#<user_id>
    SK: str  # APPROVAL#<approval_id>
    GSI2PK: str = ""  # USER#<user_id>#STATUS#pending
    GSI2SK: str = ""  # DATE#<created_at>
    entity_type: str = EntityType.PENDING_APPROVAL.value
    approval_id: str = ""
    approval_type: str = ""
    subject_type: str = ""
    subject_id: str = ""
    created_at: str = ""
    reminder_sent_at: Optional[str] = None
    status: str = "pending"
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB."""
        return {k: v for k, v in asdict(self).items() if v is not None and v != ""}


@dataclass
class ConversationMessage:
    """Conversation message."""
    PK: str  # USER#<user_id>
    SK: str  # CONV#<conversation_id>#MSG#<message_id>
    entity_type: str = EntityType.CONVERSATION_MESSAGE.value
    conversation_id: str = ""
    message_id: str = ""
    timestamp: str = ""
    role: str = ""  # "user" or "assistant"
    content: str = ""
    response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB."""
        return {k: v for k, v in asdict(self).items() if v is not None and v != ""}


@dataclass
class CategoryStats:
    """Category statistics."""
    PK: str  # USER#<user_id>
    SK: str  # STATS#<category>#<month>
    entity_type: str = EntityType.CATEGORY_STATS.value
    category: str = ""
    month: str = ""
    transaction_count: int = 0
    total_amount: float = 0.0
    average_amount: float = 0.0
    std_deviation: float = 0.0
    min_amount: float = 0.0
    max_amount: float = 0.0
    updated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB."""
        return {k: v for k, v in asdict(self).items() if v is not None and v != ""}


@dataclass
class UserProfile:
    """User profile."""
    PK: str  # USER#<user_id>
    SK: str = "PROFILE"
    entity_type: str = EntityType.USER_PROFILE.value
    email: str = ""
    business_name: str = ""
    created_at: str = ""
    custom_categories: List[str] = None
    notification_preferences: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.custom_categories is None:
            self.custom_categories = []
        if self.notification_preferences is None:
            self.notification_preferences = {"email": True, "approval_reminders": True}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB."""
        return {k: v for k, v in asdict(self).items() if v is not None and v != ""}


# Key generation functions
def generate_user_pk(user_id: str) -> str:
    """Generate partition key for user."""
    return f"USER#{user_id}"


def generate_document_sk(document_id: str) -> str:
    """Generate sort key for document."""
    return f"DOC#{document_id}"


def generate_transaction_sk(transaction_id: str) -> str:
    """Generate sort key for transaction."""
    return f"TXN#{transaction_id}"


def generate_bank_transaction_sk(bank_transaction_id: str) -> str:
    """Generate sort key for bank transaction."""
    return f"BANK#{bank_transaction_id}"


def generate_audit_sk(timestamp: str, action_id: str) -> str:
    """Generate sort key for audit entry."""
    return f"AUDIT#{timestamp}#{action_id}"


def generate_approval_sk(approval_id: str) -> str:
    """Generate sort key for pending approval."""
    return f"APPROVAL#{approval_id}"


def generate_conversation_sk(conversation_id: str, message_id: str) -> str:
    """Generate sort key for conversation message."""
    return f"CONV#{conversation_id}#MSG#{message_id}"


def generate_stats_sk(category: str, month: str) -> str:
    """Generate sort key for category stats."""
    return f"STATS#{category}#{month}"


# GSI key generation functions
def generate_category_gsi1pk(user_id: str, category: str) -> str:
    """Generate GSI1 partition key for category queries."""
    return f"USER#{user_id}#CAT#{category}"


def generate_date_gsi1sk(date: str) -> str:
    """Generate GSI1 sort key for date queries."""
    return f"DATE#{date}"


def generate_status_gsi2pk(user_id: str, status: str) -> str:
    """Generate GSI2 partition key for status queries."""
    return f"USER#{user_id}#STATUS#{status}"


def generate_date_gsi2sk(date: str) -> str:
    """Generate GSI2 sort key for date queries."""
    return f"DATE#{date}"


def generate_timestamp() -> str:
    """Generate ISO 8601 timestamp."""
    return datetime.utcnow().isoformat() + 'Z'


def generate_id(prefix: str) -> str:
    """Generate unique ID with prefix."""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
