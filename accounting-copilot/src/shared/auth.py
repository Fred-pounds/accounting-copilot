"""
Authentication and authorization utilities.
"""

import requests
from jose import jwt, jwk
from jose.exceptions import JWTError, ExpiredSignatureError
from typing import Dict, Any
from datetime import datetime, timedelta
from .config import Config
from .exceptions import AuthenticationError, AuthorizationError
from .logger import get_logger

logger = get_logger(__name__)

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 15

# Cache for JWKS keys
_jwks_cache = None


def get_jwks_keys() -> Dict[str, Any]:
    """
    Get JWKS keys from Cognito (with caching).
    
    Returns:
        JWKS keys dictionary
    """
    global _jwks_cache
    
    if _jwks_cache is not None:
        return _jwks_cache
    
    region = Config.AWS_REGION
    user_pool_id = Config.COGNITO_USER_POOL_ID
    jwks_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
    
    try:
        response = requests.get(jwks_url, timeout=5)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache
    except Exception as e:
        raise AuthenticationError(f"Failed to fetch JWKS keys: {str(e)}")


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate Cognito JWT token.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    if not token:
        raise AuthenticationError("Missing authentication token")
    
    # Remove 'Bearer ' prefix if present
    if token.startswith('Bearer '):
        token = token[7:]
    
    try:
        # Get JWKS keys
        jwks = get_jwks_keys()
        
        # Get the key ID from token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        
        if not kid:
            raise AuthenticationError("Token missing key ID")
        
        # Find the matching key
        key = None
        for jwk_key in jwks.get('keys', []):
            if jwk_key.get('kid') == kid:
                key = jwk_key
                break
        
        if not key:
            raise AuthenticationError("Matching key not found in JWKS")
        
        # Decode and validate token
        decoded = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=Config.COGNITO_CLIENT_ID,
            options={"verify_exp": True}
        )
        
        return decoded
        
    except ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise AuthenticationError(f"Token validation failed: {str(e)}")


def get_user_id_from_token(token: str) -> str:
    """
    Extract user ID from JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        User ID (sub claim)
    """
    decoded = validate_token(token)
    return decoded.get('sub', '')


def get_user_email_from_token(token: str) -> str:
    """
    Extract user email from JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        User email
    """
    decoded = validate_token(token)
    return decoded.get('email', '')


def extract_token_from_event(event: Dict[str, Any]) -> str:
    """
    Extract JWT token from API Gateway event.
    
    Args:
        event: API Gateway event
        
    Returns:
        JWT token
        
    Raises:
        AuthenticationError: If token is missing
    """
    headers = event.get('headers', {})
    
    # Check Authorization header (case-insensitive)
    auth_header = None
    for key, value in headers.items():
        if key.lower() == 'authorization':
            auth_header = value
            break
    
    if not auth_header:
        raise AuthenticationError("Missing Authorization header")
    
    return auth_header


def check_token_expiration(decoded_token: Dict[str, Any]) -> bool:
    """
    Check if token has expired.
    
    Args:
        decoded_token: Decoded JWT token payload
        
    Returns:
        True if token is still valid, False if expired
    """
    exp = decoded_token.get('exp')
    if not exp:
        return False
    
    expiration_time = datetime.fromtimestamp(exp)
    return datetime.utcnow() < expiration_time


def check_session_timeout(decoded_token: Dict[str, Any]) -> bool:
    """
    Check if session has timed out due to inactivity.
    
    Session timeout is 15 minutes from token issuance.
    
    Args:
        decoded_token: Decoded JWT token payload
        
    Returns:
        True if session is still active, False if timed out
        
    Raises:
        AuthenticationError: If session has timed out
    """
    iat = decoded_token.get('iat')
    if not iat:
        raise AuthenticationError("Token missing issuance time")
    
    issued_time = datetime.fromtimestamp(iat)
    timeout_time = issued_time + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    if datetime.utcnow() > timeout_time:
        logger.warning(f"Session timeout for user {decoded_token.get('sub')}")
        raise AuthenticationError("Session has timed out due to inactivity")
    
    return True


def verify_user_access(user_id: str, resource_user_id: str) -> None:
    """
    Verify that user can only access their own data.
    
    Args:
        user_id: User ID from authentication token
        resource_user_id: User ID from the resource being accessed
        
    Raises:
        AuthorizationError: If user attempts to access another user's data
    """
    if user_id != resource_user_id:
        logger.warning(
            f"Authorization failed: User {user_id} attempted to access "
            f"data belonging to user {resource_user_id}"
        )
        raise AuthorizationError(
            "Access denied: You can only access your own data"
        )


def verify_pk_access(user_id: str, pk: str) -> None:
    """
    Verify that partition key starts with USER#{user_id}.
    
    All data in DynamoDB uses PK format USER#{user_id}.
    This ensures users can only access their own data.
    
    Args:
        user_id: User ID from authentication token
        pk: Partition key from DynamoDB
        
    Raises:
        AuthorizationError: If PK doesn't match user's data
    """
    expected_prefix = f"USER#{user_id}"
    
    if not pk.startswith(expected_prefix):
        logger.warning(
            f"Authorization failed: User {user_id} attempted to access "
            f"resource with PK {pk}"
        )
        raise AuthorizationError(
            "Access denied: You can only access your own data"
        )


def log_data_access(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    success: bool = True
) -> None:
    """
    Log data access attempt to audit trail.
    
    Args:
        user_id: User ID performing the action
        action: Action being performed (read, write, delete)
        resource_type: Type of resource (transaction, document, etc.)
        resource_id: ID of the resource
        success: Whether the access was successful
    """
    logger.info(
        f"Data access: user={user_id}, action={action}, "
        f"resource_type={resource_type}, resource_id={resource_id}, "
        f"success={success}"
    )


def get_user_from_event(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract user information from API Gateway event.
    
    This works with both Lambda authorizer context and direct token validation.
    
    Args:
        event: API Gateway event
        
    Returns:
        Dictionary with userId and email
        
    Raises:
        AuthenticationError: If user information cannot be extracted
    """
    # First try to get from authorizer context (if using Lambda authorizer)
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    
    if authorizer and 'userId' in authorizer:
        return {
            'userId': authorizer['userId'],
            'email': authorizer.get('email', '')
        }
    
    # Fall back to extracting and validating token directly
    token = extract_token_from_event(event)
    decoded = validate_token(token)
    
    return {
        'userId': decoded.get('sub', ''),
        'email': decoded.get('email', '')
    }



def require_auth(handler_func):
    """
    Decorator to require authentication for Lambda handlers.
    
    Extracts user information from event and passes it to the handler.
    Logs all data access attempts.
    
    Usage:
        @require_auth
        def lambda_handler(event, context, user_info):
            user_id = user_info['userId']
            # ... handler logic
    
    Args:
        handler_func: Lambda handler function
        
    Returns:
        Wrapped handler function
    """
    def wrapper(event, context):
        try:
            # Extract and validate user
            user_info = get_user_from_event(event)
            user_id = user_info['userId']
            
            if not user_id:
                raise AuthenticationError("Missing user ID")
            
            # Log authentication success
            logger.info(f"Authenticated request from user {user_id}")
            
            # Call the actual handler with user_info
            return handler_func(event, context, user_info)
            
        except (AuthenticationError, AuthorizationError) as e:
            logger.warning(f"Auth error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in auth decorator: {str(e)}")
            raise
    
    return wrapper
