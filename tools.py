from mcp_tools import get_pod_status
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

embed_model = SentenceTransformer("all-MiniLM-L6-v2")
import os
qdrant = QdrantClient(host=os.getenv("QDRANT_HOST", "localhost"), port=6333)

def search_runbooks(query: str) -> str:
    """Search internal runbooks for guidance related to the query."""
    vector = embed_model.encode(query).tolist()
    results = qdrant.query_points(
        collection_name="runbooks",
        query=vector,
        limit=2,
    ).points
    return "\n\n".join(r.payload["text"] for r in results)

TOOLS = {
    "search_runbooks": search_runbooks,
    "get_pod_status": get_pod_status,
}
