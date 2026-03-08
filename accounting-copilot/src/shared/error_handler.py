"""
Centralized error handling utilities for Lambda functions.

This module provides decorators and utilities for consistent error handling
across all Lambda functions, including:
- Try-catch blocks with proper error responses
- CloudWatch logging with appropriate severity levels
- Consistent error JSON format
- Request ID tracking
"""

import json
import functools
import traceback
from typing import Dict, Any, Callable
from datetime import datetime

from .exceptions import AppError, ValidationError, NotFoundError, AuthenticationError
from .response import error_response
from .logger import get_logger

logger = get_logger(__name__)


def lambda_error_handler(func: Callable) -> Callable:
    """
    Decorator for Lambda handlers to provide comprehensive error handling.
    
    This decorator:
    - Catches all exceptions and converts them to proper HTTP responses
    - Logs errors to CloudWatch with appropriate severity levels
    - Returns consistent error JSON format
    - Tracks request IDs for debugging
    
    Usage:
        @lambda_error_handler
        def lambda_handler(event, context):
            # Your handler code
            pass
    
    Args:
        func: Lambda handler function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        request_id = getattr(context, 'request_id', 'local')
        
        try:
            # Log incoming request
            logger.info(
                f"Request started",
                extra={
                    'request_id': request_id,
                    'function_name': getattr(context, 'function_name', 'unknown'),
                    'http_method': event.get('httpMethod'),
                    'path': event.get('path')
                }
            )
            
            # Execute the handler
            result = func(event, context)
            
            # Log successful completion
            logger.info(
                f"Request completed successfully",
                extra={
                    'request_id': request_id,
                    'status_code': result.get('statusCode', 200)
                }
            )
            
            return result
            
        except ValidationError as e:
            # Client errors (400) - log as warning
            logger.warning(
                f"Validation error: {e.message}",
                extra={
                    'request_id': request_id,
                    'error_type': 'ValidationError',
                    'error_details': e.details,
                    'status_code': e.status_code
                }
            )
            return error_response(e, request_id)
            
        except NotFoundError as e:
            # Resource not found (404) - log as warning
            logger.warning(
                f"Resource not found: {e.message}",
                extra={
                    'request_id': request_id,
                    'error_type': 'NotFoundError',
                    'error_details': e.details,
                    'status_code': e.status_code
                }
            )
            return error_response(e, request_id)
            
        except AuthenticationError as e:
            # Authentication errors (401) - log as warning
            logger.warning(
                f"Authentication error: {e.message}",
                extra={
                    'request_id': request_id,
                    'error_type': 'AuthenticationError',
                    'status_code': e.status_code
                }
            )
            return error_response(e, request_id)
            
        except AppError as e:
            # Application errors (4xx/5xx) - log as error
            logger.error(
                f"Application error: {e.message}",
                extra={
                    'request_id': request_id,
                    'error_type': type(e).__name__,
                    'error_details': e.details,
                    'status_code': e.status_code
                }
            )
            return error_response(e, request_id)
            
        except Exception as e:
            # Unexpected errors (500) - log as critical with full traceback
            logger.critical(
                f"Unhandled exception: {str(e)}",
                extra={
                    'request_id': request_id,
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                },
                exc_info=True
            )
            
            # Return generic error to client (don't expose internal details)
            error = AppError(
                "Internal server error",
                status_code=500,
                details={'error_type': type(e).__name__}
            )
            return error_response(error, request_id)
    
    return wrapper


def step_function_error_handler(func: Callable) -> Callable:
    """
    Decorator for Step Functions task handlers to provide error handling.
    
    This decorator:
    - Catches exceptions and logs them appropriately
    - Returns error information in Step Functions format
    - Preserves original exceptions for Step Functions error handling
    
    Usage:
        @step_function_error_handler
        def lambda_handler(event, context):
            # Your handler code
            pass
    
    Args:
        func: Lambda handler function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        request_id = getattr(context, 'request_id', 'local')
        
        try:
            # Log incoming request
            logger.info(
                f"Step Functions task started",
                extra={
                    'request_id': request_id,
                    'function_name': getattr(context, 'function_name', 'unknown')
                }
            )
            
            # Execute the handler
            result = func(event, context)
            
            # Log successful completion
            logger.info(
                f"Step Functions task completed successfully",
                extra={
                    'request_id': request_id,
                    'result_status': result.get('status', 'success')
                }
            )
            
            return result
            
        except AppError as e:
            # Application errors - log and re-raise for Step Functions
            logger.error(
                f"Application error in Step Functions task: {e.message}",
                extra={
                    'request_id': request_id,
                    'error_type': type(e).__name__,
                    'error_details': e.details,
                    'status_code': e.status_code
                }
            )
            # Re-raise to let Step Functions handle the error
            raise
            
        except Exception as e:
            # Unexpected errors - log and re-raise
            logger.critical(
                f"Unhandled exception in Step Functions task: {str(e)}",
                extra={
                    'request_id': request_id,
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                },
                exc_info=True
            )
            # Re-raise to let Step Functions handle the error
            raise
    
    return wrapper


def log_error_with_context(
    error: Exception,
    context: Dict[str, Any],
    severity: str = 'ERROR'
) -> None:
    """
    Log an error with additional context information.
    
    Args:
        error: The exception to log
        context: Additional context information
        severity: Log severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        **context
    }
    
    if isinstance(error, AppError):
        error_data['error_details'] = error.details
        error_data['status_code'] = error.status_code
    
    log_method = getattr(logger, severity.lower(), logger.error)
    log_method(json.dumps(error_data))
