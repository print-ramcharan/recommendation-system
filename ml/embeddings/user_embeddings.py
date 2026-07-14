import numpy as np
from qdrant_client import QdrantClient
from ml.embeddings.qdrant_client import get_qdrant_client, COLLECTION_NAME
from ml.embeddings.generate_embeddings import model as embedding_model

def compute_user_embedding(clicked_article_ids: list[int], fallback_interests) -> list[float]:
    """
    Computes a dynamic user embedding vector.
    Averages past article interactions or falls back to interest metadata.
    """
    # Safeguard interests parsing (handles JSON column dicts or lists)
    if isinstance(fallback_interests, dict):
        topics = fallback_interests.get("preferred_topics", [])
        fallback_text = " ".join(topics) if isinstance(topics, list) else str(fallback_interests)
    elif isinstance(fallback_interests, list):
        fallback_text = " ".join(fallback_interests)
    else:
        fallback_text = str(fallback_interests)

    if not clicked_article_ids:
        # Cold start fallback: Encode baseline interests
        return embedding_model.encode(fallback_text).tolist()
    
    client = get_qdrant_client()
    try:
        # Batch retrieve the specific article vectors from Qdrant
        points = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=clicked_article_ids,
            with_vectors=True
        )
        
        vectors = [p.vector for p in points if p.vector is not None]
        
        if vectors:
            # Axis=0 collapses the rows into a unified mean semantic vector profile
            user_vector = np.mean(vectors, axis=0).tolist()
            return user_vector
            
    except Exception as e:
        print(f"Vector retrieval exception: {e}. Dropping to fallback profile.")
        
    # Warm fallback if vector database retrieval experiences a connection glitch
    return embedding_model.encode(fallback_text).tolist()