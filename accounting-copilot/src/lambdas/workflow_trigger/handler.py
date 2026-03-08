"""
Workflow Trigger Lambda Function.

This Lambda function is triggered by S3 events when documents are uploaded.
It extracts metadata from the S3 event and initiates the Step Functions workflow.
"""

import json
import urllib.parse
from datetime import datetime
from typing import Dict, Any
import boto3

from shared.config import Config
from shared.logger import get_logger

logger = get_logger(__name__)

sfn_client = boto3.client('stepfunctions')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle S3 event and trigger Step Functions workflow.
    
    Args:
        event: S3 event
        context: Lambda context
        
    Returns:
        Response with execution details
    """
    request_id = context.aws_request_id
    logger.info(f"Processing S3 event: {request_id}")
    
    executions = []
    
    # Process each S3 record
    for record in event.get('Records', []):
        try:
            # Extract S3 details
            s3_bucket = record['s3']['bucket']['name']
            s3_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
            
            logger.info(f"Processing file: s3://{s3_bucket}/{s3_key}")
            
            # Extract metadata from S3 key
            # Format: documents/{user_id}/{doc_type}/{year}/{month}/{document_id}.{ext}
            key_parts = s3_key.split('/')
            
            if len(key_parts) < 6 or key_parts[0] != 'documents':
                logger.warning(f"Skipping file with unexpected key format: {s3_key}")
                continue
            
            user_id = key_parts[1]
            document_id = key_parts[5].split('.')[0]  # Remove extension
            
            # Prepare workflow input
            workflow_input = {
                'user_id': user_id,
                'document_id': document_id,
                's3_bucket': s3_bucket,
                's3_key': s3_key
            }
            
            # Start Step Functions execution
            response = sfn_client.start_execution(
                stateMachineArn=Config.WORKFLOW_ARN,
                name=f"{document_id}-{int(datetime.utcnow().timestamp())}",
                input=json.dumps(workflow_input)
            )
            
            execution_arn = response['executionArn']
            logger.info(f"Started workflow execution: {execution_arn}")
            
            executions.append({
                'document_id': document_id,
                'execution_arn': execution_arn
            })
            
        except Exception as e:
            logger.error(f"Failed to process S3 record: {str(e)}", exc_info=True)
            # Continue processing other records
            continue
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {len(executions)} documents',
            'executions': executions
        })
    }
