import json, os, random, time
import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.8-flash"]

index = faiss.read_index("data/index.faiss")
with open("data/chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)


def search(query: str, k: int = 3) -> list[dict]:
    emb = client.models.embed_content(model="gemini-embedding-001", contents=query)
    vec = np.array([emb.embeddings[0].values]).astype("float32")
    distances, indices = index.search(vec, k)
    return [{"chunk": chunks[i], "distance": float(d)} for i, d in zip(indices[0], distances[0])]


def build_prompt(query: str, retrieved: list[dict]) -> str:
    context = "\n\n---\n\n".join(
        f"[Page {r['chunk']['page_number']}]\n{r['chunk']['text']}" for r in retrieved
    )
    return f"""You are a helpful assistant answering questions about a document.
Use ONLY the excerpts below to answer the question. Each excerpt is labeled with its page number.
If the answer is not contained in these excerpts, say "I couldn't find this in the document" - do not use outside knowledge.
When you answer, cite the page number(s) your answer comes from, like (Page 4).

Excerpts:
{context}

Question: {query}

Answer:"""


def generate(prompt: str, retries_per_model: int = 3) -> str:
    last_err = None
    for model in MODELS:
        for attempt in range(retries_per_model):
            try:
                return client.models.generate_content(model=model, contents=prompt).text
            except errors.APIError as e:
                last_err = e
                if e.code not in (429, 500, 503):
                    raise
                time.sleep(2 ** attempt * 2 + random.random())
    raise last_err


def condense_question(query: str, history: list[dict]) -> str:
    if not history:
        return query
    convo = "\n".join(f"{m['role'].title()}: {m['content']}" for m in history[-6:])
    prompt = f"""Given the conversation and a follow-up question, rewrite the follow-up
as a single standalone question that makes sense without the conversation.
Return ONLY the rewritten question.

Conversation:
{convo}

Follow-up: {query}

Standalone question:"""
    return generate(prompt).strip()


def ask(query: str, history: list[dict], k: int = 3) -> dict:
    standalone = condense_question(query, history)
    retrieved = search(standalone, k=k)
    answer = generate(build_prompt(standalone, retrieved))
    return {
        "answer": answer,
        "standalone_question": standalone,
        "pages": sorted({r["chunk"]["page_number"] for r in retrieved}),
    }
