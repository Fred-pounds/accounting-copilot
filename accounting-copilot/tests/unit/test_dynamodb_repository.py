"""
Unit tests for DynamoDB repository layer.
"""

import pytest
from decimal import Decimal
from moto import mock_aws
import boto3
from src.shared.dynamodb_repository import DynamoDBRepository
from src.shared.models import (
    UserProfile, Document, Transaction, BankTransaction, AuditEntry,
    PendingApproval, ConversationMessage, CategoryStats,
    generate_user_pk, generate_document_sk, generate_transaction_sk,
    generate_timestamp, generate_id,
    DocumentType, TransactionType, TransactionStatus
)
from src.shared.exceptions import ValidationError


@pytest.fixture
def dynamodb_table():
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create table
        table = dynamodb.create_table(
            TableName='TestTable',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI2PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI2SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'GSI2',
                    'KeySchema': [
                        {'AttributeName': 'GSI2PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI2SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield dynamodb


@pytest.fixture
def repository(dynamodb_table):
    """Create a repository instance with mock DynamoDB."""
    return DynamoDBRepository('TestTable', dynamodb_resource=dynamodb_table)



class TestUserProfileOperations:
    """Test user profile CRUD operations."""
    
    def test_create_user_profile(self, repository):
        """Test creating a user profile."""
        profile = repository.create_user_profile(
            user_id="user123",
            email="test@example.com",
            business_name="Test Business"
        )
        
        assert profile.PK == "USER#user123"
        assert profile.email == "test@example.com"
        assert profile.business_name == "Test Business"
    
    def test_create_duplicate_user_profile(self, repository):
        """Test that creating duplicate user profile raises error."""
        repository.create_user_profile(
            user_id="user123",
            email="test@example.com",
            business_name="Test Business"
        )
        
        with pytest.raises(ValidationError):
            repository.create_user_profile(
                user_id="user123",
                email="test@example.com",
                business_name="Test Business"
            )
    
    def test_get_user_profile(self, repository):
        """Test retrieving a user profile."""
        repository.create_user_profile(
            user_id="user123",
            email="test@example.com",
            business_name="Test Business"
        )
        
        profile = repository.get_user_profile("user123")
        assert profile is not None
        assert profile.email == "test@example.com"
    
    def test_get_nonexistent_user_profile(self, repository):
        """Test retrieving a non-existent user profile."""
        profile = repository.get_user_profile("nonexistent")
        assert profile is None
    
    def test_update_user_profile(self, repository):
        """Test updating a user profile."""
        repository.create_user_profile(
            user_id="user123",
            email="test@example.com",
            business_name="Test Business"
        )
        
        updated = repository.update_user_profile(
            user_id="user123",
            updates={"business_name": "Updated Business"}
        )
        
        assert updated.business_name == "Updated Business"


class TestDocumentOperations:
    """Test document CRUD operations."""
    
    def test_create_document(self, repository):
        """Test creating a document."""
        doc = Document(
            PK=generate_user_pk("user123"),
            SK=generate_document_sk("doc_abc123"),
            document_id="doc_abc123",
            s3_key="documents/user123/doc_abc123.jpg",
            s3_bucket="test-bucket",
            upload_timestamp=generate_timestamp(),
            document_type=DocumentType.RECEIPT.value
        )
        
        created = repository.create_document("user123", doc)
        assert created.document_id == "doc_abc123"
    
    def test_get_document(self, repository):
        """Test retrieving a document."""
        doc = Document(
            PK=generate_user_pk("user123"),
            SK=generate_document_sk("doc_abc123"),
            document_id="doc_abc123",
            s3_key="documents/user123/doc_abc123.jpg",
            s3_bucket="test-bucket",
            upload_timestamp=generate_timestamp(),
            document_type=DocumentType.RECEIPT.value
        )
        repository.create_document("user123", doc)
        
        retrieved = repository.get_document("user123", "doc_abc123")
        assert retrieved is not None
        assert retrieved.document_id == "doc_abc123"
    
    def test_list_documents(self, repository):
        """Test listing documents."""
        for i in range(3):
            doc = Document(
                PK=generate_user_pk("user123"),
                SK=generate_document_sk(f"doc_{i}"),
                document_id=f"doc_{i}",
                s3_key=f"documents/user123/doc_{i}.jpg",
                s3_bucket="test-bucket",
                upload_timestamp=generate_timestamp(),
                document_type=DocumentType.RECEIPT.value
            )
            repository.create_document("user123", doc)
        
        docs = repository.list_documents("user123")
        assert len(docs) == 3
    
    def test_update_document(self, repository):
        """Test updating a document."""
        doc = Document(
            PK=generate_user_pk("user123"),
            SK=generate_document_sk("doc_abc123"),
            document_id="doc_abc123",
            s3_key="documents/user123/doc_abc123.jpg",
            s3_bucket="test-bucket",
            upload_timestamp=generate_timestamp(),
            document_type=DocumentType.RECEIPT.value
        )
        repository.create_document("user123", doc)
        
        updated = repository.update_document(
            "user123",
            "doc_abc123",
            {"ocr_status": "completed", "extracted_text": "Test text"}
        )
        
        assert updated.ocr_status == "completed"
        assert updated.extracted_text == "Test text"


class TestTransactionOperations:
    """Test transaction CRUD operations."""
    
    def test_create_transaction(self, repository):
        """Test creating a transaction."""
        txn = Transaction(
            PK=generate_user_pk("user123"),
            SK=generate_transaction_sk("txn_xyz789"),
            GSI1PK="USER#user123#CAT#Office Supplies",
            GSI1SK="DATE#2024-01-15",
            GSI2PK="USER#user123#STATUS#pending_review",
            GSI2SK="DATE#2024-01-15",
            transaction_id="txn_xyz789",
            date="2024-01-15",
            amount=45.99,
            category="Office Supplies",
            vendor="Office Depot",
            created_at=generate_timestamp()
        )
        
        created = repository.create_transaction("user123", txn)
        assert created.transaction_id == "txn_xyz789"
        assert created.amount == 45.99
    
    def test_get_transaction(self, repository):
        """Test retrieving a transaction."""
        txn = Transaction(
            PK=generate_user_pk("user123"),
            SK=generate_transaction_sk("txn_xyz789"),
            transaction_id="txn_xyz789",
            date="2024-01-15",
            amount=45.99,
            category="Office Supplies",
            created_at=generate_timestamp()
        )
        repository.create_transaction("user123", txn)
        
        retrieved = repository.get_transaction("user123", "txn_xyz789")
        assert retrieved is not None
        assert retrieved.amount == 45.99
    
    def test_list_transactions(self, repository):
        """Test listing transactions."""
        for i in range(3):
            txn = Transaction(
                PK=generate_user_pk("user123"),
                SK=generate_transaction_sk(f"txn_{i}"),
                transaction_id=f"txn_{i}",
                date="2024-01-15",
                amount=10.0 * (i + 1),
                category="Office Supplies",
                created_at=generate_timestamp()
            )
            repository.create_transaction("user123", txn)
        
        txns = repository.list_transactions("user123")
        assert len(txns) == 3
    
    def test_query_transactions_by_category(self, repository):
        """Test querying transactions by category."""
        # Create transactions in different categories
        for i in range(2):
            txn = Transaction(
                PK=generate_user_pk("user123"),
                SK=generate_transaction_sk(f"txn_office_{i}"),
                GSI1PK="USER#user123#CAT#Office Supplies",
                GSI1SK=f"DATE#2024-01-{15+i:02d}",
                transaction_id=f"txn_office_{i}",
                date=f"2024-01-{15+i:02d}",
                amount=10.0 * (i + 1),
                category="Office Supplies",
                created_at=generate_timestamp()
            )
            repository.create_transaction("user123", txn)
        
        txn = Transaction(
            PK=generate_user_pk("user123"),
            SK=generate_transaction_sk("txn_util_1"),
            GSI1PK="USER#user123#CAT#Utilities",
            GSI1SK="DATE#2024-01-17",
            transaction_id="txn_util_1",
            date="2024-01-17",
            amount=100.0,
            category="Utilities",
            created_at=generate_timestamp()
        )
        repository.create_transaction("user123", txn)
        
        office_txns = repository.query_transactions_by_category("user123", "Office Supplies")
        assert len(office_txns) == 2
        assert all(t.category == "Office Supplies" for t in office_txns)
    
    def test_update_transaction(self, repository):
        """Test updating a transaction."""
        txn = Transaction(
            PK=generate_user_pk("user123"),
            SK=generate_transaction_sk("txn_xyz789"),
            transaction_id="txn_xyz789",
            date="2024-01-15",
            amount=45.99,
            category="Office Supplies",
            created_at=generate_timestamp()
        )
        repository.create_transaction("user123", txn)
        
        updated = repository.update_transaction(
            "user123",
            "txn_xyz789",
            {"status": "approved", "approved_by": "user"}
        )
        
        assert updated.status == "approved"
        assert updated.approved_by == "user"
    
    def test_delete_transaction(self, repository):
        """Test deleting a transaction."""
        txn = Transaction(
            PK=generate_user_pk("user123"),
            SK=generate_transaction_sk("txn_xyz789"),
            transaction_id="txn_xyz789",
            date="2024-01-15",
            amount=45.99,
            category="Office Supplies",
            created_at=generate_timestamp()
        )
        repository.create_transaction("user123", txn)
        
        repository.delete_transaction("user123", "txn_xyz789")
        
        retrieved = repository.get_transaction("user123", "txn_xyz789")
        assert retrieved is None


class TestBankTransactionOperations:
    """Test bank transaction operations."""
    
    def test_create_bank_transaction(self, repository):
        """Test creating a bank transaction."""
        bank_txn = BankTransaction(
            PK=generate_user_pk("user123"),
            SK="BANK#bank_456",
            bank_transaction_id="bank_456",
            date="2024-01-15",
            amount=45.99,
            description="OFFICE DEPOT #1234",
            imported_at=generate_timestamp()
        )
        
        created = repository.create_bank_transaction("user123", bank_txn)
        assert created.bank_transaction_id == "bank_456"
    
    def test_list_bank_transactions(self, repository):
        """Test listing bank transactions."""
        for i in range(3):
            bank_txn = BankTransaction(
                PK=generate_user_pk("user123"),
                SK=f"BANK#bank_{i}",
                bank_transaction_id=f"bank_{i}",
                date="2024-01-15",
                amount=10.0 * (i + 1),
                description=f"Transaction {i}",
                imported_at=generate_timestamp()
            )
            repository.create_bank_transaction("user123", bank_txn)
        
        bank_txns = repository.list_bank_transactions("user123")
        assert len(bank_txns) == 3


class TestAuditEntryOperations:
    """Test audit entry operations."""
    
    def test_create_audit_entry(self, repository):
        """Test creating an audit entry."""
        audit = AuditEntry(
            PK=generate_user_pk("user123"),
            SK="AUDIT#2024-01-15T10:30:00Z#audit_001",
            action_id="audit_001",
            timestamp="2024-01-15T10:30:00Z",
            action_type="classification",
            actor="ai",
            subject_type="transaction",
            subject_id="txn_xyz789",
            result="success"
        )
        
        created = repository.create_audit_entry("user123", audit)
        assert created.action_id == "audit_001"
    
    def test_list_audit_entries(self, repository):
        """Test listing audit entries."""
        for i in range(3):
            audit = AuditEntry(
                PK=generate_user_pk("user123"),
                SK=f"AUDIT#2024-01-15T10:3{i}:00Z#audit_{i:03d}",
                action_id=f"audit_{i:03d}",
                timestamp=f"2024-01-15T10:3{i}:00Z",
                action_type="classification",
                actor="ai",
                subject_type="transaction",
                subject_id=f"txn_{i}",
                result="success"
            )
            repository.create_audit_entry("user123", audit)
        
        audits = repository.list_audit_entries("user123")
        assert len(audits) == 3


class TestBatchOperations:
    """Test batch operations."""
    
    def test_batch_write_items(self, repository):
        """Test batch writing items."""
        items = []
        for i in range(5):
            txn = Transaction(
                PK=generate_user_pk("user123"),
                SK=generate_transaction_sk(f"txn_{i}"),
                transaction_id=f"txn_{i}",
                date="2024-01-15",
                amount=10.0 * (i + 1),
                category="Office Supplies",
                created_at=generate_timestamp()
            )
            items.append(txn.to_dict())
        
        repository.batch_write_items(items)
        
        # Verify items were written
        txns = repository.list_transactions("user123")
        assert len(txns) == 5


class TestDecimalConversion:
    """Test float/Decimal conversion."""
    
    def test_float_to_decimal_conversion(self, repository):
        """Test that floats are converted to Decimal for DynamoDB."""
        txn = Transaction(
            PK=generate_user_pk("user123"),
            SK=generate_transaction_sk("txn_xyz789"),
            transaction_id="txn_xyz789",
            date="2024-01-15",
            amount=45.99,
            category="Office Supplies",
            created_at=generate_timestamp()
        )
        
        repository.create_transaction("user123", txn)
        retrieved = repository.get_transaction("user123", "txn_xyz789")
        
        # Should be converted back to float
        assert isinstance(retrieved.amount, float)
        assert retrieved.amount == 45.99
