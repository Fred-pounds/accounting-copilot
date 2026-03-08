"""
Unit tests for data models.
"""

import pytest
from datetime import datetime
from src.shared.models import (
    UserProfile, Document, Transaction, BankTransaction, AuditEntry,
    PendingApproval, ConversationMessage, CategoryStats,
    generate_user_pk, generate_document_sk, generate_transaction_sk,
    generate_bank_transaction_sk, generate_audit_sk, generate_approval_sk,
    generate_conversation_sk, generate_stats_sk,
    generate_category_gsi1pk, generate_date_gsi1sk,
    generate_status_gsi2pk, generate_date_gsi2sk,
    generate_timestamp, generate_id,
    EntityType, TransactionType, TransactionStatus, DocumentType, OCRStatus
)


class TestKeyGeneration:
    """Test key generation functions."""
    
    def test_generate_user_pk(self):
        """Test user partition key generation."""
        user_id = "user123"
        pk = generate_user_pk(user_id)
        assert pk == "USER#user123"
    
    def test_generate_document_sk(self):
        """Test document sort key generation."""
        doc_id = "doc_abc123"
        sk = generate_document_sk(doc_id)
        assert sk == "DOC#doc_abc123"
    
    def test_generate_transaction_sk(self):
        """Test transaction sort key generation."""
        txn_id = "txn_xyz789"
        sk = generate_transaction_sk(txn_id)
        assert sk == "TXN#txn_xyz789"
    
    def test_generate_bank_transaction_sk(self):
        """Test bank transaction sort key generation."""
        bank_txn_id = "bank_456"
        sk = generate_bank_transaction_sk(bank_txn_id)
        assert sk == "BANK#bank_456"

    
    def test_generate_audit_sk(self):
        """Test audit entry sort key generation."""
        timestamp = "2024-01-15T10:30:00Z"
        action_id = "audit_001"
        sk = generate_audit_sk(timestamp, action_id)
        assert sk == "AUDIT#2024-01-15T10:30:00Z#audit_001"
    
    def test_generate_approval_sk(self):
        """Test approval sort key generation."""
        approval_id = "approval_123"
        sk = generate_approval_sk(approval_id)
        assert sk == "APPROVAL#approval_123"
    
    def test_generate_conversation_sk(self):
        """Test conversation message sort key generation."""
        conv_id = "conv_abc"
        msg_id = "msg_001"
        sk = generate_conversation_sk(conv_id, msg_id)
        assert sk == "CONV#conv_abc#MSG#msg_001"
    
    def test_generate_stats_sk(self):
        """Test category stats sort key generation."""
        category = "Office Supplies"
        month = "2024-01"
        sk = generate_stats_sk(category, month)
        assert sk == "STATS#Office Supplies#2024-01"
    
    def test_generate_category_gsi1pk(self):
        """Test GSI1 partition key for category queries."""
        user_id = "user123"
        category = "Office Supplies"
        gsi1pk = generate_category_gsi1pk(user_id, category)
        assert gsi1pk == "USER#user123#CAT#Office Supplies"
    
    def test_generate_date_gsi1sk(self):
        """Test GSI1 sort key for date queries."""
        date = "2024-01-15"
        gsi1sk = generate_date_gsi1sk(date)
        assert gsi1sk == "DATE#2024-01-15"
    
    def test_generate_status_gsi2pk(self):
        """Test GSI2 partition key for status queries."""
        user_id = "user123"
        status = "pending"
        gsi2pk = generate_status_gsi2pk(user_id, status)
        assert gsi2pk == "USER#user123#STATUS#pending"
    
    def test_generate_date_gsi2sk(self):
        """Test GSI2 sort key for date queries."""
        date = "2024-01-15"
        gsi2sk = generate_date_gsi2sk(date)
        assert gsi2sk == "DATE#2024-01-15"
    
    def test_generate_timestamp(self):
        """Test timestamp generation."""
        timestamp = generate_timestamp()
        assert timestamp.endswith('Z')
        # Verify it's a valid ISO 8601 timestamp
        datetime.fromisoformat(timestamp.rstrip('Z'))
    
    def test_generate_id(self):
        """Test ID generation."""
        prefix = "txn"
        id1 = generate_id(prefix)
        id2 = generate_id(prefix)
        
        assert id1.startswith("txn_")
        assert id2.startswith("txn_")
        assert id1 != id2  # Should be unique


class TestUserProfile:
    """Test UserProfile model."""
    
    def test_user_profile_creation(self):
        """Test creating a user profile."""
        profile = UserProfile(
            PK="USER#user123",
            SK="PROFILE",
            email="test@example.com",
            business_name="Test Business",
            created_at="2024-01-15T10:30:00Z"
        )
        
        assert profile.PK == "USER#user123"
        assert profile.SK == "PROFILE"
        assert profile.email == "test@example.com"
        assert profile.entity_type == EntityType.USER_PROFILE.value
    
    def test_user_profile_to_dict(self):
        """Test converting user profile to dictionary."""
        profile = UserProfile(
            PK="USER#user123",
            SK="PROFILE",
            email="test@example.com",
            business_name="Test Business",
            created_at="2024-01-15T10:30:00Z"
        )
        
        data = profile.to_dict()
        assert data['PK'] == "USER#user123"
        assert data['email'] == "test@example.com"
        assert 'custom_categories' in data


