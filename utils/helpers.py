"""
Helper functions for medical agent nodes
"""

from typing import Dict, List, Tuple, Any, Optional
import logging
from utils.llm import call_llm
from utils.parsing.response_parser import parse_yaml_response, validate_yaml_structure
from utils.role_enum import RoleEnum

# Configure logging with Vietnam timezone
from utils.timezone_utils import setup_vietnam_logging
from config.logging_config import logging_config

if logging_config.USE_VIETNAM_TIMEZONE:
    logger = setup_vietnam_logging(__name__, 
                                 level=getattr(logging, logging_config.LOG_LEVEL.upper()),
                                 format_str=logging_config.LOG_FORMAT)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, logging_config.LOG_LEVEL.upper()))


def get_score_threshold() -> float:
    """Get retrieval score threshold for decision making"""
    return 0.1


def serialize_conversation_history(messages):
    """
    Serialize SQLAlchemy message objects to plain Python dicts
    
    Args:
        messages: SQLAlchemy relationship collection of ChatMessage objects
        
    Returns:
        list: List of serialized message dictionaries
    """
    conversation_history = []
    for msg in messages:
        conversation_history.append({
            "role": msg.role,
            "content": msg.content,
            "api_role": msg.api_role,
            "input_type": msg.input_type
        })
    return conversation_history

def format_conversation_history(conversation_history):
    """Format conversation history from list of dicts to readable text"""
    if not conversation_history:
        return "Không có cuộc hội thoại trước đó"
    
    formatted_messages = []
    for msg in conversation_history:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        if role == 'user':
            formatted_messages.append(f"Người dùng: {content}")
        elif role == 'bot':
            formatted_messages.append(f"Bot: {content}")
        else:
            formatted_messages.append(f"{role}: {content}")
    
    return "\n".join(formatted_messages)
