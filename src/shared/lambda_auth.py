"""
Lambda authorization helpers.

This module provides helper functions to add authorization checks
to Lambda handlers with minimal code changes.
"""

from typing import Dict, Any, Callable
from functools import wraps
from .auth import (
    extract_token_from_event,
    get_user_id_from_token,
    verify_pk_access,
    log_data_access
)
from .exceptions import AuthenticationError, AuthorizationError
from .logger import get_logger

logger = get_logger(__name__)


def authorize_and_extract_user(event: Dict[str, Any]) -> str:
    """
    Extract and validate user from event.
    
    Args:
        event: API Gateway event
        
    Returns:
        User ID
        
    Raises:
        AuthenticationError: If authentication fails
    """
    token = extract_token_from_event(event)
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise AuthenticationError("Invalid user ID")
    
    return user_id


def verify_resource_access(user_id: str, resource_pk: str, resource_type: str, resource_id: str) -> None:
    """
    Verify user can access a resource and log the access attempt.
    
    Args:
        user_id: User ID from token
        resource_pk: Partition key of the resource
        resource_type: Type of resource (transaction, document, etc.)
        resource_id: ID of the resource
        
    Raises:
        AuthorizationError: If user cannot access the resource
    """
    try:
        # Verify PK starts with USER#{user_id}
        verify_pk_access(user_id, resource_pk)
        
        # Log successful access
        log_data_access(user_id, 'read', resource_type, resource_id, success=True)
        
    except AuthorizationError as e:
        # Log failed access attempt
        log_data_access(user_id, 'read', resource_type, resource_id, success=False)
        raise


def log_write_access(user_id: str, action: str, resource_type: str, resource_id: str) -> None:
    """
    Log a write operation (create, update, delete).
    
    Args:
        user_id: User ID performing the action
        action: Action being performed (create, update, delete)
        resource_type: Type of resource
        resource_id: ID of the resource
    """
    log_data_access(user_id, action, resource_type, resource_id, success=True)
