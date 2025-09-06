"""
Conversation Management System

This module handles conversation context, memory, and session management
for Steve's Mom AI agent.
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """A single message in a conversation."""

    id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class ConversationContext:
    """Context information for a conversation."""

    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    messages: List[ConversationMessage]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            messages=[ConversationMessage.from_dict(msg) for msg in data["messages"]],
            metadata=data["metadata"],
        )


class ConversationManager:
    """Manages conversation contexts and memory."""

    def __init__(self, storage_path: Optional[Path] = None, max_context_length: int = 20):
        self.storage_path = storage_path or Path("data/conversations")
        self.max_context_length = max_context_length
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.session_timeout = timedelta(hours=24)  # 24 hour session timeout

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Load active conversations
        self._load_active_conversations()

    def _load_active_conversations(self):
        """Load active conversations from storage."""
        try:
            for session_file in self.storage_path.glob("*.json"):
                try:
                    with open(session_file, "r") as f:
                        data = json.load(f)

                    context = ConversationContext.from_dict(data)

                    # Check if session is still active (not expired)
                    if datetime.now() - context.last_activity < self.session_timeout:
                        self.active_conversations[context.session_id] = context
                    else:
                        # Archive expired session
                        self._archive_conversation(context.session_id)

                except Exception as e:
                    logger.warning(f"Failed to load conversation from {session_file}: {e}")

        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")

    def _save_conversation(self, session_id: str):
        """Save conversation to storage."""
        if session_id not in self.active_conversations:
            return

        try:
            context = self.active_conversations[session_id]
            session_file = self.storage_path / f"{session_id}.json"

            with open(session_file, "w") as f:
                json.dump(context.to_dict(), f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save conversation {session_id}: {e}")

    def _archive_conversation(self, session_id: str):
        """Archive an expired conversation."""
        try:
            session_file = self.storage_path / f"{session_id}.json"
            if session_file.exists():
                archive_dir = self.storage_path / "archived"
                archive_dir.mkdir(exist_ok=True)

                archive_file = (
                    archive_dir / f"{session_id}_{datetime.now().strftime('%Y%m%d')}.json"
                )
                session_file.rename(archive_file)

        except Exception as e:
            logger.warning(f"Failed to archive conversation {session_id}: {e}")

    async def get_or_create_conversation(
        self, session_id: str, user_id: str
    ) -> ConversationContext:
        """Get existing conversation or create a new one."""
        # Check if conversation exists and is active
        if session_id in self.active_conversations:
            context = self.active_conversations[session_id]

            # Check if session has expired
            if datetime.now() - context.last_activity > self.session_timeout:
                # Archive expired session and create new one
                await self._archive_conversation_async(session_id)
                del self.active_conversations[session_id]
            else:
                # Update last activity
                context.last_activity = datetime.now()
                return context

        # Create new conversation
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            messages=[],
            metadata={},
        )

        self.active_conversations[session_id] = context
        return context

    async def add_message(
        self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Add a message to the conversation."""
        if session_id not in self.active_conversations:
            raise ValueError(f"Conversation {session_id} not found")

        context = self.active_conversations[session_id]

        message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        context.messages.append(message)
        context.last_activity = datetime.now()

        # Trim context if too long
        if len(context.messages) > self.max_context_length:
            # Keep system messages and recent messages
            system_messages = [msg for msg in context.messages if msg.role == "system"]
            recent_messages = [msg for msg in context.messages if msg.role != "system"][
                -self.max_context_length:
            ]
            context.messages = system_messages + recent_messages

        # Save conversation
        self._save_conversation(session_id)

        return message

    async def get_conversation_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """Get conversation history."""
        if session_id not in self.active_conversations:
            return []

        context = self.active_conversations[session_id]
        messages = context.messages

        if limit:
            messages = messages[-limit:]

        return messages

    async def get_context_for_ai(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation context formatted for AI model."""
        messages = await self.get_conversation_history(session_id)

        # Convert to AI model format
        ai_messages = []
        for msg in messages:
            ai_messages.append({"role": msg.role, "content": msg.content})

        return ai_messages

    async def update_conversation_metadata(self, session_id: str, metadata: Dict[str, Any]):
        """Update conversation metadata."""
        if session_id in self.active_conversations:
            context = self.active_conversations[session_id]
            context.metadata.update(metadata)
            context.last_activity = datetime.now()
            self._save_conversation(session_id)

    async def end_conversation(self, session_id: str):
        """End and archive a conversation."""
        if session_id in self.active_conversations:
            await self._archive_conversation_async(session_id)
            del self.active_conversations[session_id]

    async def _archive_conversation_async(self, session_id: str):
        """Async version of archive conversation."""
        await asyncio.get_event_loop().run_in_executor(None, self._archive_conversation, session_id)

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.active_conversations.keys())

    def get_conversation_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation statistics."""
        if session_id not in self.active_conversations:
            return None

        context = self.active_conversations[session_id]

        return {
            "session_id": session_id,
            "user_id": context.user_id,
            "created_at": context.created_at.isoformat(),
            "last_activity": context.last_activity.isoformat(),
            "message_count": len(context.messages),
            "duration_minutes": (context.last_activity - context.created_at).total_seconds() / 60,
            "metadata": context.metadata,
        }


# Global conversation manager instance
conversation_manager = ConversationManager()
