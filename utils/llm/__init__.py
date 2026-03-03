"""
LLM utilities - API calls and prompts
"""

from .call_llm import call_llm
from .prompts import (
    PROMPT_OQA_CLASSIFY_EN,
    PROMPT_OQA_COMPOSE_VI_WITH_SOURCES,
    PROMPT_OQA_CHITCHAT,
)

__all__ = [
    "call_llm",
    "PROMPT_OQA_CLASSIFY_EN",
    "PROMPT_OQA_COMPOSE_VI_WITH_SOURCES",
    "PROMPT_OQA_CHITCHAT",
]
