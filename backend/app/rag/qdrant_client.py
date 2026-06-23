from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

COLLECTION_NAME = "body_literacy_docs"
BATCH_SIZE = 200
client = QdrantClient(
    host = "localhost",
    port = 6333
)

def create_collection():
    """
    Create a Qdrant collection for storing document embeddings.
    """
    collections = client.get_collections()
    existing = [
        c.name
        for c in collections.collections
    ]

    if COLLECTION_NAME in existing:
        info = client.get_collection("body_literacy_docs")
        print(info)
        print(f"Collection '{COLLECTION_NAME}' already exists.")
        client.delete_collection(
            collection_name="body_literacy_docs"
        )
    client.create_collection(
        collection_name = COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,  # Size of the embedding vector
            distance=Distance.COSINE  # Use cosine distance for similarity search   
        )
    )

    print(f"Collection '{COLLECTION_NAME}' created successfully.")

def upload_chunks(embedded_chunks):
    points = []
    for idx, chunk in enumerate(embedded_chunks):
        points.append(
            PointStruct(
                id=idx,
                vector=chunk["embedding"],
                payload={
                    "source": chunk["metadata"]["source"],
                    "page": chunk["metadata"]["page"],
                    "chunk_index": chunk["metadata"]["chunk_index"],
                    "text": chunk["text"]
                }
            )
        )
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i:i+BATCH_SIZE]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        print(
            f"Uploaded {i + len(batch)}/{len(points)}"
        )