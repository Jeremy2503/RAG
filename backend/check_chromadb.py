"""
Check what documents are stored in ChromaDB.
"""
import chromadb
from pathlib import Path

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./data/chroma")
print("[INFO] Connected to ChromaDB\n")

# Get collection
try:
    collection = client.get_collection("policy_documents")
    print(f"[OK] Found collection: policy_documents")
    
    # Get collection count
    count = collection.count()
    print(f"[INFO] Total documents in collection: {count}\n")
    
    if count == 0:
        print("[WARNING] Collection is EMPTY! No documents have been embedded yet.")
        print("\nPossible reasons:")
        print("1. Document processing failed")
        print("2. OCR extraction failed")
        print("3. Embedding generation failed")
        print("\nCheck backend logs for errors during upload.")
    else:
        # Get some sample documents
        results = collection.get(limit=5, include=["documents", "metadatas"])
        
        print("=" * 60)
        print("SAMPLE DOCUMENTS IN CHROMADB:")
        print("=" * 60)
        
        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
            print(f"\n[Document {i}]")
            print(f"  Document Type: {meta.get('document_type', 'N/A')}")
            print(f"  Document ID: {meta.get('document_id', 'N/A')}")
            print(f"  Title: {meta.get('title', 'N/A')}")
            print(f"  Chunk {meta.get('chunk_index', '?')} of {meta.get('total_chunks', '?')}")
            print(f"  Content Preview: {doc[:200]}...")
            
        # Check for hr_policy documents specifically
        print("\n" + "=" * 60)
        hr_results = collection.get(
            where={"document_type": "hr_policy"},
            limit=10,
            include=["documents", "metadatas"]
        )
        hr_count = len(hr_results['ids'])
        print(f"HR POLICY documents found: {hr_count}")
        
        if hr_count == 0:
            print("[WARNING] No documents with document_type='hr_policy' found!")
            print("\nDocuments by type:")
            all_docs = collection.get(include=["metadatas"])
            types = {}
            for meta in all_docs['metadatas']:
                doc_type = meta.get('document_type', 'unknown')
                types[doc_type] = types.get(doc_type, 0) + 1
            for doc_type, count in types.items():
                print(f"  - {doc_type}: {count} chunks")
        else:
            print(f"[OK] Found {hr_count} HR policy chunks")
            print(f"\nFirst HR policy chunk:")
            print(f"  Title: {hr_results['metadatas'][0].get('title', 'N/A')}")
            print(f"  Content: {hr_results['documents'][0][:300]}...")
        
        print("=" * 60)
        
except Exception as e:
    print(f"[ERROR] {e}")
    print("\nCollection might not exist yet. Upload a document first.")

