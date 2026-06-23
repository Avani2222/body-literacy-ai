from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

def chunk_documents(documents):
    """
    Split extracted documents into chunks while preserving metadata.

    Args:
        documents: List of dictionaries from ingest.py

    Returns:
        List of chunk dictionaries
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len
    )

    chunks = []

    for doc in documents:
        text = doc["text"]
        text_chunks = splitter.split_text(text)
        for idx, chunk in enumerate(text_chunks):
            chunks.append(
                {
                    "text": chunk,
                    "metadata":{
                        "source": doc["source"],
                        "page": doc["page"],
                        "chunk_index": idx
                    }
                }
            )
    return chunks