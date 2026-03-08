"""
Lambda function: Transaction Classifier
Classifies transactions using Amazon Bedrock.
"""

import json
import time
from typing import Dict, Any, List
from decimal import Decimal
from botocore.exceptions import ClientError
from shared.config import Config
from shared.exceptions import ClassificationError, BedrockError
from shared.aws_clients import bedrock_runtime, get_dynamodb_table
from shared.models import generate_id, generate_timestamp, TransactionType, TransactionStatus
from shared.logger import setup_logger
from shared.audit import log_classification_audit

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

# Default categories
DEFAULT_CATEGORIES = [
    'Office Supplies',
    'Utilities',
    'Marketing',
    'Travel',
    'Salaries',
    'Rent',
    'Equipment',
    'Software',
    'Consulting',
    'Revenue',
    'Other'
]


def get_user_categories(user_id: str) -> List[str]:
    """
    Get user's custom categories from DynamoDB.
    
    Args:
        user_id: User ID
        
    Returns:
        List of categories (default + custom)
    """
    try:
        table = get_dynamodb_table()
        response = table.get_item(
            Key={
                'PK': f"USER#{user_id}",
                'SK': 'PROFILE'
            }
        )
        
        if 'Item' in response:
            custom_categories = response['Item'].get('custom_categories', [])
            # Combine default and custom categories
            return DEFAULT_CATEGORIES + custom_categories
        
        return DEFAULT_CATEGORIES
        
    except Exception as e:
        logger.warning(f"Failed to fetch user categories: {str(e)}, using defaults")
        return DEFAULT_CATEGORIES


def build_classification_prompt(extracted_data: Dict[str, Any], categories: List[str]) -> str:
    """
    Build prompt for Bedrock classification.
    
    Args:
        extracted_data: Extracted document data
        categories: List of available categories
        
    Returns:
        Prompt string
    """
    parsed_fields = extracted_data.get('parsed_fields', {})
    
    # Format categories as bullet list
    category_list = '\n'.join([f"- {cat}" for cat in categories])
    
    prompt = f"""Classify the following transaction into one of these categories:
{category_list}

Transaction details:
- Date: {parsed_fields.get('date', 'Unknown')}
- Amount: {parsed_fields.get('amount', 'Unknown')}
- Vendor: {parsed_fields.get('vendor', 'Unknown')}
- Description: {extracted_data.get('extracted_text', '')[:200]}

Respond with JSON only:
{{
  "category": "category_name",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "transaction_type": "income or expense"
}}"""
    
    return prompt


