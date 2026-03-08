"""
Lambda authorizer for API Gateway.

This module implements a Lambda authorizer that validates JWT tokens
and generates IAM policies for API Gateway access control.
"""

import json
from typing import Dict, Any
from .auth import validate_token, get_user_id_from_token
from .exceptions import AuthenticationError
from .logger import get_logger

logger = get_logger(__name__)


def generate_policy(
    principal_id: str,
    effect: str,
    resource: str,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate IAM policy for API Gateway.
    
    Args:
        principal_id: User identifier
        effect: 'Allow' or 'Deny'
        resource: API Gateway resource ARN
        context: Additional context to pass to Lambda functions
        
    Returns:
        IAM policy document
    """
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }
    
    if context:
        policy['context'] = context
    
    return policy


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda authorizer handler for API Gateway.
    
    Validates JWT token and returns IAM policy.
    
    Args:
        event: API Gateway authorizer event
        context: Lambda context
        
    Returns:
        IAM policy document
    """
    try:
        # Extract token from event
        token = event.get('authorizationToken', '')
        
        if not token:
            logger.warning("Missing authorization token")
            raise AuthenticationError("Unauthorized")
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Validate token
        decoded = validate_token(token)
        user_id = decoded.get('sub', '')
        email = decoded.get('email', '')
        
        if not user_id:
            logger.warning("Token missing user ID")
            raise AuthenticationError("Invalid token: missing user ID")
        
        # Log successful authentication
        logger.info(f"User authenticated: {user_id}")
        
        # Generate Allow policy
        policy = generate_policy(
            principal_id=user_id,
            effect='Allow',
            resource=event['methodArn'],
            context={
                'userId': user_id,
                'email': email
            }
        )
        
        return policy
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        # Return Deny policy
        return generate_policy(
            principal_id='unauthorized',
            effect='Deny',
            resource=event['methodArn']
        )
    except Exception as e:
        logger.error(f"Authorizer error: {str(e)}")
        # Return Deny policy for any unexpected errors
        return generate_policy(
            principal_id='error',
            effect='Deny',
            resource=event['methodArn']
        )
