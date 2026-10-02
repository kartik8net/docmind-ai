from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Conversation, Message

class ConversationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, title: str = "New chat") -> Conversation:
        conv = Conversation(title=title)
        self.session.add(conv)
        self.session.commit()
        return conv

    def add_message(self, conversation_id: int, role: str, content: str) -> Message:
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        self.session.add(msg)
        self.session.commit()
        return msg

    def get_history(self, conversation_id: int, limit: int = 6) -> list[dict]:
        """Last `limit` messages, oldest first, in the same shape the notebook uses."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )
        rows = list(self.session.scalars(stmt))[::-1]
        return [{"role": m.role, "content": m.content} for m in rows]
