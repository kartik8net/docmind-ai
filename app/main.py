from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import rag
from app.db import Base, SessionLocal, engine
from app.models import Conversation
from app.repositories import ConversationRepository

Base.metadata.create_all(engine)
app = FastAPI(title="DocMind AI")


def get_repo():
    with SessionLocal() as session:
        yield ConversationRepository(session)


class ChatRequest(BaseModel):
    question: str


@app.post("/conversations")
def create_conversation(repo: ConversationRepository = Depends(get_repo)):
    conv = repo.create("New chat")
    return {"id": conv.id}


@app.post("/conversations/{conversation_id}/chat")
def chat(conversation_id: int, body: ChatRequest, repo: ConversationRepository = Depends(get_repo)):
    if repo.session.get(Conversation, conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    history = repo.get_history(conversation_id, limit=6)
    result = rag.ask(body.question, history)
    repo.add_message(conversation_id, "user", body.question)
    repo.add_message(conversation_id, "assistant", result["answer"])
    return result
