import glob
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "runbooks"

model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(host="localhost", port=6333)

client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

points = []
point_id = 0

for filepath in glob.glob("data/runbooks/*.md"):
    with open(filepath, "r") as f:
        text = f.read()

    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]

    for chunk in chunks:
        embedding = model.encode(chunk).tolist()
        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={"text": chunk, "source": filepath},
            )
        )
        point_id += 1

client.upsert(collection_name=COLLECTION_NAME, points=points)
print(f"Ingested {len(points)} chunks from {len(glob.glob('data/runbooks/*.md'))} runbooks.")
