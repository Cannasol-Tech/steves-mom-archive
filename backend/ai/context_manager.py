"""
Context Manager for Steve's Mom AI Chatbot

This module manages conversation context, memory windows, and session state
for maintaining coherent multi-turn conversations.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, UTC
import hashlib

from .providers.base import Message, MessageRole

logger = logging.getLogger(__name__)


@dataclass
class ConversationSession:
    """Represents a conversation session."""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    messages: List[Message]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}


@dataclass
class ContextWindow:
    """Represents a context window for AI processing."""
    messages: List[Message]
    total_tokens: int
    max_tokens: int
    truncated: bool = False
    summary: Optional[str] = None


class ContextManager:
    """
    Manages conversation context and memory for AI interactions.
    
    Features:
    - Session management with automatic cleanup
    - Token-aware context windows
    - Message summarization for long conversations
    - Context injection and retrieval
    - Memory persistence (in-memory for MVP, can be extended to Redis/SQL)
    """
    
    def __init__(
        self,
        max_context_tokens: int = 8192,
        max_session_age_hours: int = 24,
        max_sessions_per_user: int = 10,
        summarization_threshold: int = 4096
    ):
        """
        Initialize the context manager.
        
        Args:
            max_context_tokens: Maximum tokens in context window
            max_session_age_hours: Maximum age of sessions before cleanup
            max_sessions_per_user: Maximum sessions per user
            summarization_threshold: Token count to trigger summarization
        """
        self.max_context_tokens = max_context_tokens
        self.max_session_age_hours = max_session_age_hours
        self.max_sessions_per_user = max_sessions_per_user
        self.summarization_threshold = summarization_threshold
        
        # In-memory storage (replace with Redis/SQL for production)
        self.sessions: Dict[str, ConversationSession] = {}
        self.user_sessions: Dict[str, List[str]] = {}
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the session cleanup background task."""
        async def cleanup_loop():
            while True:
                try:
                    await self.cleanup_expired_sessions()
                    await asyncio.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
                    await asyncio.sleep(300)  # Retry in 5 minutes
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: User identifier
            session_id: Optional session ID (generated if not provided)
            metadata: Optional session metadata
            
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = self._generate_session_id(user_id)
        
        now = datetime.now(UTC)
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            messages=[],
            metadata=metadata or {}
        )
        
        self.sessions[session_id] = session
        
        # Track user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        
        self.user_sessions[user_id].append(session_id)
        
        # Enforce session limits per user
        await self._enforce_session_limits(user_id)
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id
    
    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to a session.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system, tool)
            content: Message content
            metadata: Optional message metadata
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        message = Message(
            role=role,
            content=content,
            metadata=metadata
        )
        
        session.messages.append(message)
        session.last_activity = datetime.now(UTC)
        
        # Check if summarization is needed
        await self._check_summarization_needed(session_id)
        
        logger.debug(f"Added {role.value} message to session {session_id}")
    
    async def get_context_window(
        self,
        session_id: str,
        max_tokens: Optional[int] = None
    ) -> ContextWindow:
        """
        Get context window for a session.
        
        Args:
            session_id: Session identifier
            max_tokens: Override default max tokens
            
        Returns:
            ContextWindow with messages and metadata
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        max_tokens = max_tokens or self.max_context_tokens
        
        # Start with all messages
        messages = session.messages.copy()
        total_tokens = self._estimate_tokens(messages)
        
        # If within limits, return as-is
        if total_tokens <= max_tokens:
            return ContextWindow(
                messages=messages,
                total_tokens=total_tokens,
                max_tokens=max_tokens,
                truncated=False
            )
        
        # Need to truncate - keep recent messages and system messages
        truncated_messages = []
        current_tokens = 0
        
        # Always include system messages
        system_messages = [msg for msg in messages if msg.role == MessageRole.SYSTEM]
        for msg in system_messages:
            msg_tokens = self._estimate_tokens([msg])
            if current_tokens + msg_tokens <= max_tokens:
                truncated_messages.append(msg)
                current_tokens += msg_tokens
        
        # Add recent messages in reverse order
        non_system_messages = [msg for msg in messages if msg.role != MessageRole.SYSTEM]
        for msg in reversed(non_system_messages):
            msg_tokens = self._estimate_tokens([msg])
            if current_tokens + msg_tokens <= max_tokens:
                truncated_messages.insert(len(system_messages), msg)
                current_tokens += msg_tokens
            else:
                break
        
        return ContextWindow(
            messages=truncated_messages,
            total_tokens=current_tokens,
            max_tokens=max_tokens,
            truncated=True,
            summary=session.metadata.get("conversation_summary")
        )
    
    async def get_session_messages(self, session_id: str) -> List[Message]:
        """Get all messages for a session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        return self.sessions[session_id].messages.copy()
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user."""
        return self.user_sessions.get(user_id, []).copy()
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        user_id = session.user_id
        
        # Remove from sessions
        del self.sessions[session_id]
        
        # Remove from user sessions
        if user_id in self.user_sessions:
            self.user_sessions[user_id] = [
                sid for sid in self.user_sessions[user_id] if sid != session_id
            ]
            
            # Clean up empty user session lists
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        logger.info(f"Deleted session {session_id}")
        return True
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=self.max_session_age_hours)
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.last_activity < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": len(session.messages),
            "estimated_tokens": self._estimate_tokens(session.messages),
            "metadata": session.metadata
        }
    
    def _generate_session_id(self, user_id: str) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now(UTC).isoformat()
        data = f"{user_id}:{timestamp}:{id(self)}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def _estimate_tokens(self, messages: List[Message]) -> int:
        """Estimate token count for messages."""
        total_chars = 0
        for message in messages:
            total_chars += len(message.content)
            total_chars += len(message.role.value)
            if message.metadata:
                total_chars += len(str(message.metadata))
        
        # Rough approximation: 1 token ≈ 4 characters
        return total_chars // 4
    
    async def _check_summarization_needed(self, session_id: str) -> None:
        """Check if conversation summarization is needed."""
        session = self.sessions[session_id]
        total_tokens = self._estimate_tokens(session.messages)
        
        # Summarize if we exceed threshold, have enough messages, and haven't summarized recently
        if (total_tokens > self.summarization_threshold and 
            len(session.messages) > 10 and
            len(session.messages) % 10 == 0):  # Only summarize at intervals
            await self._summarize_conversation(session_id)
    
    async def _summarize_conversation(self, session_id: str) -> None:
        """Summarize conversation to reduce context size."""
        # This is a placeholder for conversation summarization
        # In a full implementation, this would use the AI model to create summaries
        session = self.sessions[session_id]
        
        # Simple summarization: keep recent messages, summarize older ones
        if len(session.messages) > 10:
            # Keep last 10 messages
            recent_messages = session.messages[-10:]
            
            # Create simple summary of older messages
            older_messages = session.messages[:-10]
            summary_parts = []
            
            for msg in older_messages:
                if msg.role == MessageRole.USER:
                    summary_parts.append(f"User asked about: {msg.content[:100]}...")
                elif msg.role == MessageRole.ASSISTANT:
                    summary_parts.append(f"Assistant responded about: {msg.content[:100]}...")
            
            summary = "Previous conversation summary:\n" + "\n".join(summary_parts[-5:])
            
            # Update session
            session.messages = recent_messages
            session.metadata["conversation_summary"] = summary
            session.metadata["summarized_at"] = datetime.now(UTC).isoformat()
            
            logger.info(f"Summarized conversation for session {session_id}")
    
    async def _enforce_session_limits(self, user_id: str) -> None:
        """Enforce maximum sessions per user."""
        user_session_ids = self.user_sessions.get(user_id, [])
        
        if len(user_session_ids) > self.max_sessions_per_user:
            # Remove oldest sessions
            sessions_to_remove = len(user_session_ids) - self.max_sessions_per_user
            
            # Sort by last activity (oldest first)
            session_ages = []
            for session_id in user_session_ids:
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    session_ages.append((session.last_activity, session_id))
            
            session_ages.sort()  # Oldest first
            
            for _, session_id in session_ages[:sessions_to_remove]:
                await self.delete_session(session_id)
            
            logger.info(f"Removed {sessions_to_remove} old sessions for user {user_id}")
    
    async def shutdown(self) -> None:
        """Shutdown the context manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Context manager shutdown complete")
