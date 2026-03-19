"""
Run this script once to load all Webster documents into the vector store.
Place all your PDF, DOCX, and TXT files in the 'data' folder first.
"""
from document_processor import load_documents, chunk_documents
from vector_store import VectorStore
import os

def setup():
    print("=" * 50)
    print("Webster AI - Document Setup")
    print("=" * 50)
    
    # Check data folder
    if not os.path.exists("data"):
        os.makedirs("data")
        print("\n✅ Created 'data' folder")
        print("📁 Please add your Webster documents to the 'data' folder:")
        print("   - webster-student-handbook.pdf")
        print("   - COURSE_CATALOGS.docx")
        print("   - Any other Webster PDFs or DOCX files")
        print("\nThen run this script again!")
        return
    
    # Check if data folder has files
    files = [f for f in os.listdir("data") if f.endswith(('.pdf', '.docx', '.txt'))]
    
    if not files:
        print("\n⚠️  No documents found in 'data' folder!")
        print("📁 Please add your Webster documents:")
        print("   - webster-student-handbook.pdf")
        print("   - COURSE_CATALOGS.docx")
        print("   - Any other Webster PDFs or DOCX files")
        return
    
    print(f"\n📄 Found {len(files)} document(s): {', '.join(files)}")
    
    # Load documents
    print("\n📖 Loading documents...")
    documents = load_documents("data")
    
    if not documents:
        print("❌ No documents could be loaded!")
        return
    
    # Chunk documents
    print("\n✂️  Chunking documents...")
    chunks = chunk_documents(documents, chunk_size=300, overlap=30)
    
    # Create vector store
    print("\n🔍 Creating vector store...")
    store = VectorStore("data/vector_store.json")
    store.add_chunks(chunks)
    
    print("\n✅ Setup complete!")
    print(f"   Documents loaded: {len(documents)}")
    print(f"   Chunks created: {len(chunks)}")
    print("\n🚀 Now run: python3 app.py")

if __name__ == "__main__":
    setup()
