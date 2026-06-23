import os
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()


EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str):
    """
    Generate embedding for a single text chunk
    """
    return EMBEDDING_MODEL.encode(text).tolist()

def embed_chunks(chunks):
    """
    Generate embeddings for a list of text chunks
    """
    embeddings_chunks = []
    for chunk in chunks:
        print(".")
        embedding = get_embedding(chunk["text"])
        embeddings_chunks.append({
            "text": chunk["text"],
            "embedding": embedding,
            "metadata": chunk["metadata"]
        })
    return embeddings_chunks