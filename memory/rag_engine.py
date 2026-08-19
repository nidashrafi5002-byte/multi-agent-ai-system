import os
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./memory/chroma_db")

# Embedding function
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Get or create collection
collection = chroma_client.get_or_create_collection(
    name="research_docs",
    embedding_function=embedding_fn
)

def add_pdf_to_db(pdf_file, filename: str) -> str:
    """Extract text from PDF and store in ChromaDB"""
    try:
        # Read PDF
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        if not text.strip():
            return "❌ Could not extract text from PDF"

        # Split into chunks
        chunk_size = 500
        chunks = []
        words = text.split()

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        # Store in ChromaDB
        collection.add(
            documents=chunks,
            ids=[f"{filename}_chunk_{i}" for i in range(len(chunks))],
            metadatas=[{"source": filename, "chunk": i} 
                      for i in range(len(chunks))]
        )

        return f"✅ Added {len(chunks)} chunks from {filename}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

def search_documents(query: str, n_results: int = 3) -> list:
    """Search relevant chunks from stored documents"""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )

        if results and results["documents"]:
            docs = []
            for i, doc in enumerate(results["documents"][0]):
                source = results["metadatas"][0][i]["source"]
                docs.append({
                    "content": doc,
                    "source": source
                })
            return docs
        return []

    except Exception as e:
        return []

def get_stored_documents() -> list:
    """Get list of all stored documents"""
    try:
        results = collection.get()
        sources = set()
        if results and results["metadatas"]:
            for meta in results["metadatas"]:
                sources.add(meta["source"])
        return list(sources)
    except:
        return []

def clear_documents() -> str:
    """Clear all documents from database"""
    try:
        global collection
        chroma_client.delete_collection("research_docs")
        collection = chroma_client.get_or_create_collection(
            name="research_docs",
            embedding_function=embedding_fn
        )
        return "✅ All documents cleared!"
    except Exception as e:
        return f"❌ Error: {str(e)}"