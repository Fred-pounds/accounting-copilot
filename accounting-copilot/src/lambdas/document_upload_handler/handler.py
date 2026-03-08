"""
Document Upload Handler Lambda Function.

This Lambda function handles document upload requests by:
1. Validating file type and size
2. Generating unique document ID and S3 key
3. Creating pre-signed S3 upload URL
4. Storing document metadata in DynamoDB
5. Initiating Step Functions workflow for processing
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os

from shared.config import Config
from shared.exceptions import ValidationError, AppError
from shared.response import success_response, error_response, cors_response
from shared.entities import Document
from shared.aws_clients import s3_client, sfn_client, get_dynamodb_table
from shared.logger import get_logger
from shared.error_handler import lambda_error_handler
from shared.xray_tracing import trace_lambda_handler, trace_subsegment, add_annotation

logger = get_logger(__name__)

# Allowed file types and extensions
ALLOWED_MIME_TYPES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'application/pdf': '.pdf'
}

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}

# Maximum file size in bytes (10 MB)
MAX_FILE_SIZE = Config.MAX_DOCUMENT_SIZE_MB * 1024 * 1024

# Pre-signed URL expiration (15 minutes)
PRESIGNED_URL_EXPIRATION = 900


def validate_file_metadata(content_type: str, file_size: int, filename: str) -> None:
    """
    Validate file metadata before generating upload URL.
    
    Args:
        content_type: MIME type of the file
        file_size: Size of the file in bytes
        filename: Original filename
        
    Raises:
        ValidationError: If validation fails
    """
    # Validate content type
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"Invalid file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES.keys())}",
            details={'content_type': content_type}
        )
    
    # Validate file size
    if file_size <= 0:
        raise ValidationError(
            "File size must be greater than 0",
            details={'file_size': file_size}
        )
    
    if file_size > MAX_FILE_SIZE:
        raise ValidationError(
            f"File size exceeds maximum allowed size of {Config.MAX_DOCUMENT_SIZE_MB} MB",
            details={
                'file_size': file_size,
                'max_size': MAX_FILE_SIZE
            }
        )
    
    # Validate file extension
    if filename:
        ext = os.path.splitext(filename.lower())[1]
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Invalid file extension. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}",
                details={'extension': ext}
            )


def generate_s3_key(user_id: str, document_id: str, content_type: str) -> str:
    """
    Generate S3 key for document storage.
    
    Args:
        user_id: User ID
        document_id: Unique document ID
        content_type: MIME type of the file
        
    Returns:
        S3 key path
    """
    now = datetime.utcnow()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    
    # Determine document type folder
    if content_type == 'application/pdf':
        doc_type = 'bank_statements'
    else:
        doc_type = 'receipts'
    
    # Get file extension
    extension = ALLOWED_MIME_TYPES.get(content_type, '.bin')
    
    # Format: documents/{user_id}/{doc_type}/{year}/{month}/{document_id}.{ext}
    return f"documents/{user_id}/{doc_type}/{year}/{month}/{document_id}{extension}"


def generate_presigned_upload_url(
    bucket: str,
    key: str,
    content_type: str,
    file_size: int
) -> str:
    """
    Generate pre-signed S3 upload URL.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        content_type: MIME type of the file
        file_size: Size of the file in bytes
        
    Returns:
        Pre-signed upload URL
    """
    try:
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ContentType': content_type,
                'ContentLength': file_size,
                'ServerSideEncryption': 'AES256'
            },
            ExpiresIn=PRESIGNED_URL_EXPIRATION,
            HttpMethod='PUT'
        )
        return url
    except Exception as e:
        logger.error(f"Failed to generate pre-signed URL: {str(e)}")
        raise AppError(
            "Failed to generate upload URL",
            details={'error': str(e)}
        )


def store_document_metadata(document: Document) -> None:
    """
    Store document metadata in DynamoDB.
    
    Args:
        document: Document entity
        
    Raises:
        AppError: If DynamoDB operation fails
    """
    try:
        table = get_dynamodb_table()
        table.put_item(Item=document.to_dynamodb())
        logger.info(f"Stored document metadata: {document.document_id}")
    except Exception as e:
        logger.error(f"Failed to store document metadata: {str(e)}")
        raise AppError(
            "Failed to store document metadata",
            details={'error': str(e)}
        )


def initiate_processing_workflow(
    user_id: str,
    document_id: str,
    s3_bucket: str,
    s3_key: str
) -> str:
    """
    Initiate Step Functions workflow for document processing.
    
    Args:
        user_id: User ID
        document_id: Document ID
        s3_bucket: S3 bucket name
        s3_key: S3 object key
        
    Returns:
        Execution ARN
        
    Raises:
        AppError: If workflow initiation fails
    """
    try:
        workflow_input = {
            'user_id': user_id,
            'document_id': document_id,
            's3_bucket': s3_bucket,
            's3_key': s3_key
        }
        
        response = sfn_client.start_execution(
            stateMachineArn=Config.WORKFLOW_ARN,
            name=f"{document_id}-{int(datetime.utcnow().timestamp())}",
            input=json.dumps(workflow_input)
        )
        
        execution_arn = response['executionArn']
        logger.info(f"Started workflow execution: {execution_arn}")
        return execution_arn
        
    except Exception as e:
        logger.error(f"Failed to initiate workflow: {str(e)}")
        raise AppError(
            "Failed to initiate document processing workflow",
            details={'error': str(e)}
        )


def extract_user_id(event: Dict[str, Any]) -> str:
    """
    Extract user ID from request context.
    
    Args:
        event: Lambda event
        
    Returns:
        User ID
        
    Raises:
        ValidationError: If user ID cannot be extracted
    """
    # Extract from Cognito authorizer claims
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    claims = authorizer.get('claims', {})
    
    user_id = claims.get('sub') or claims.get('cognito:username')
    
    if not user_id:
        raise ValidationError(
            "User ID not found in request context",
            details={'authorizer': authorizer}
        )
    
    return user_id


@lambda_error_handler
@trace_lambda_handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for document upload requests.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.aws_request_id if context else 'local'
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response()
    
    # Extract user ID from auth context
    user_id = extract_user_id(event)
    add_annotation('user_id', user_id)
    
    # Parse request body
    body = json.loads(event.get('body', '{}'))
    
    content_type = body.get('content_type')
    file_size = body.get('file_size')
    filename = body.get('filename', '')
    document_type = body.get('document_type', 'receipt')
    
    # Validate required fields
    if not content_type:
        raise ValidationError("Missing required field: content_type")
    if not file_size:
        raise ValidationError("Missing required field: file_size")
    
    # Validate file metadata
    with trace_subsegment('validate_file', {'content_type': content_type, 'file_size': file_size}):
        validate_file_metadata(content_type, file_size, filename)
    
    # Generate unique document ID
    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    add_annotation('document_id', document_id)
    
    # Generate S3 key
    with trace_subsegment('generate_s3_key'):
        s3_key = generate_s3_key(user_id, document_id, content_type)
    
    # Generate pre-signed upload URL
    with trace_subsegment('generate_presigned_url'):
        upload_url = generate_presigned_upload_url(
            bucket=Config.DOCUMENTS_BUCKET,
            key=s3_key,
            content_type=content_type,
            file_size=file_size
        )
    
    # Create document entity
    document = Document(
        user_id=user_id,
        document_id=document_id,
        s3_key=s3_key,
        s3_bucket=Config.DOCUMENTS_BUCKET,
        upload_timestamp=datetime.utcnow().isoformat() + 'Z',
        document_type=document_type,
        ocr_status='pending'
    )
    
    # Store document metadata
    with trace_subsegment('store_document_metadata'):
        store_document_metadata(document)
    
    # Note: Workflow will be triggered automatically by S3 event after file upload
    logger.info(f"Document metadata stored. Workflow will start after file upload: {document_id}")
    
    # Return response
    response_data = {
        'document_id': document_id,
        'upload_url': upload_url,
        'expires_in': PRESIGNED_URL_EXPIRATION,
        'instructions': {
            'method': 'PUT',
            'headers': {
                'Content-Type': content_type,
                'Content-Length': str(file_size)
            },
            'note': 'Workflow will be triggered automatically after successful upload'
        }
    }
    
    logger.info(f"Document upload initiated: {document_id}")
    
    return success_response(response_data, status_code=201)
