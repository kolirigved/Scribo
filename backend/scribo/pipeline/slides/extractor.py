import pypdf

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF file page by page.
    
    Args:
        pdf_path: Path to the PDF slide deck.
        
    Returns:
        A string containing all text, with [Slide: Page X] breadcrumbs.
    """
    text_chunks = []
    
    with open(pdf_path, 'rb') as file:
        reader = pypdf.PdfReader(file)
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                page_text = page_text.strip()
                # Append a breadcrumb for chunking and search citations
                text_chunks.append(f"[Slide: Page {i+1}]\n{page_text}")
                
    return "\n\n".join(text_chunks)
