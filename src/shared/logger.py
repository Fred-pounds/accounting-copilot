"""
Logging utilities for Lambda functions.
"""

import logging
import json
from typing import Any, Dict


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with JSON formatting for CloudWatch.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level.upper()))
    
    # Use simple format for CloudWatch
    formatter = logging.Formatter(
        '%(levelname)s\t%(name)s\t%(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


def log_event(logger: logging.Logger, event_type: str, data: Dict[str, Any]) -> None:
    """
    Log a structured event.
    
    Args:
        logger: Logger instance
        event_type: Type of event
        data: Event data
    """
    log_data = {
        'event_type': event_type,
        **data
    }
    logger.info(json.dumps(log_data))


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None) -> None:
    """
    Log an error with context.
    
    Args:
        logger: Logger instance
        error: Exception
        context: Additional context
    """
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {}
    }
    logger.error(json.dumps(error_data))


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger
    """
    return setup_logger(name, level)