def fallback_classification(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rule-based fallback classification when Bedrock is unavailable.
    
    Args:
        extracted_data: Extracted document data
        
    Returns:
        Classification result with lower confidence
    """
    parsed_fields = extracted_data.get('parsed_fields', {})
    vendor = parsed_fields.get('vendor', '').lower()
    description = extracted_data.get('extracted_text', '').lower()
    amount = parsed_fields.get('amount', 0.0)
    
    # Simple rule-based classification
    category = 'Other'
    reasoning = 'Fallback rule-based classification'
    transaction_type = TransactionType.EXPENSE.value
    
    # Check vendor and description for keywords
    if any(keyword in vendor or keyword in description for keyword in ['office', 'staples', 'depot', 'paper', 'supplies']):
        category = 'Office Supplies'
        reasoning = 'Vendor/description contains office supply keywords'
    elif any(keyword in vendor or keyword in description for keyword in ['electric', 'power', 'water', 'gas', 'utility']):
        category = 'Utilities'
        reasoning = 'Vendor/description contains utility keywords'
    elif any(keyword in vendor or keyword in description for keyword in ['google', 'facebook', 'ads', 'marketing', 'advertising']):
        category = 'Marketing'
        reasoning = 'Vendor/description contains marketing keywords'
    elif any(keyword in vendor or keyword in description for keyword in ['hotel', 'airline', 'uber', 'lyft', 'travel', 'flight']):
        category = 'Travel'
        reasoning = 'Vendor/description contains travel keywords'
    elif any(keyword in vendor or keyword in description for keyword in ['salary', 'payroll', 'wages']):
        category = 'Salaries'
        reasoning = 'Vendor/description contains salary keywords'
    elif any(keyword in vendor or keyword in description for keyword in ['rent', 'lease', 'landlord']):
        category = 'Rent'
        reasoning = 'Vendor/description contains rent keywords'
    elif any(keyword in vendor or keyword in description for keyword in ['equipment', 'hardware', 'machinery']):
        category = 'Equipment'
        reasoning = 'Vendor/description contains equipment keywords'
    elif any(keyword in vendor or keyword in description for keyword in ['software', 'saas', 'subscription', 'license']):
        category = 'Software'
        reasoning = 'Vendor/description contains software keywords'
    elif any(keyword in vendor or keyword in description for keyword in ['consulting', 'consultant', 'advisory']):
        category = 'Consulting'
        reasoning = 'Vendor/description contains consulting keywords'
    elif any(keyword in vendor or keyword in description for keyword in ['revenue', 'income', 'sales', 'payment received']):
        category = 'Revenue'
        transaction_type = TransactionType.INCOME.value
        reasoning = 'Vendor/description contains revenue keywords'
    
    # Fallback classifications have lower confidence
    confidence = 0.5
    
    logger.info(f"Fallback classification: {category} (confidence: {confidence})")
    
    return {
        'category': category,
        'confidence': confidence,
        'reasoning': reasoning,
        'transaction_type': transaction_type,
        '_fallback': True  # Mark as fallback for audit logging
    }


def classify_with_bedrock(extracted_data: Dict[str, Any], categories: List[str], max_retries: int = 2) -> Dict[str, Any]:
    """
    Classify transaction using Bedrock with retry logic.
    
    Args:
        extracted_data: Extracted document data
        categories: List of available categories
        max_retries: Maximum number of retry attempts
        
    Returns:
        Classification result
        
    Raises:
        BedrockError: If classification fails after all retries
    """
    prompt = build_classification_prompt(extracted_data, categories)
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Calling Bedrock for classification (attempt {attempt + 1}/{max_retries + 1})")
            
            # Call Bedrock
            response = bedrock_runtime.invoke_model(
                modelId=Config.BEDROCK_MODEL_ID,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 500,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Extract JSON from response
            classification = json.loads(content)
            
            # Validate confidence score
            if not isinstance(classification.get('confidence'), (int, float)):
                raise ValueError("Invalid confidence score in response")
            
            confidence = float(classification['confidence'])
            if not (0.0 <= confidence <= 1.0):
                raise ValueError(f"Confidence score {confidence} out of range [0, 1]")
            
            classification['confidence'] = confidence
            
            logger.info(f"Classification: {classification['category']} "
                       f"(confidence: {classification['confidence']})")
            
            return classification
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            logger.warning(f"Bedrock API error (attempt {attempt + 1}): {error_code} - {str(e)}")
            
            if attempt < max_retries:
                # Exponential backoff: 2^attempt seconds
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Bedrock classification failed after {max_retries + 1} attempts")
                raise BedrockError(f"Failed to classify transaction after {max_retries + 1} attempts: {str(e)}")
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse Bedrock response (attempt {attempt + 1}): {str(e)}")
            
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to parse Bedrock response after {max_retries + 1} attempts")
                raise BedrockError(f"Failed to parse classification response: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during classification: {str(e)}")
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise BedrockError(f"Unexpected classification error: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Classify transaction.
    
    Args:
        event: Step Functions event
        context: Lambda context
        
    Returns:
        Classification result
    """
    try:
        logger.info(f"Processing classification request: {json.dumps(event)}")
        
        # Extract parameters
        document_id = event['document_id']
        user_id = event['user_id']
        extracted_data = event['extracted_data']
        
        # Get user's categories (default + custom)
        categories = get_user_categories(user_id)
        logger.info(f"Using {len(categories)} categories for classification")
        
        # Try Bedrock classification with retry logic
        try:
            classification = classify_with_bedrock(extracted_data, categories)
        except BedrockError as e:
            # Fallback to rule-based classification if Bedrock fails
            logger.warning(f"Bedrock unavailable, using fallback classification: {str(e)}")
            classification = fallback_classification(extracted_data)
        
        # Generate transaction ID
        transaction_id = generate_id('txn')
        timestamp = generate_timestamp()
        
        # Get parsed fields
        parsed_fields = extracted_data.get('parsed_fields', {})
        
        # Determine if flagged for review
        confidence = classification['confidence']
        flagged = confidence < Config.CLASSIFICATION_CONFIDENCE_THRESHOLD
        status = TransactionStatus.PENDING_REVIEW.value if flagged else TransactionStatus.APPROVED.value
        
        logger.info(f"Transaction flagged for review: {flagged} (confidence: {confidence}, threshold: {Config.CLASSIFICATION_CONFIDENCE_THRESHOLD})")
        
        # Create transaction record
        transaction = {
            'PK': f"USER#{user_id}",
            'SK': f"TXN#{transaction_id}",
            'GSI1PK': f"USER#{user_id}#CAT#{classification['category']}",
            'GSI1SK': f"DATE#{parsed_fields.get('date', timestamp[:10])}",
            'GSI2PK': f"USER#{user_id}#STATUS#{status}",
            'GSI2SK': f"DATE#{timestamp}",
            'entity_type': 'transaction',
            'transaction_id': transaction_id,
            'date': parsed_fields.get('date', timestamp[:10]),
            'amount': parsed_fields.get('amount', 0.0),
            'currency': parsed_fields.get('currency', 'USD'),
            'type': classification.get('transaction_type', TransactionType.EXPENSE.value),
            'category': classification['category'],
            'vendor': parsed_fields.get('vendor', 'Unknown'),
            'description': extracted_data.get('extracted_text', '')[:500],
            'classification_confidence': confidence,
            'classification_reasoning': classification['reasoning'],
            'status': status,
            'flagged_for_review': flagged,
            'validation_issues': [],
            'source': 'receipt',
            'document_id': document_id,
            'reconciliation_status': 'unmatched',
            'created_at': timestamp,
            'updated_at': timestamp,
            'created_by': 'ai'
        }
        
        # Save to DynamoDB
        table = get_dynamodb_table()
        
        # Convert all float values to Decimal for DynamoDB
        transaction_decimal = convert_floats_to_decimal(transaction)
        
        table.put_item(Item=transaction_decimal)
        
        logger.info(f"Transaction created: {transaction_id} (category: {classification['category']}, confidence: {confidence})")
        
        # Log to audit trail
        actor_details = 'bedrock:claude-3-haiku' if not isinstance(classification.get('_fallback'), bool) or not classification.get('_fallback') else 'fallback_classifier'
        log_classification_audit(
            user_id=user_id,
            transaction_id=transaction_id,
            category=classification['category'],
            confidence=confidence,
            reasoning=classification['reasoning'],
            actor_details=actor_details
        )
        
        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'category': classification['category'],
            'confidence': confidence,
            'flagged_for_review': flagged,
            'transaction_type': classification.get('transaction_type', TransactionType.EXPENSE.value)
        }
        
    except (ClassificationError, BedrockError) as e:
        logger.error(f"Classification error: {e.message}")
        raise e
    except Exception as e:
        logger.exception("Unhandled exception in classifier")
        raise ClassificationError(f"Classification failed: {str(e)}")
