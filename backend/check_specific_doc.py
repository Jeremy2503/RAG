"""
Check the specific newly uploaded document.
"""
import chromadb

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./data/chroma")
collection = client.get_collection("policy_documents")

# Search for the specific document ID
document_id = "692eb5be3cfde3ee152be14d"

print(f"[INFO] Searching for document ID: {document_id}\n")

# Get all chunks for this document
results = collection.get(
    where={"document_id": document_id},
    limit=10,
    include=["documents", "metadatas"]
)

if len(results['ids']) == 0:
    print(f"[ERROR] No chunks found for document {document_id}")
    print("\nPossible reasons:")
    print("1. Document processing failed")
    print("2. Document ID mismatch")
    print("3. Chunks stored with different ID")
else:
    print(f"[OK] Found {len(results['ids'])} chunks for this document\n")
    print("=" * 60)
    print("DOCUMENT DETAILS:")
    print("=" * 60)
    
    first_meta = results['metadatas'][0]
    print(f"Document ID: {first_meta.get('document_id', 'N/A')}")
    print(f"Document Type: {first_meta.get('document_type', 'N/A')}")  # <-- KEY!
    print(f"Title: {first_meta.get('title', 'N/A')}")
    print(f"Total Chunks: {first_meta.get('total_chunks', 'N/A')}")
    print(f"Uploaded By: {first_meta.get('uploaded_by', 'N/A')}")
    print(f"Uploaded At: {first_meta.get('uploaded_at', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("FIRST CHUNK CONTENT:")
    print("=" * 60)
    print(results['documents'][0][:500])
    print("\n" + "=" * 60)

