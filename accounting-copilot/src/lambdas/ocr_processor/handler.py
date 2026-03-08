"""
Lambda function: OCR Processor
Extracts text from documents using Amazon Textract.
"""

import json
import time
from typing import Dict, Any
from decimal import Decimal
from shared.config import Config
from shared.exceptions import OCRFailure
from shared.aws_clients import s3_client, textract_client, get_dynamodb_table, sns_client
from shared.models import generate_timestamp, OCRStatus
from shared.logger import setup_logger
from shared.document_parser import DocumentParser, DocumentParserError
from shared.error_handler import step_function_error_handler
from shared.xray_tracing import trace_lambda_handler, trace_subsegment, add_annotation, add_metadata

logger = setup_logger(__name__)


def convert_floats_to_decimal(obj):
    """
    Recursively convert all float values to Decimal for DynamoDB compatibility.
    
    Args:
        obj: Object to convert (dict, list, or primitive)
        
    Returns:
        Object with floats converted to Decimal
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    else:
        return obj


def extract_text_from_document(s3_bucket: str, s3_key: str, max_retries: int = 2) -> Dict[str, Any]:
    """
    Extract text from document using Textract with retry logic.
    
    Args:
        s3_bucket: S3 bucket name
        s3_key: S3 object key
        max_retries: Maximum number of retry attempts
        
    Returns:
        Extracted text and parsed fields
        
    Raises:
        OCRFailure: If extraction fails after all retries
    """
    from botocore.exceptions import ClientError
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Starting Textract for s3://{s3_bucket}/{s3_key} (attempt {attempt + 1}/{max_retries + 1})")
            
            # Call Textract
            response = textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                }
            )
            
            # Extract text from blocks
            text_lines = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_lines.append(block['Text'])
            
            extracted_text = '\n'.join(text_lines)
            logger.info(f"Extracted {len(text_lines)} lines of text")
            
            # Parse fields - determine document type from S3 key if possible
            document_type = 'receipt'  # default
            if 'invoice' in s3_key.lower():
                document_type = 'invoice'
            elif 'bank' in s3_key.lower() or 'statement' in s3_key.lower():
                document_type = 'bank_statement'
            
            parsed_fields = parse_document_fields(extracted_text, document_type)
            
            return {
                'extracted_text': extracted_text,
                'parsed_fields': parsed_fields,
                'block_count': len(response.get('Blocks', []))
            }
            
        except DocumentParserError as e:
            # Parsing errors are not retryable - the document content is the issue
            logger.error(f"Document parsing failed: {str(e)}")
            raise OCRFailure(f"Document parsing failed: {str(e)}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            logger.warning(f"Textract attempt {attempt + 1} failed: {error_code} - {str(e)}")
            
            # Don't retry on certain errors
            if error_code in ['InvalidParameterException', 'InvalidS3ObjectException', 'UnsupportedDocumentException']:
                logger.error(f"Non-retryable Textract error: {error_code}")
                raise OCRFailure(f"Invalid document or parameters: {str(e)}")
            
            # Retry with exponential backoff
            if attempt < max_retries:
                backoff_time = 2 ** attempt  # 1s, 2s, 4s...
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
            else:
                logger.error(f"Textract failed after {max_retries + 1} attempts")
                raise OCRFailure(f"Failed to extract text after {max_retries + 1} attempts: {str(e)}")
                
        except Exception as e:
            logger.error(f"Unexpected error during Textract: {str(e)}")
            if attempt < max_retries:
                backoff_time = 2 ** attempt
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
            else:
                raise OCRFailure(f"Failed to extract text from document: {str(e)}")


def send_ocr_failure_notification(document_id: str, user_id: str, error_message: str) -> None:
    """
    Send SNS notification when OCR fails.
    
    Args:
        document_id: Document ID that failed
        user_id: User ID
        error_message: Error message
    """
    try:
        if not Config.SNS_OCR_FAILURES:
            logger.warning("SNS_OCR_FAILURES topic not configured, skipping notification")
            return
        
        message = {
            'document_id': document_id,
            'user_id': user_id,
            'error': error_message,
            'timestamp': generate_timestamp(),
            'action_required': 'Manual entry required'
        }
        
        sns_client.publish(
            TopicArn=Config.SNS_OCR_FAILURES,
            Subject=f'OCR Processing Failed - Document {document_id}',
            Message=json.dumps(message, indent=2)
        )
        
        logger.info(f"Sent OCR failure notification for document {document_id}")
        
    except Exception as e:
        logger.error(f"Failed to send SNS notification: {str(e)}")
        # Don't raise - notification failure shouldn't block the main flow


def parse_document_fields(text: str, document_type: str = 'receipt') -> Dict[str, Any]:
    """
    Parse structured fields from extracted text using the DocumentParser.
    
    Args:
        text: Extracted text
        document_type: Type of document (receipt, invoice, bank_statement)
        
    Returns:
        Parsed fields
        
    Raises:
        DocumentParserError: If required fields are missing or malformed
    """
    try:
        parsed = DocumentParser.parse(text, document_type)
        return parsed
    except DocumentParserError as e:
        logger.error(f"Document parsing failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during parsing: {str(e)}")
        raise DocumentParserError(f"Failed to parse document: {str(e)}")


@step_function_error_handler
@trace_lambda_handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process document with OCR.
    
    Args:
        event: Step Functions event
        context: Lambda context
        
    Returns:
        OCR result
    """
    start_time = time.time()
    
    logger.info(f"Processing OCR request: {json.dumps(event)}")
    
    # Extract parameters
    document_id = event['document_id']
    user_id = event['user_id']
    s3_bucket = event['s3_bucket']
    s3_key = event['s3_key']
    
    add_annotation('document_id', document_id)
    add_annotation('user_id', user_id)
    add_metadata('s3_location', {'bucket': s3_bucket, 'key': s3_key})
    
    try:
        # Update document status to processing
        with trace_subsegment('update_document_status_processing'):
            table = get_dynamodb_table()
            table.update_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': f"DOC#{document_id}"
                },
                UpdateExpression='SET ocr_status = :status',
                ExpressionAttributeValues={
                    ':status': OCRStatus.PROCESSING.value
                }
            )
        
        # Extract text
        with trace_subsegment('extract_text_from_document'):
            result = extract_text_from_document(s3_bucket, s3_key)
        
        # Calculate processing time
        processing_duration_ms = int((time.time() - start_time) * 1000)
        add_metadata('processing_duration_ms', processing_duration_ms)
        
        # Update document in DynamoDB
        with trace_subsegment('update_document_with_results'):
            # Convert any float values to Decimal for DynamoDB
            parsed_fields_decimal = convert_floats_to_decimal(result['parsed_fields'])
            
            table.update_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': f"DOC#{document_id}"
                },
                UpdateExpression='SET ocr_status = :status, extracted_text = :text, '
                               'parsed_fields = :fields, processing_duration_ms = :duration',
                ExpressionAttributeValues={
                    ':status': OCRStatus.COMPLETED.value,
                    ':text': result['extracted_text'],
                    ':fields': parsed_fields_decimal,
                    ':duration': processing_duration_ms
                }
            )
        
        logger.info(f"OCR completed in {processing_duration_ms}ms")
        
        return {
            'status': 'success',
            'document_id': document_id,
            'extracted_text': result['extracted_text'],
            'parsed_fields': result['parsed_fields'],
            'processing_duration_ms': processing_duration_ms
        }
        
    except (OCRFailure, DocumentParserError) as e:
        # Handle OCR and parsing failures
        error_message = e.message if isinstance(e, OCRFailure) else f"Document parsing failed: {str(e)}"
        logger.error(f"OCR/Parsing failure: {error_message}")
        
        # Send SNS notification
        send_ocr_failure_notification(
            document_id=document_id,
            user_id=user_id,
            error_message=error_message
        )
        
        # Update document status to failed
        try:
            table = get_dynamodb_table()
            table.update_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': f"DOC#{document_id}"
                },
                UpdateExpression='SET ocr_status = :status, error_message = :error',
                ExpressionAttributeValues={
                    ':status': OCRStatus.FAILED.value,
                    ':error': error_message
                }
            )
        except Exception as update_error:
            logger.error(f"Failed to update document status: {str(update_error)}")
        
        # Re-raise for Step Functions error handling
        if isinstance(e, OCRFailure):
            raise
        else:
            raise OCRFailure(error_message)
