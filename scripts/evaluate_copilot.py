import json
import argparse
from typing import List, Dict, Any

from recongraph.learning.rag import get_rag_pipeline
from recongraph.learning.knowledge_base import build_default_knowledge_base
from recongraph.learning.llm_provider import get_llm_provider, AnswerClaims
from recongraph.learning.grounding import validate_citations
from recongraph.learning.confidence import compute_confidence
from recongraph.learning.circuit_breaker import CircuitBreaker

def run_evaluation(dataset_path: str):
    print("Initializing components...")
    pipeline = get_rag_pipeline()
    kb = build_default_knowledge_base()
    pipeline.ingest(kb.to_rag_documents())
    
    llm = get_llm_provider("gemini") # Or default
    breaker = CircuitBreaker()
    
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
        
    print(f"Starting E2E Evaluation on {len(dataset)} queries...\n")
    
    results = []
    
    for item in dataset:
        query = item["query"]
        print(f"Query: {query}")
        
        # 1. Retrieval
        retrieved_docs = pipeline.search_hybrid(query, limit=3)
        confidence = compute_confidence(retrieved_docs)
        
        if confidence.level == "INSUFFICIENT":
            print("  -> ABSTAINED (Insufficient Confidence)")
            results.append({"query": query, "status": "ABSTAINED"})
            continue
            
        context = "\n\n".join([
            f"DocID: {d.get('metadata', {}).get('document_id')}\nText: {d.get('text')}"
            for d in retrieved_docs
        ])
        
        # 2. LLM Generation
        prompt = f"Answer this query based only on the context below. Query: {query}\n\nContext:\n{context}"
        try:
            response = breaker.execute(llm.generate, prompt, AnswerClaims)
            claims = AnswerClaims.model_validate_json(response)
        except Exception as e:
            print(f"  -> ERROR during LLM generation: {str(e)}")
            results.append({"query": query, "status": "ERROR", "error": str(e)})
            continue
            
        # 3. Grounding Validation
        grounding = validate_citations(claims, retrieved_docs)
        
        print(f"  -> Grounded: {grounding.is_fully_grounded}")
        if not grounding.is_fully_grounded:
            print(f"  -> Hallucinated Citations: {grounding.hallucinated_citations}")
            
        results.append({
            "query": query,
            "status": "SUCCESS",
            "grounded": grounding.is_fully_grounded,
            "claims": claims.dict(),
            "hallucinations": grounding.hallucinated_citations
        })
        
    # Summary
    successes = [r for r in results if r["status"] == "SUCCESS"]
    grounded = [r for r in successes if r.get("grounded")]
    
    print("\n--- Evaluation Summary ---")
    print(f"Total: {len(dataset)}")
    print(f"Success: {len(successes)}")
    print(f"Abstained/Errors: {len(dataset) - len(successes)}")
    if successes:
        print(f"Grounding Rate: {len(grounded) / len(successes):.2%}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="tests/data/rag_benchmark.json")
    args = parser.parse_args()
    run_evaluation(args.dataset)
