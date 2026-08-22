import json
import argparse
from pathlib import Path
from recongraph.learning.rag import get_rag_pipeline
from recongraph.learning.knowledge_base import build_default_knowledge_base

def run_benchmark(dataset_path: str):
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
        
    pipeline = get_rag_pipeline()
    kb = build_default_knowledge_base()
    pipeline.ingest(kb.to_rag_documents())
    
    total_queries = len(dataset)
    hits = 0
    mrr_sum = 0.0
    
    print(f"Running benchmark on {total_queries} queries...")
    
    for item in dataset:
        query = item["query"]
        expected_docs = item["expected_documents"]
        
        # We'll use hybrid search for the benchmark
        try:
            results = pipeline.search_hybrid(query, limit=5)
        except Exception:
            results = pipeline.search(query, limit=5)
            
        retrieved_ids = [r.get("metadata", {}).get("document_id") for r in results]
        
        # Calculate Hit (Recall@5)
        hit = any(expected in retrieved_ids for expected in expected_docs)
        if hit:
            hits += 1
            
        # Calculate MRR (Mean Reciprocal Rank)
        rank = 0
        for i, ret_id in enumerate(retrieved_ids):
            if ret_id in expected_docs:
                rank = i + 1
                break
        
        if rank > 0:
            mrr_sum += 1.0 / rank
            
    recall_at_5 = hits / total_queries
    mrr = mrr_sum / total_queries
    
    print(f"\n--- Benchmark Results ---")
    print(f"Total Queries: {total_queries}")
    print(f"Recall@5:      {recall_at_5:.2%}")
    print(f"MRR@5:         {mrr:.4f}")
    
    return recall_at_5, mrr

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark RAG Retrieval")
    parser.add_argument("--dataset", type=str, default="tests/data/rag_benchmark.json", help="Path to benchmark JSON")
    args = parser.parse_args()
    
    run_benchmark(args.dataset)
