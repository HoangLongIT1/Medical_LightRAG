"""
Business logic for chat operations
"""

import uuid
from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from database.models import Users, ChatThread, ChatMessage
from schemas.chat_schemas import (
    MessageSchema, 
    ThreadSchema, 
    ThreadWithMessagesSchema,
    ThreadMessagesResponse
)


class ChatService:
    """Service class for chat-related business logic"""
    
    # Configuration constants
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200
    MIN_PAGE_SIZE = 1
    WELCOME_MESSAGE = "Xin chào! Tôi là trợ lý AI của bạn. Rất vui được hỗ trợ bạn - Bạn cần tôi giúp gì hôm nay?"
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_threads(self, user_id: int) -> List[ThreadSchema]:
        """Get all threads for a user"""
        threads = self.db.query(ChatThread).filter(
            ChatThread.user_id == user_id
        ).order_by(
            ChatThread.updated_at.desc()
        ).all()
        
        return [
            ThreadSchema(
                id=thread.id,
                name=thread.name,
                created_at=thread.created_at.isoformat(),
                updated_at=thread.updated_at.isoformat()
            ) for thread in threads
        ]
    
    def create_thread(self, user_id: int, name: str) -> ThreadSchema:
        """Create a new thread with welcome message"""
        thread_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Create thread
        new_thread = ChatThread(
            id=thread_id,
            user_id=user_id,
            name=name,
            created_at=now,
            updated_at=now,
        )
        
        # Add welcome message
        welcome_message = ChatMessage(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            role="bot",
            content=self.WELCOME_MESSAGE,
            timestamp=now,
        )
        
        self.db.add(new_thread)
        self.db.add(welcome_message)
        self.db.commit()
        
        return ThreadSchema(
            id=new_thread.id,
            name=new_thread.name,
            created_at=new_thread.created_at.isoformat(),
            updated_at=new_thread.updated_at.isoformat()
        )
    
    def get_thread_with_messages(self, thread_id: str, user_id: int) -> ThreadWithMessagesSchema:
        """Get a specific thread with all messages"""
        thread = self._get_user_thread(thread_id, user_id)
        
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread_id
        ).order_by(
            ChatMessage.timestamp.asc()
        ).all()
        
        formatted_messages = [
            self._format_message(msg) for msg in messages
        ]
        
        return ThreadWithMessagesSchema(
            id=thread.id,
            name=thread.name,
            created_at=thread.created_at.isoformat(),
            updated_at=thread.updated_at.isoformat(),
            messages=formatted_messages,
            total_messages=len(formatted_messages),
            user_id=user_id
        )
    
    def get_thread_messages_paginated(
        self, 
        thread_id: str, 
        user_id: int, 
        page: int = 1, 
        limit: int = None
    ) -> ThreadMessagesResponse:
        """Get thread messages with pagination"""
        # Validate and normalize pagination parameters
        page, limit = self._validate_pagination(page, limit)
        
        # Verify thread ownership
        thread = self._get_user_thread(thread_id, user_id)
        
        # Calculate pagination
        offset = (page - 1) * limit
        
        # Get total count
        total_messages = self.db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread_id
        ).count()
        
        # Get paginated messages
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread_id
        ).order_by(
            ChatMessage.timestamp.asc()
        ).offset(offset).limit(limit).all()
        
        # Format messages
        formatted_messages = [
            self._format_message(msg) for msg in messages
        ]
        
        # Calculate if there are more messages
        has_next = (offset + limit) < total_messages
        
        return ThreadMessagesResponse(
            thread_id=thread.id,
            thread_name=thread.name,
            messages=formatted_messages,
            total_messages=total_messages,
            user_id=user_id,
            created_at=thread.created_at.isoformat(),
            updated_at=thread.updated_at.isoformat(),
            page=page,
            limit=limit,
            has_next=has_next
        )
    
    def rename_thread(self, thread_id: str, user_id: int, new_name: str) -> ThreadSchema:
        """Rename a thread"""
        thread = self._get_user_thread(thread_id, user_id)
        
        thread.name = new_name
        thread.updated_at = datetime.now()
        self.db.commit()
        
        return ThreadSchema(
            id=thread.id,
            name=thread.name,
            created_at=thread.created_at.isoformat(),
            updated_at=thread.updated_at.isoformat()
        )
    
    def delete_thread(self, thread_id: str, user_id: int) -> None:
        """Delete a thread"""
        thread = self._get_user_thread(thread_id, user_id)
        
        self.db.delete(thread)
        self.db.commit()
    
    def _get_user_thread(self, thread_id: str, user_id: int) -> ChatThread:
        """Get thread ensuring user ownership"""
        thread = self.db.query(ChatThread).filter(
            ChatThread.id == thread_id,
            ChatThread.user_id == user_id
        ).first()
        
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found or you don't have permission to access it"
            )
        
        return thread
    
    def _format_message(self, message: ChatMessage) -> MessageSchema:
        """Format a database message to schema"""
        return MessageSchema(
            id=message.id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp.isoformat(),
            api_role=message.api_role,
            suggestions=message.suggestions,
            need_clarify=message.need_clarify,
            input_type=message.input_type,
            summary=message.summary
        )
    
    def _validate_pagination(self, page: int, limit: Optional[int]) -> Tuple[int, int]:
        """Validate and normalize pagination parameters"""
        # Set default limit if not provided
        if limit is None:
            limit = self.DEFAULT_PAGE_SIZE
        
        # Validate and clamp limit
        if limit > self.MAX_PAGE_SIZE:
            limit = self.MAX_PAGE_SIZE
        elif limit < self.MIN_PAGE_SIZE:
            limit = self.MIN_PAGE_SIZE
        
        # Validate page
        if page < 1:
            page = 1
        
        return page, limit
