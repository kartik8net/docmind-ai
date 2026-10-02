from app.db import Base, SessionLocal, engine
import app.models  # registers the tables with Base
from app.repositories import ConversationRepository

Base.metadata.create_all(engine)

with SessionLocal() as session:
    repo = ConversationRepository(session)
    conv = repo.create("Attention paper")
    repo.add_message(conv.id, "user", "What is multi-head attention?")
    repo.add_message(conv.id, "assistant", "It runs several attention layers in parallel (Page 4).")
    repo.add_message(conv.id, "user", "How many of them does the base model use?")
    print("conversation id:", conv.id)
    print(repo.get_history(conv.id))
