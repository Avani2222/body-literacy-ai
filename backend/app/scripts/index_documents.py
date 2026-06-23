from app.rag.ingest import load_pdf_folder
from app.rag.chunker import chunk_documents
from app.rag.embed import embed_chunks

from app.rag.qdrant_client import (
    create_collection,
    upload_chunks
)

PDF_FOLDER = "app/data/research_papers"

def main():
    print("Loading PDFs...")
    documents = load_pdf_folder(
        PDF_FOLDER
    )
    print(
        f"Loaded {len(documents)} pages"
    )

    print("Chunking...")
    chunks = chunk_documents(
        documents
    )
    print(
        f"Created {len(chunks)} chunks"
    )
    print("Generating embeddings...")
    embedded_chunks = embed_chunks(
        chunks
    )
    print(
        f"Generated {len(embedded_chunks)} embeddings"
    )

    print("Creating collection...")
    create_collection()
    print("Uploading to Qdrant...")
    upload_chunks(
        embedded_chunks
    )
    print("Done!")

if __name__ == "__main__":
    main()