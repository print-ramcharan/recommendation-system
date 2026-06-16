import json
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "articles"


def get_qdrant_client() -> QdrantClient:
    """Initializes and returns a connection to the Qdrant engine."""
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def init_collection_and_upsert():
    client = get_qdrant_client()

    # 1. Ensure the 'articles' collection exists with a 384-dim Cosine configuration
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)

    if not exists:
        print(f"Creating collection '{COLLECTION_NAME}' (384 dimensions, Cosine distance)...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")

    # 2. Load the generated articles.json artifact
    json_path = os.path.join("data", "embeddings", "articles.json")
    if not os.path.exists(json_path):
        print(f"Error: Embedding file not found at {json_path}. Run generate_embeddings first!")
        return

    with open(json_path, "r") as f:
        embedding_data = json.load(f)

    print(f"Staging {len(embedding_data)} vectors for upsert...")

    # 3. Parse items into native Qdrant PointStruct elements
    points = []
    for item in embedding_data:
        points.append(
            PointStruct(
                id=item["article_id"], 
                vector=item["vector"],
                payload={"article_id": item["article_id"]}  
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"Successfully indexed! Total active vectors in collection: {collection_info.points_count}")


if __name__ == "__main__":
    init_collection_and_upsert()