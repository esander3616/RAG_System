import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from openai import OpenAI
from tokenomics import log_usage
load_dotenv()

MODEL = "gemini-3.5-flash-lite"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "policies"
TOP_K = 3

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
_collection = _chroma_client.get_collection(
    name=COLLECTION_NAME, embedding_function=_embedding_fn
)

ANSWER_SYSTEM_PROMPT = """You are a helpful assistant answering questions
about company policy using ONLY the provided context. If the context does
not contain the answer, say so honestly rather than making something up.
Reference which document your answer is based on."""

def retrieve(question: str, top_k: int = TOP_K) -> list[tuple[str, str]]:
    """Returns a list of (chunk_text, source_filename) tuples."""
    results = _collection.query(query_texts=[question], n_results=top_k)
    chunks = results["documents"][0]
    sources = [m["source"] for m in results["metadatas"][0]]
    return list(zip(chunks, sources))

def answer_question(question: str) -> dict:
    retrieved = retrieve(question)
    context = "\n\n".join(f"[Source: {src}]\n{chunk}" for chunk, src in retrieved)

    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    log_usage("QualitativeAgent", completion.usage.prompt_tokens, completion.usage.completion_tokens)

    return {
        "question": question,
        "answer": completion.choices[0].message.content.strip(),
        "sources": sorted(set(src for _, src in retrieved)),
    }

if __name__ == "__main__":
    for q in [
        "What is our company's security policy on passwords?",
        "How long should code reviews take?",
        "What's our policy on expense approvals?",
        "How do we handle customer complaints?",
    ]:
        result = answer_question(q)
        print(f"\nQ: {result['question']}")
        print(f"A: {result['answer']}")
        print(f"Sources: {result['sources']}")