# Authentication and Authorization Implementation

This document describes the authentication and authorization implementation for the AI Accounting Copilot.

## Overview

The system uses AWS Cognito for authentication with JWT tokens. All API endpoints require authentication, and authorization checks ensure users can only access their own data.

## Components

### 1. Authentication Utilities (`auth.py`)

Core authentication functions:

- **`validate_token(token: str)`**: Validates JWT token using Cognito JWKS
- **`get_user_id_from_token(token: str)`**: Extracts user ID from token
- **`check_token_expiration(decoded_token: Dict)`**: Checks if token has expired
- **`check_session_timeout(decoded_token: Dict)`**: Enforces 15-minute session timeout
- **`extract_token_from_event(event: Dict)`**: Extracts token from API Gateway event

### 2. Authorization Utilities (`auth.py`)

Authorization and access control functions:

- **`verify_user_access(user_id: str, resource_user_id: str)`**: Verifies user can access resource
- **`verify_pk_access(user_id: str, pk: str)`**: Verifies PK starts with `USER#{user_id}`
- **`log_data_access(...)`**: Logs all data access attempts to audit trail

### 3. Lambda Authorizer (`authorizer.py`)

API Gateway Lambda authorizer that:
- Validates JWT tokens
- Returns IAM policy (Allow/Deny)
- Passes user context to Lambda functions
- Logs authentication attempts

### 4. Lambda Authorization Helpers (`lambda_auth.py`)

Helper functions for Lambda handlers:

- **`authorize_and_extract_user(event: Dict)`**: Extract and validate user from event
- **`verify_resource_access(...)`**: Verify user can access a resource and log access
- **`log_write_access(...)`**: Log write operations (create, update, delete)

## Session Timeout

The system enforces a 15-minute inactivity timeout:

- Tokens are checked for expiration (standard JWT `exp` claim)
- Session timeout is calculated from token issuance time (`iat` claim)
- After 15 minutes of inactivity, users must re-authenticate

## Authorization Model

### Data Isolation

All data in DynamoDB uses partition keys with format: `USER#{user_id}`

This ensures:
1. Users can only query their own data
2. Cross-user data access is prevented at the database level
3. Authorization checks verify PK matches authenticated user

### Access Control Flow

1. **Authentication**: Extract and validate JWT token
2. **User Extraction**: Get user ID from token
3. **Resource Access**: Verify resource PK starts with `USER#{user_id}`
4. **Audit Logging**: Log all data access attempts

### Example Authorization Check

```python
# In Lambda handler
user_id = authorize_and_extract_user(event)

# Get resource
transaction = repository.get_transaction(user_id, transaction_id)

# Verify access
verify_resource_access(user_id, transaction.PK, 'transaction', transaction_id)
```

## Audit Trail

All data access attempts are logged with:
- User ID
- Action (read, write, delete, etc.)
- Resource type (transaction, document, etc.)
- Resource ID
- Success/failure status
- Timestamp

## Lambda Handler Updates

All Lambda handlers have been updated with authorization checks:

### Transaction API (`transaction_api/handler.py`)
- ✅ Create: Logs write access
- ✅ Get: Verifies PK access, logs read access
- ✅ List: Logs list access
- ✅ Update: Verifies PK access, logs write access
- ✅ Delete: Verifies PK access, logs write access
- ✅ Approve: Verifies PK access, logs write access
- ✅ Correct: Verifies PK access, logs write access

### Document API (`document_api/handler.py`)
- ✅ Get: Verifies PK access, logs read access
- ✅ List: Logs list access

### Dashboard API (`dashboard_api/handler.py`)
- ✅ Get Summary: Logs read access

### Audit Trail API (`audit_trail_api/handler.py`)
- ✅ Query: Logs read access
- ✅ Export CSV: Logs export access

### Financial Assistant (`financial_assistant/handler.py`)
- ✅ Query: Logs query access

### Approval Manager (`approval_manager/handler.py`)
- ✅ List Pending: Logs list access
- ✅ Approve: Verifies PK access, logs approve access
- ✅ Reject: Verifies PK access, logs reject access

## Security Features

### 1. Token Validation
- JWT signature verification using Cognito JWKS
- Token expiration checking
- Audience validation

### 2. Session Management
- 15-minute inactivity timeout
- Automatic session invalidation
- Token refresh support

### 3. Authorization Checks
- PK-based access control
- User data isolation
- Cross-user access prevention

### 4. Audit Logging
- All access attempts logged
- Failed access attempts tracked
- Comprehensive audit trail

### 5. Error Handling
- 401 Unauthorized for authentication failures
- 403 Forbidden for authorization failures
- Detailed error messages for debugging
- Security-safe error responses to clients

## Configuration

Required environment variables:

```bash
COGNITO_USER_POOL_ID=<user-pool-id>
COGNITO_CLIENT_ID=<client-id>
AWS_REGION=<region>
```

## Testing

To test authentication and authorization:

1. **Valid Token**: Should allow access to user's own data
2. **Expired Token**: Should return 401 Unauthorized
3. **Invalid Token**: Should return 401 Unauthorized
4. **Cross-User Access**: Should return 403 Forbidden
5. **Session Timeout**: Should return 401 after 15 minutes

## Requirements Validation

This implementation satisfies:

- ✅ **Requirement 10.4**: Authentication required for all financial data endpoints
- ✅ **Requirement 10.5**: 15-minute session timeout enforced
- ✅ **Requirement 10.6**: All data access attempts logged to audit trail

## Future Enhancements

Potential improvements:

1. **MFA Support**: Add multi-factor authentication
2. **Role-Based Access Control**: Support for different user roles
3. **API Rate Limiting**: Prevent abuse
4. **Token Refresh**: Automatic token refresh before expiration
5. **Session Management**: Track active sessions in DynamoDB
