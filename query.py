import sys
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "runbooks"

model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(host="localhost", port=6333)

query = sys.argv[1] if len(sys.argv) > 1 else "pod keeps restarting"
query_vector = model.encode(query).tolist()

results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=query_vector,
    limit=3,
).points

for r in results:
    print(f"score={r.score:.3f}  source={r.payload['source']}")
    print(f"  {r.payload['text'][:120]}...")
    print()
