"""
HTTP response utilities for Lambda functions.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from .exceptions import AppError


def success_response(
    data: Any,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a successful HTTP response.
    
    Args:
        data: Response data to serialize
        status_code: HTTP status code
        headers: Additional headers
        
    Returns:
        API Gateway response dict
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS,POST,PUT,DELETE'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(data, default=str)
    }


def error_response(
    error: AppError,
    request_id: str,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create an error HTTP response.
    
    Args:
        error: Application error
        request_id: Request ID for tracking
        headers: Additional headers
        
    Returns:
        API Gateway response dict
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS,POST,PUT,DELETE'
    }
    
    if headers:
        default_headers.update(headers)
    
    error_body = {
        'error': {
            'code': f'ERR_{error.status_code}',
            'message': error.message,
            'details': error.details,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    }
    
    return {
        'statusCode': error.status_code,
        'headers': default_headers,
        'body': json.dumps(error_body)
    }


def cors_response() -> Dict[str, Any]:
    """
    Create a CORS preflight response.
    
    Returns:
        API Gateway response dict for OPTIONS requests
    """
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,OPTIONS,POST,PUT,DELETE'
        },
        'body': ''
    }
