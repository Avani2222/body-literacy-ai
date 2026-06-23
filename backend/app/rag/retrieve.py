from app.rag.embed import get_embedding
from app.rag.qdrant_client import client, COLLECTION_NAME

top_k = 5  # Number of top results to retrieve

def retrieve(query: str, top_k: int = top_k):
    """
    Retrieve relevant chunks from Qdrant based on the query.

    Args:
        query (str): The input query string.
        top_k (int): Number of top results to retrieve.
    """

    query_embedding = get_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k
    )

    retreived_chunks = []
    for point in results.points:
        retreived_chunks.append({
            "text": point.payload["text"],
            "source": point.payload["source"],
            "page": point.payload["page"],
            "score":point.score,
            "chunk_index": point.payload["chunk_index"]
        })

    return retreived_chunks