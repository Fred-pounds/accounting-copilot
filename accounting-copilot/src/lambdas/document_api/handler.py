"""
Lambda function: Document API
Provides document retrieval with pre-signed S3 download URLs.
"""

import json
import os
from typing import Dict, Any

from shared.response import success_response, error_response
from shared.auth import extract_token_from_event, get_user_id_from_token
from shared.lambda_auth import (
    authorize_and_extract_user,
    verify_resource_access,
    log_write_access
)
from shared.exceptions import AppError, ValidationError, NotFoundError
from shared.logger import setup_logger
from shared.dynamodb_repository import DynamoDBRepository
from shared.aws_clients import s3_client

logger = setup_logger(__name__)

# Get configuration from environment
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'AccountingCopilot')
PRESIGNED_URL_EXPIRATION = int(os.environ.get('PRESIGNED_URL_EXPIRATION', '300'))  # 5 minutes


def get_repository() -> DynamoDBRepository:
    """Get or create repository instance."""
    return DynamoDBRepository(TABLE_NAME)


def generate_presigned_download_url(s3_bucket: str, s3_key: str, expiration: int = 300) -> str:
    """
    Generate a pre-signed S3 download URL.
    
    Args:
        s3_bucket: S3 bucket name
        s3_key: S3 object key
        expiration: URL expiration time in seconds (default 300 = 5 minutes)
        
    Returns:
        Pre-signed download URL
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': s3_bucket,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        logger.error(f"Error generating pre-signed URL: {e}")
        raise AppError(f"Failed to generate download URL: {str(e)}")


def lambda_handler_get(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get a single document by ID with pre-signed download URL.
    GET /documents/{id}
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with document metadata and download_url
    """
    request_id = context.aws_request_id
    
    try:
        logger.info(f"Processing get document request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Get document ID from path
        document_id = event.get('pathParameters', {}).get('id')
        if not document_id:
            raise ValidationError("Document ID is required")
        
        # Get repository
        repository = get_repository()
        
        # Get document
        document = repository.get_document(user_id, document_id)
        
        if not document:
            raise NotFoundError(f"Document {document_id} not found")
        
        # Verify user can access this document
        verify_resource_access(user_id, document.PK, 'document', document_id)
        
        # Convert document to dict
        document_data = document.to_dict()
        
        # Generate pre-signed download URL
        try:
            download_url = generate_presigned_download_url(
                document.s3_bucket,
                document.s3_key,
                PRESIGNED_URL_EXPIRATION
            )
            document_data['download_url'] = download_url
        except Exception as e:
            logger.error(f"Failed to generate download URL for document {document_id}: {e}")
            # Include error in response but don't fail the request
            document_data['download_url_error'] = "Failed to generate download URL"
        
        logger.info(f"Retrieved document {document_id} for user {user_id}")
        
        return success_response(document_data)
        
    except AppError as e:
        logger.error(f"Get document error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)


def lambda_handler_list(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List documents with pagination.
    GET /documents
    
    Query parameters:
    - limit: Max results (default 50, max 100)
    - last_evaluated_key: For pagination (base64 encoded JSON)
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with list of documents and pagination info
    """
    request_id = context.aws_request_id
    
    try:
        logger.info(f"Processing list documents request: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Log list access
        log_write_access(user_id, 'list', 'document', 'all')
        
        # Get query parameters
        params = event.get('queryStringParameters') or {}
        limit = int(params.get('limit', 50))
        
        # Validate limit
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100")
        
        # Get repository
        repository = get_repository()
        
        # List documents
        documents = repository.list_documents(user_id, limit)
        
        # Convert to dict format
        documents_data = [doc.to_dict() for doc in documents]
        
        result = {
            'documents': documents_data,
            'count': len(documents_data)
        }
        
        # Note: For full pagination support with last_evaluated_key,
        # we would need to modify the repository method to return
        # the LastEvaluatedKey from DynamoDB and include it in the response
        
        logger.info(f"Retrieved {len(documents)} documents for user {user_id}")
        
        return success_response(result)
        
    except AppError as e:
        logger.error(f"List documents error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)



def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler that routes requests to appropriate handlers.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    http_method = event.get('httpMethod', '')
    path_parameters = event.get('pathParameters') or {}
    
    try:
        if http_method == 'GET':
            # Check if it's a single document request (has ID in path)
            document_id = path_parameters.get('id')
            if document_id:
                return lambda_handler_get(event, context)
            else:
                return lambda_handler_list(event, context)
        else:
            return error_response(
                AppError(f"Unsupported HTTP method: {http_method}", status_code=405),
                context.aws_request_id
            )
    
    except Exception as e:
        logger.exception("Unhandled exception in router")
        return error_response(
            AppError("Internal server error", status_code=500),
            context.aws_request_id
        )
