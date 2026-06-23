import fitz
from pathlib import Path

def extract_pdf(pdf_path:str):
    """
    Extracts text from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file."""
    
    docs = fitz.open(pdf_path)
    pages=[]
    for page_num in range(len(docs)):
        text = docs[page_num].get_text()
        if text.strip():
            pages.append({
                "source": Path(pdf_path).name,
                "page": page_num + 1,
                "text": text
            })

    docs.close()
    return pages

def load_pdf_folder(folder_path:str):
    """
    Extract text from all PDFs in a folder.
    """
    all_pages = []

    pdf_files = Path(folder_path).glob("*.pdf")
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}")
        pages = extract_pdf(str(pdf_file))
        all_pages.extend(pages)

    return all_pages