"""
Lambda function: Financial Assistant
Conversational AI for answering financial questions.
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from shared.response import success_response, error_response
from shared.auth import extract_token_from_event, get_user_id_from_token
from shared.lambda_auth import authorize_and_extract_user, log_write_access
from shared.exceptions import AppError, ValidationError
from shared.logger import setup_logger
from shared.audit import log_assistant_query_audit
from shared.aws_clients import bedrock_runtime, get_dynamodb_table
from shared.config import Config
from shared.models import ConversationMessage, generate_id, generate_timestamp

logger = setup_logger(__name__)


def query_relevant_transactions(user_id: str, question: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Query relevant transaction data based on question context.
    
    Args:
        user_id: User ID
        question: User's question
        limit: Maximum number of transactions to retrieve
        
    Returns:
        List of transaction dictionaries
    """
    table = get_dynamodb_table()
    
    # Determine date range based on question keywords
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)  # Default: last 3 months
    
    # Adjust date range based on question
    question_lower = question.lower()
    if 'this month' in question_lower or 'current month' in question_lower:
        start_date = end_date.replace(day=1)
    elif 'last month' in question_lower:
        start_date = (end_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        end_date = end_date.replace(day=1) - timedelta(days=1)
    elif 'this year' in question_lower or 'current year' in question_lower:
        start_date = end_date.replace(month=1, day=1)
    elif 'last year' in question_lower:
        start_date = end_date.replace(year=end_date.year - 1, month=1, day=1)
        end_date = end_date.replace(year=end_date.year - 1, month=12, day=31)
    
    # Query transactions
    try:
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'USER#{user_id}',
                ':sk': 'TXN#'
            },
            Limit=limit
        )
        
        transactions = response.get('Items', [])
        
        # Filter by date range
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        filtered_transactions = [
            txn for txn in transactions
            if start_date_str <= txn.get('date', '') <= end_date_str
        ]
        
        logger.info(f"Retrieved {len(filtered_transactions)} transactions for context")
        return filtered_transactions
        
    except Exception as e:
        logger.error(f"Error querying transactions: {e}")
        return []


