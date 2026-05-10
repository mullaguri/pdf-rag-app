from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import ConversationHistory, User
from database import get_db
from datetime import datetime, timezone
import json


class HistoryService:
    """Service for managing user conversation history."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_conversation(
        self,
        user_id: int,
        question: str,
        answer: str,
        sources: List[str],
        session_id: Optional[str] = None
    ) -> ConversationHistory:
        """Add a new conversation entry to the history."""
        conversation = ConversationHistory(
            user_id=user_id,
            question=question,
            answer=answer,
            sources=json.dumps(sources) if sources else None,
            session_id=session_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by="system",
            updated_by="system"
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_conversation_history(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[ConversationHistory]:
        """Get conversation history for a user, optionally filtered by session."""
        query = self.db.query(ConversationHistory).filter(
            ConversationHistory.user_id == user_id
        )
        
        if session_id:
            query = query.filter(ConversationHistory.session_id == session_id)
        
        return query.order_by(desc(ConversationHistory.created_at)).limit(limit).all()
    
    def get_conversation_context(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        max_history: int = 5
    ) -> str:
        """Get formatted conversation history for context in RAG prompts."""
        history = self.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=max_history
        )
        
        if not history:
            return ""
        
        # Format history as conversation pairs (excluding the most recent as it's the current question)
        context_lines = ["Previous conversation:"]
        for conv in reversed(history[:-1]):  # Reverse to get chronological order, exclude most recent
            sources_info = ""
            if conv.sources:
                try:
                    sources_list = json.loads(conv.sources)
                    sources_info = f" (Sources: {', '.join(sources_list)})"
                except:
                    pass
            
            context_lines.append(f"Human: {conv.question}")
            context_lines.append(f"Assistant: {conv.answer}{sources_info}")
        
        return "\n".join(context_lines)
    
    def clear_user_history(self, user_id: int, session_id: Optional[str] = None) -> int:
        """Clear conversation history for a user, optionally by session."""
        query = self.db.query(ConversationHistory).filter(
            ConversationHistory.user_id == user_id
        )
        
        if session_id:
            query = query.filter(ConversationHistory.session_id == session_id)
        
        count = query.count()
        query.delete()
        self.db.commit()
        return count
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user object by username."""
        return self.db.query(User).filter(User.username == username).first()


def get_history_service(db: Session = None) -> HistoryService:
    """Get a HistoryService instance."""
    if db is None:
        db = next(get_db())
    return HistoryService(db)
