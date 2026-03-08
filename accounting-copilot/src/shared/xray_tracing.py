"""
AWS X-Ray tracing utilities for Lambda functions.

This module provides utilities for enabling X-Ray tracing across all Lambda functions,
including:
- Automatic patching of boto3 clients for tracing
- Custom subsegments for key operations
- Context managers for tracing code blocks
"""

import os
import functools
from typing import Callable, Any, Dict, Optional
from contextlib import contextmanager

# Check if X-Ray is enabled via environment variable
XRAY_ENABLED = os.environ.get('XRAY_ENABLED', 'true').lower() == 'true'

# Import X-Ray SDK only if enabled
if XRAY_ENABLED:
    try:
        from aws_xray_sdk.core import xray_recorder, patch_all
        from aws_xray_sdk.core.context import Context
        
        # Patch all supported libraries (boto3, botocore, requests, etc.)
        patch_all()
        
    except ImportError:
        # X-Ray SDK not installed, disable tracing
        XRAY_ENABLED = False
        xray_recorder = None
else:
    xray_recorder = None


def trace_lambda_handler(func: Callable) -> Callable:
    """
    Decorator to enable X-Ray tracing for Lambda handlers.
    
    This decorator automatically creates a segment for the Lambda invocation
    and adds metadata about the request.
    
    Usage:
        @trace_lambda_handler
        def lambda_handler(event, context):
            # Your handler code
            pass
    
    Args:
        func: Lambda handler function to wrap
        
    Returns:
        Wrapped function with X-Ray tracing
    """
    if not XRAY_ENABLED or xray_recorder is None:
        # X-Ray disabled, return original function
        return func
    
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Any:
        # Add metadata to the segment
        try:
            xray_recorder.put_metadata('function_name', getattr(context, 'function_name', 'unknown'))
            xray_recorder.put_metadata('request_id', getattr(context, 'request_id', 'unknown'))
            
            # Add HTTP method and path if available (API Gateway)
            if 'httpMethod' in event:
                xray_recorder.put_annotation('http_method', event['httpMethod'])
            if 'path' in event:
                xray_recorder.put_annotation('path', event['path'])
            
            # Add user ID if available
            request_context = event.get('requestContext', {})
            authorizer = request_context.get('authorizer', {})
            claims = authorizer.get('claims', {})
            user_id = claims.get('sub') or claims.get('cognito:username')
            if user_id:
                xray_recorder.put_annotation('user_id', user_id)
        
        except Exception:
            # Don't fail if metadata/annotation fails
            pass
        
        # Execute the handler
        return func(event, context)
    
    return wrapper


@contextmanager
def trace_subsegment(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Context manager for creating custom X-Ray subsegments.
    
    Use this to trace specific operations within your Lambda function.
    
    Usage:
        with trace_subsegment('database_query', {'table': 'transactions'}):
            # Your code here
            result = table.query(...)
    
    Args:
        name: Name of the subsegment
        metadata: Optional metadata to attach to the subsegment
        
    Yields:
        The subsegment object (or None if X-Ray is disabled)
    """
    if not XRAY_ENABLED or xray_recorder is None:
        # X-Ray disabled, just execute the code block
        yield None
        return
    
    subsegment = xray_recorder.begin_subsegment(name)
    
    try:
        # Add metadata if provided
        if metadata:
            for key, value in metadata.items():
                try:
                    xray_recorder.put_metadata(key, value)
                except Exception:
                    # Don't fail if metadata fails
                    pass
        
        yield subsegment
        
    except Exception as e:
        # Record the exception in the subsegment
        try:
            xray_recorder.put_metadata('error', str(e))
            xray_recorder.put_metadata('error_type', type(e).__name__)
        except Exception:
            pass
        raise
        
    finally:
        xray_recorder.end_subsegment()


def trace_function(name: Optional[str] = None):
    """
    Decorator to trace a specific function with a custom subsegment.
    
    Usage:
        @trace_function('process_transaction')
        def process_transaction(transaction_id):
            # Your code here
            pass
    
    Args:
        name: Optional name for the subsegment (defaults to function name)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        if not XRAY_ENABLED or xray_recorder is None:
            # X-Ray disabled, return original function
            return func
        
        subsegment_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with trace_subsegment(subsegment_name):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def add_annotation(key: str, value: Any) -> None:
    """
    Add an annotation to the current X-Ray segment/subsegment.
    
    Annotations are indexed and can be used for filtering traces.
    
    Args:
        key: Annotation key
        value: Annotation value (must be string, number, or boolean)
    """
    if not XRAY_ENABLED or xray_recorder is None:
        return
    
    try:
        xray_recorder.put_annotation(key, value)
    except Exception:
        # Don't fail if annotation fails
        pass


def add_metadata(key: str, value: Any, namespace: str = 'default') -> None:
    """
    Add metadata to the current X-Ray segment/subsegment.
    
    Metadata is not indexed but can contain any JSON-serializable data.
    
    Args:
        key: Metadata key
        value: Metadata value (any JSON-serializable object)
        namespace: Optional namespace for organizing metadata
    """
    if not XRAY_ENABLED or xray_recorder is None:
        return
    
    try:
        xray_recorder.put_metadata(key, value, namespace)
    except Exception:
        # Don't fail if metadata fails
        pass


def trace_aws_client(client_name: str):
    """
    Ensure an AWS client is patched for X-Ray tracing.
    
    This is automatically done by patch_all(), but can be called
    explicitly if needed.
    
    Args:
        client_name: Name of the AWS service (e.g., 'dynamodb', 's3', 'textract')
    """
    if not XRAY_ENABLED:
        return
    
    try:
        from aws_xray_sdk.core import patch
        patch([client_name])
    except Exception:
        # Don't fail if patching fails
        pass
