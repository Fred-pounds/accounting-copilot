# Approval Manager Lambda Functions

This module implements approval management functionality for the AI Accounting Copilot, including detection logic for transactions requiring approval and API endpoints for managing pending approvals.

## Overview

The approval manager handles three types of approvals:
1. **Large Transactions**: Transactions exceeding 10% of average monthly expenses
2. **New Vendors**: Vendors not seen in the last 90 days
3. **Bulk Reclassification**: Operations reclassifying 2 or more transactions

## Functions

### Detection Functions

#### `detect_large_transaction(user_id, amount, transaction_date)`
Detects if a transaction exceeds 10% of the user's average monthly expenses.

**Logic**:
- Queries transactions from the last 3 months
- Calculates average monthly expenses from approved expense transactions
- Returns `True` if transaction > 10% of average
- Falls back to $1000 threshold if no historical data exists

**Parameters**:
- `user_id` (str): User ID
- `amount` (Decimal): Transaction amount
- `transaction_date` (str): Transaction date in YYYY-MM-DD format

**Returns**: `bool` - True if transaction is large

#### `detect_new_vendor(user_id, vendor, transaction_date)`
Detects if a vendor is new (not seen in the last 90 days).

**Logic**:
- Queries transactions from the last 90 days
- Performs case-insensitive, whitespace-trimmed vendor name matching
- Returns `True` if vendor not found in historical transactions

**Parameters**:
- `user_id` (str): User ID
- `vendor` (str): Vendor name
- `transaction_date` (str): Transaction date in YYYY-MM-DD format

**Returns**: `bool` - True if vendor is new

#### `detect_bulk_reclassification(transaction_ids)`
Detects if an operation is a bulk reclassification (>= 2 transactions).

**Parameters**:
- `transaction_ids` (List[str]): List of transaction IDs

**Returns**: `bool` - True if >= 2 transactions

#### `create_pending_approval(user_id, approval_type, subject_type, subject_id, details)`
Creates a pending approval record in DynamoDB.

**Parameters**:
- `user_id` (str): User ID
- `approval_type` (str): Type of approval (large_transaction, new_vendor, bulk_reclassification)
- `subject_type` (str): Type of subject (transaction, transactions)
- `subject_id` (str): ID of subject (transaction_id or comma-separated IDs)
- `details` (Dict): Additional details about the approval

**Returns**: `PendingApproval` - Created approval entity

### API Endpoints

#### `lambda_handler_list_pending(event, context)`
**Endpoint**: `GET /approvals/pending`

Lists all pending approvals for the authenticated user.

**Response**:
```json
{
  "approvals": [
    {
      "approval_id": "approval_abc123",
      "approval_type": "large_transaction",
      "subject_type": "transaction",
      "subject_id": "txn_xyz789",
      "created_at": "2024-01-15T10:30:00Z",
      "status": "pending",
      "details": {
        "amount": 1500.0,
        "reason": "Exceeds 10% of average monthly expenses"
      }
    }
  ],
  "count": 1
}
```

#### `lambda_handler_approve(event, context)`
**Endpoint**: `POST /approvals/{id}/approve`

Approves a pending approval and updates related transactions.

**Behavior**:
- For `large_transaction` and `new_vendor`: Updates single transaction to "approved" status
- For `bulk_reclassification`: Updates all transactions with new category and "approved" status
- Removes approval from pending index (GSI2)

**Response**:
```json
{
  "message": "Approval processed successfully",
  "approval_id": "approval_abc123",
  "status": "approved"
}
```

#### `lambda_handler_reject(event, context)`
**Endpoint**: `POST /approvals/{id}/reject`

Rejects a pending approval and updates related transactions.

**Request Body** (optional):
```json
{
  "reason": "Too expensive"
}
```

**Behavior**:
- For `large_transaction` and `new_vendor`: Updates single transaction to "rejected" status
- For `bulk_reclassification`: No transaction updates (original categories remain)
- Removes approval from pending index (GSI2)

**Response**:
```json
{
  "message": "Approval rejected successfully",
  "approval_id": "approval_abc123",
  "status": "rejected"
}
```

## Usage Example

### Creating a Pending Approval

```python
from src.lambdas.approval_manager.handler import (
    detect_large_transaction,
    create_pending_approval
)

# Check if transaction requires approval
user_id = "user123"
amount = Decimal("1500.0")
transaction_date = "2024-01-15"

if detect_large_transaction(user_id, amount, transaction_date):
    # Create pending approval
    approval = create_pending_approval(
        user_id=user_id,
        approval_type="large_transaction",
        subject_type="transaction",
        subject_id="txn_xyz789",
        details={
            "amount": float(amount),
            "reason": "Exceeds 10% of average monthly expenses"
        }
    )
    print(f"Created approval: {approval.approval_id}")
```

### Integrating with Transaction Processing

```python
# In transaction classifier or validator
from src.lambdas.approval_manager.handler import (
    detect_large_transaction,
    detect_new_vendor,
    create_pending_approval
)

def process_transaction(user_id, transaction):
    # Check for approval requirements
    requires_approval = False
    approval_type = None
    approval_reason = None
    
    # Check large transaction
    if detect_large_transaction(user_id, transaction.amount, transaction.date):
        requires_approval = True
        approval_type = "large_transaction"
        approval_reason = "Exceeds 10% of average monthly expenses"
    
    # Check new vendor
    elif detect_new_vendor(user_id, transaction.vendor, transaction.date):
        requires_approval = True
        approval_type = "new_vendor"
        approval_reason = f"New vendor: {transaction.vendor}"
    
    if requires_approval:
        # Create pending approval
        create_pending_approval(
            user_id=user_id,
            approval_type=approval_type,
            subject_type="transaction",
            subject_id=transaction.transaction_id,
            details={
                "amount": float(transaction.amount),
                "vendor": transaction.vendor,
                "reason": approval_reason
            }
        )
        # Set transaction status to pending_review
        transaction.status = "pending_review"
        transaction.flagged_for_review = True
```

## Environment Variables

- `DYNAMODB_TABLE`: Name of the DynamoDB table (default: "AccountingCopilot")

## Error Handling

All functions handle errors gracefully:
- Detection functions return `False` on error (default to not requiring approval)
- API handlers return appropriate HTTP error responses
- All errors are logged for debugging

## Testing

Run unit tests:
```bash
pytest tests/unit/test_approval_manager.py -v
```

## Requirements Validated

This implementation validates the following requirements:
- **8.1**: Large transaction approval (> 10% of average monthly expenses)
- **8.2**: New vendor approval
- **8.3**: Bulk reclassification approval (>= 2 transactions)
- **8.4**: Display pending approvals (via GET /approvals/pending endpoint)
