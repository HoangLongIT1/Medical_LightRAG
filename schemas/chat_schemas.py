"""
Pydantic schemas for chat API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MessageSchema(BaseModel):
    """Unified message schema for API responses"""
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user/bot)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    api_role: Optional[str] = Field(None, description="API role used for user messages")
    suggestions: Optional[List[str]] = Field(None, description="Bot message suggestions")
    need_clarify: Optional[bool] = Field(None, description="Whether response needs clarification")
    input_type: Optional[str] = Field(None, description="Classified input type")
    summary: Optional[str] = Field(None, description="Message summary")


class ThreadSchema(BaseModel):
    """Thread schema for API responses"""
    id: str = Field(..., description="Thread identifier")
    name: str = Field(..., description="Thread name")
    created_at: str = Field(..., description="Thread creation timestamp")
    updated_at: str = Field(..., description="Thread last update timestamp")


class ThreadWithMessagesSchema(ThreadSchema):
    """Thread with messages for detailed responses"""
    messages: List[MessageSchema] = Field(..., description="List of messages")
    total_messages: int = Field(..., description="Total number of messages")
    user_id: int = Field(..., description="User ID")


# Request schemas
class CreateThreadRequest(BaseModel):
    """Request schema for creating a new thread"""
    name: str = Field(..., min_length=1, max_length=255, description="Thread name")


class RenameThreadRequest(BaseModel):
    """Request schema for renaming a thread"""
    name: str = Field(..., min_length=1, max_length=255, description="New thread name")


class SendMessageRequest(BaseModel):
    """Request schema for sending a message"""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    role: Optional[str] = Field(None, description="Message role")


# Response schemas
class ThreadListResponse(BaseModel):
    """Response schema for thread list"""
    threads: List[ThreadSchema] = Field(..., description="List of threads")
    total: int = Field(..., description="Total number of threads")


class ThreadMessagesResponse(BaseModel):
    """Response schema for thread messages with pagination"""
    thread_id: str = Field(..., description="Thread identifier")
    thread_name: str = Field(..., description="Thread name")
    messages: List[MessageSchema] = Field(..., description="List of messages in chronological order")
    total_messages: int = Field(..., description="Total number of messages")
    user_id: int = Field(..., description="User ID")
    created_at: str = Field(..., description="Thread creation timestamp")
    updated_at: str = Field(..., description="Thread last update timestamp")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Messages per page")
    has_next: bool = Field(..., description="Whether there are more messages")
