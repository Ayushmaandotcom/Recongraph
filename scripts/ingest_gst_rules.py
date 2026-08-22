import os
import sys

# Ensure src is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from recongraph.learning.knowledge_base import build_default_knowledge_base
from recongraph.learning.qdrant_pipeline import RAGPipeline

def main():
    print("Building default knowledge base...")
    kb = build_default_knowledge_base()
    
    docs = kb.to_rag_documents()
    print(f"Generated {len(docs)} documents.")

    print("Initializing RAG pipeline...")
    pipeline = RAGPipeline()
    
    print("Ingesting documents into Qdrant...")
    pipeline.ingest(docs)
    print("Ingestion complete.")

    print("\nTesting search...")
    queries = [
        "What are the conditions for claiming ITC under Section 16(2)?",
        "How is ITC reversed when supplier does not pay tax?",
        "What is the time limit to claim ITC?"
    ]

    for q in queries:
        print(f"\nQuery: {q}")
        results = pipeline.search(q, limit=2)
        for r in results:
            print(f" - [{r.get('metadata', {}).get('document_id')}] {r.get('text', '')[:100]}...")

if __name__ == "__main__":
    main()