class TestDocument:
    """Test Document model."""
    
    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            PK="USER#user123",
            SK="DOC#doc_abc123",
            document_id="doc_abc123",
            s3_key="documents/user123/doc_abc123.jpg",
            s3_bucket="test-bucket",
            upload_timestamp="2024-01-15T10:30:00Z",
            document_type=DocumentType.RECEIPT.value
        )
        
        assert doc.document_id == "doc_abc123"
        assert doc.entity_type == EntityType.DOCUMENT.value
        assert doc.ocr_status == OCRStatus.PENDING.value
    
    def test_document_to_dict(self):
        """Test converting document to dictionary."""
        doc = Document(
            PK="USER#user123",
            SK="DOC#doc_abc123",
            document_id="doc_abc123",
            s3_key="documents/user123/doc_abc123.jpg",
            s3_bucket="test-bucket",
            upload_timestamp="2024-01-15T10:30:00Z",
            document_type=DocumentType.RECEIPT.value
        )
        
        data = doc.to_dict()
        assert data['document_id'] == "doc_abc123"
        assert data['entity_type'] == EntityType.DOCUMENT.value


class TestTransaction:
    """Test Transaction model."""
    
    def test_transaction_creation(self):
        """Test creating a transaction."""
        txn = Transaction(
            PK="USER#user123",
            SK="TXN#txn_xyz789",
            GSI1PK="USER#user123#CAT#Office Supplies",
            GSI1SK="DATE#2024-01-15",
            transaction_id="txn_xyz789",
            date="2024-01-15",
            amount=45.99,
            category="Office Supplies",
            vendor="Office Depot"
        )
        
        assert txn.transaction_id == "txn_xyz789"
        assert txn.amount == 45.99
        assert txn.entity_type == EntityType.TRANSACTION.value
        assert txn.validation_issues == []
    
    def test_transaction_to_dict(self):
        """Test converting transaction to dictionary."""
        txn = Transaction(
            PK="USER#user123",
            SK="TXN#txn_xyz789",
            transaction_id="txn_xyz789",
            date="2024-01-15",
            amount=45.99,
            category="Office Supplies"
        )
        
        data = txn.to_dict()
        assert data['transaction_id'] == "txn_xyz789"
        assert data['amount'] == 45.99


class TestBankTransaction:
    """Test BankTransaction model."""
    
    def test_bank_transaction_creation(self):
        """Test creating a bank transaction."""
        bank_txn = BankTransaction(
            PK="USER#user123",
            SK="BANK#bank_456",
            bank_transaction_id="bank_456",
            date="2024-01-15",
            amount=45.99,
            description="OFFICE DEPOT #1234"
        )
        
        assert bank_txn.bank_transaction_id == "bank_456"
        assert bank_txn.amount == 45.99
        assert bank_txn.reconciliation_status == "unmatched"


class TestAuditEntry:
    """Test AuditEntry model."""
    
    def test_audit_entry_creation(self):
        """Test creating an audit entry."""
        audit = AuditEntry(
            PK="USER#user123",
            SK="AUDIT#2024-01-15T10:30:00Z#audit_001",
            action_id="audit_001",
            timestamp="2024-01-15T10:30:00Z",
            action_type="classification",
            actor="ai",
            subject_type="transaction",
            subject_id="txn_xyz789"
        )
        
        assert audit.action_id == "audit_001"
        assert audit.actor == "ai"
        assert audit.action_details == {}


class TestPendingApproval:
    """Test PendingApproval model."""
    
    def test_pending_approval_creation(self):
        """Test creating a pending approval."""
        approval = PendingApproval(
            PK="USER#user123",
            SK="APPROVAL#approval_123",
            GSI2PK="USER#user123#STATUS#pending",
            GSI2SK="DATE#2024-01-15T10:30:00Z",
            approval_id="approval_123",
            approval_type="new_vendor",
            subject_type="transaction",
            subject_id="txn_xyz789",
            created_at="2024-01-15T10:30:00Z"
        )
        
        assert approval.approval_id == "approval_123"
        assert approval.status == "pending"
        assert approval.details == {}


class TestConversationMessage:
    """Test ConversationMessage model."""
    
    def test_conversation_message_creation(self):
        """Test creating a conversation message."""
        msg = ConversationMessage(
            PK="USER#user123",
            SK="CONV#conv_abc#MSG#msg_001",
            conversation_id="conv_abc",
            message_id="msg_001",
            timestamp="2024-01-15T14:30:00Z",
            role="user",
            content="Can I afford to hire a new employee?"
        )
        
        assert msg.message_id == "msg_001"
        assert msg.role == "user"


class TestCategoryStats:
    """Test CategoryStats model."""
    
    def test_category_stats_creation(self):
        """Test creating category statistics."""
        stats = CategoryStats(
            PK="USER#user123",
            SK="STATS#Office Supplies#2024-01",
            category="Office Supplies",
            month="2024-01",
            transaction_count=15,
            total_amount=450.00,
            average_amount=30.00,
            std_deviation=12.50
        )
        
        assert stats.category == "Office Supplies"
        assert stats.transaction_count == 15
        assert stats.average_amount == 30.00
