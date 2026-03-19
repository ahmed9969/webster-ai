import os
from pathlib import Path

def load_documents(data_folder="data"):
    """Load all documents from the data folder"""
    documents = []
    data_path = Path(data_folder)
    
    if not data_path.exists():
        print(f"Data folder '{data_folder}' not found!")
        return documents
    
    for file_path in data_path.iterdir():
        if file_path.suffix == ".pdf":
            try:
                import fitz
                doc = fitz.open(str(file_path))
                text = ""
                for page in doc:
                    text += page.get_text()
                documents.append({
                    "source": file_path.name,
                    "content": text
                })
                print(f"Loaded PDF: {file_path.name}")
            except Exception as e:
                print(f"Error loading PDF {file_path.name}: {e}")
                
        elif file_path.suffix == ".docx":
            try:
                from docx import Document
                doc = Document(str(file_path))
                text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                documents.append({
                    "source": file_path.name,
                    "content": text
                })
                print(f"Loaded DOCX: {file_path.name}")
            except Exception as e:
                print(f"Error loading DOCX {file_path.name}: {e}")
                
        elif file_path.suffix == ".txt":
            try:
                text = file_path.read_text(encoding="utf-8")
                documents.append({
                    "source": file_path.name,
                    "content": text
                })
                print(f"Loaded TXT: {file_path.name}")
            except Exception as e:
                print(f"Error loading TXT {file_path.name}: {e}")
    
    print(f"\nTotal documents loaded: {len(documents)}")
    return documents

def chunk_documents(documents, chunk_size=500, overlap=50):
    """Split documents into smaller chunks for better search"""
    chunks = []
    
    for doc in documents:
        content = doc["content"]
        source = doc["source"]
        
        words = content.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text.strip()) > 50:
                chunks.append({
                    "source": source,
                    "content": chunk_text,
                    "chunk_id": len(chunks)
                })
    
    print(f"Total chunks created: {len(chunks)}")
    return chunks