def get_conversation_history(user_id: str, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get last N conversation turns for context.
    
    Args:
        user_id: User ID
        conversation_id: Conversation ID
        limit: Maximum number of messages to retrieve
        
    Returns:
        List of conversation messages
    """
    table = get_dynamodb_table()
    
    try:
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'USER#{user_id}',
                ':sk': f'CONV#{conversation_id}#MSG#'
            },
            Limit=limit,
            ScanIndexForward=False  # Most recent first
        )
        
        messages = response.get('Items', [])
        # Reverse to get chronological order
        messages.reverse()
        
        logger.info(f"Retrieved {len(messages)} conversation messages")
        return messages
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        return []


def build_transaction_summary(transactions: List[Dict[str, Any]]) -> str:
    """
    Build a summary of transactions for the prompt.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Formatted transaction summary
    """
    if not transactions:
        return "No transaction data available."
    
    summary_lines = []
    summary_lines.append(f"Transaction Data ({len(transactions)} transactions):\n")
    
    # Group by type
    income_txns = [t for t in transactions if t.get('type') == 'income']
    expense_txns = [t for t in transactions if t.get('type') == 'expense']
    
    # Calculate totals
    total_income = sum(Decimal(t.get('amount', '0')) for t in income_txns)
    total_expenses = sum(Decimal(t.get('amount', '0')) for t in expense_txns)
    
    summary_lines.append(f"Total Income: ${total_income:.2f}")
    summary_lines.append(f"Total Expenses: ${total_expenses:.2f}")
    summary_lines.append(f"Net: ${(total_income - total_expenses):.2f}\n")
    
    # Group expenses by category
    category_totals = {}
    for txn in expense_txns:
        category = txn.get('category', 'Uncategorized')
        amount = Decimal(txn.get('amount', '0'))
        category_totals[category] = category_totals.get(category, Decimal('0')) + amount
    
    if category_totals:
        summary_lines.append("Expenses by Category:")
        for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            summary_lines.append(f"  - {category}: ${amount:.2f}")
        summary_lines.append("")
    
    # Include sample transactions for reference
    summary_lines.append("Sample Transactions:")
    for txn in transactions[:10]:  # First 10 transactions
        txn_id = txn.get('transaction_id', 'unknown')
        date = txn.get('date', 'unknown')
        vendor = txn.get('vendor', 'unknown')
        amount = txn.get('amount', '0')
        category = txn.get('category', 'unknown')
        txn_type = txn.get('type', 'unknown')
        
        summary_lines.append(
            f"  [{txn_id}] {date} - {vendor}: ${amount} ({category}, {txn_type})"
        )
    
    return "\n".join(summary_lines)


def build_conversation_context(messages: List[Dict[str, Any]]) -> str:
    """
    Build conversation history for the prompt.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        Formatted conversation history
    """
    if not messages:
        return "No previous conversation."
    
    context_lines = []
    for msg in messages:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        
        if role == 'user':
            context_lines.append(f"User: {content}")
        elif role == 'assistant':
            response = msg.get('response', {})
            answer = response.get('content', content)
            context_lines.append(f"Assistant: {answer}")
    
    return "\n".join(context_lines)


def build_prompt(question: str, transaction_summary: str, conversation_history: str) -> str:
    """
    Build the prompt for Bedrock.
    
    Args:
        question: User's question
        transaction_summary: Summary of relevant transactions
        conversation_history: Previous conversation turns
        
    Returns:
        Formatted prompt
    """
    prompt = f"""You are a financial assistant for an SME owner. Answer questions about their business finances using the provided transaction data.

{transaction_summary}

Conversation history:
{conversation_history}

User question: {question}

Provide a clear answer in plain language. Cite specific transactions or data points as evidence using the format [transaction_id]. If you don't have enough data to answer the question, explain what specific data is missing. Keep your response concise and actionable."""
    
    return prompt


def call_bedrock(prompt: str) -> Dict[str, Any]:
    """
    Call Bedrock Claude 3 Haiku model.
    
    Args:
        prompt: The prompt to send
        
    Returns:
        Response from Bedrock
    """
    try:
        request_body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.7
        }
        
        response = bedrock_runtime.invoke_model(
            modelId=Config.BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        logger.info("Successfully called Bedrock")
        return response_body
        
    except Exception as e:
        logger.error(f"Error calling Bedrock: {e}")
        raise AppError(f"Failed to generate response: {str(e)}")


def extract_citations(response_text: str) -> List[str]:
    """
    Extract transaction citations from response.
    
    Args:
        response_text: The assistant's response
        
    Returns:
        List of transaction IDs cited
    """
    # Find all [transaction_id] patterns
    citations = re.findall(r'\[([^\]]+)\]', response_text)
    
    # Filter to only transaction IDs (start with txn_)
    transaction_citations = [c for c in citations if c.startswith('txn_')]
    
    logger.info(f"Extracted {len(transaction_citations)} citations")
    return transaction_citations


def check_insufficient_data(transactions: List[Dict[str, Any]], question: str) -> Optional[str]:
    """
    Check if there's insufficient data to answer the question.
    
    Args:
        transactions: Available transactions
        question: User's question
        
    Returns:
        Explanation message if data is insufficient, None otherwise
    """
    if not transactions:
        return "I don't have any transaction data to analyze. Please upload some financial documents or add transactions manually to get started."
    
    question_lower = question.lower()
    
    # Check for specific data requirements
    if 'revenue' in question_lower or 'income' in question_lower:
        income_txns = [t for t in transactions if t.get('type') == 'income']
        if not income_txns:
            return "I don't have any income transactions recorded yet. Please add income data to analyze revenue."
    
    if 'expense' in question_lower or 'spending' in question_lower or 'cost' in question_lower:
        expense_txns = [t for t in transactions if t.get('type') == 'expense']
        if not expense_txns:
            return "I don't have any expense transactions recorded yet. Please add expense data to analyze spending."
    
    # Check for time-based questions
    if len(transactions) < 5:
        return f"I only have {len(transactions)} transaction(s) available, which may not be enough for a comprehensive analysis. Please add more transaction data for better insights."
    
    return None


def store_conversation_message(user_id: str, conversation_id: str, question: str, 
                               answer: str, citations: List[str], confidence: float) -> None:
    """
    Store conversation message in DynamoDB.
    
    Args:
        user_id: User ID
        conversation_id: Conversation ID
        question: User's question
        answer: Assistant's answer
        citations: List of transaction IDs cited
        confidence: Confidence score
    """
    table = get_dynamodb_table()
    
    # Store user message
    user_message_id = generate_id('msg')
    user_message = ConversationMessage(
        PK=f'USER#{user_id}',
        SK=f'CONV#{conversation_id}#MSG#{user_message_id}',
        conversation_id=conversation_id,
        message_id=user_message_id,
        timestamp=generate_timestamp(),
        role='user',
        content=question
    )
    
    # Store assistant message
    assistant_message_id = generate_id('msg')
    assistant_message = ConversationMessage(
        PK=f'USER#{user_id}',
        SK=f'CONV#{conversation_id}#MSG#{assistant_message_id}',
        conversation_id=conversation_id,
        message_id=assistant_message_id,
        timestamp=generate_timestamp(),
        role='assistant',
        content=answer,
        response={
            'content': answer,
            'citations': citations,
            'confidence': confidence
        }
    )
    
    try:
        # Batch write both messages
        with table.batch_writer() as batch:
            batch.put_item(Item=user_message.to_dict())
            batch.put_item(Item=assistant_message.to_dict())
        
        logger.info(f"Stored conversation messages for conversation {conversation_id}")
        
    except Exception as e:
        logger.error(f"Error storing conversation: {e}")
        # Don't fail the request if storage fails


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Answer financial question.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.request_id
    
    try:
        logger.info(f"Processing assistant query: {request_id}")
        
        # Extract and validate token
        user_id = authorize_and_extract_user(event)
        
        # Log assistant query access
        log_write_access(user_id, 'query', 'financial_assistant', 'question')
        
        # Parse request
        body = json.loads(event.get('body', '{}'))
        question = body.get('question', '').strip()
        conversation_id = body.get('conversation_id', generate_id('conv'))
        
        if not question:
            raise ValidationError("Question is required")
        
        logger.info(f"Question: {question}")
        
        # Query relevant transaction data
        transactions = query_relevant_transactions(user_id, question)
        
        # Check for insufficient data
        insufficient_data_msg = check_insufficient_data(transactions, question)
        if insufficient_data_msg:
            response_data = {
                'answer': insufficient_data_msg,
                'citations': [],
                'confidence': 1.0,
                'conversation_id': conversation_id
            }
            
            # Store conversation
            store_conversation_message(
                user_id, conversation_id, question,
                insufficient_data_msg, [], 1.0
            )
            
            # Log to audit trail
            log_assistant_query_audit(
                user_id=user_id,
                question=question,
                answer=insufficient_data_msg,
                confidence=1.0,
                citations=[]
            )
            
            return success_response(response_data)
        
        # Get conversation history
        conversation_history = get_conversation_history(user_id, conversation_id)
        
        # Build prompt components
        transaction_summary = build_transaction_summary(transactions)
        conversation_context = build_conversation_context(conversation_history)
        prompt = build_prompt(question, transaction_summary, conversation_context)
        
        # Call Bedrock
        bedrock_response = call_bedrock(prompt)
        
        # Extract answer from response
        content_blocks = bedrock_response.get('content', [])
        answer = ''
        for block in content_blocks:
            if block.get('type') == 'text':
                answer = block.get('text', '')
                break
        
        if not answer:
            raise AppError("No response generated from Bedrock")
        
        # Extract citations
        citations = extract_citations(answer)
        
        # Calculate confidence (simplified - based on presence of citations)
        confidence = 0.9 if citations else 0.7
        
        response_data = {
            'answer': answer,
            'citations': citations,
            'confidence': confidence,
            'conversation_id': conversation_id
        }
        
        # Store conversation
        store_conversation_message(
            user_id, conversation_id, question,
            answer, citations, confidence
        )
        
        # Log to audit trail
        log_assistant_query_audit(
            user_id=user_id,
            question=question,
            answer=answer,
            confidence=confidence,
            citations=citations
        )
        
        logger.info(f"Successfully processed assistant query with {len(citations)} citations")
        return success_response(response_data)
        
    except AppError as e:
        logger.error(f"Assistant error: {e.message}")
        return error_response(e, request_id)
    except Exception as e:
        logger.exception("Unhandled exception")
        error = AppError("Internal server error")
        return error_response(error, request_id)
