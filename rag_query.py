import sys
import requests
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "runbooks"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "sre-copilot"

model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(host="localhost", port=6333)

question = sys.argv[1] if len(sys.argv) > 1 else "why is my pod crashlooping?"
query_vector = model.encode(question).tolist()

results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=query_vector,
    limit=3,
).points

context = "\n\n".join(r.payload["text"] for r in results)

prompt = f"""You are an SRE assistant. Use ONLY the context below to answer the question.
If the context doesn't contain the answer, say so.

Context:
{context}

Question: {question}

Answer:"""

response = requests.post(
    OLLAMA_URL,
    json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
)

print(response.json()["response"])
