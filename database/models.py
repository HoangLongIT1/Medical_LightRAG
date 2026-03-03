"""
Database models for the chat application
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    
    # Relationship
    threads = relationship("ChatThread", back_populates="user", cascade="all, delete-orphan")
    
class ChatThread(Base):
    __tablename__ = "chat_threads"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("Users", back_populates="threads")
    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan")
    
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True)
    thread_id = Column(String(36), ForeignKey("chat_threads.id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)  # 'user' or 'bot'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    api_role = Column(String(50), nullable=True)
    suggestions = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    need_clarify = Column(Boolean, nullable=True)
    input_type = Column(String(50), nullable=True)
    
    # Relationship
    thread = relationship("ChatThread", back_populates="messages")


class ClinicalState(Base):
    """Tracks patient clinical state across a conversation thread.
    
    Stores extracted symptoms, patient profile, and symptom change diffs.
    Updated by ClinicalStateManager node after each user message.
    """
    __tablename__ = "clinical_states"
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(String(36), ForeignKey("chat_threads.id", ondelete="CASCADE"), unique=True)
    symptoms = Column(JSON, default=list)           # Current symptom list
    previous_symptoms = Column(JSON, default=list)   # Symptoms from previous turn
    profile = Column(JSON, default=dict)             # {age, gender, history}
    current_condition = Column(Text, default="")     # Summary of current condition
    symptom_changes = Column(JSON, default=dict)     # {added: [], removed: [], unchanged: []}
    intent = Column(String(50), default="UNKNOWN")   # MEDICAL, CHITCHAT, etc.
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    thread = relationship("ChatThread", backref="clinical_state")
