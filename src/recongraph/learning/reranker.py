from typing import List, Dict, Any

class Reranker:
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.model = None
        self.model_name = model_name
    
    def _load(self):
        if self.model is None:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
    
    def rerank(self, query: str, candidates: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        if not candidates:
            return []
            
        self._load()
        
        pairs = [[query, doc.get("text", "")] for doc in candidates]
        scores = self.model.predict(pairs)
        
        for i, doc in enumerate(candidates):
            doc["reranker_score"] = float(scores[i])
            
        candidates.sort(key=lambda x: x.get("reranker_score", 0), reverse=True)
        return candidates[:limit]
