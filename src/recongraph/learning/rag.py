import os
import uuid
from typing import List, Dict, Any, Optional
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    pass # Handle gracefully if not installed yet

from .embeddings import EmbeddingProvider, get_embedding_provider
from .bm25 import BM25Index
from .reranker import Reranker

class RAGPipeline:
    def __init__(self, 
                 collection_name: str = "gst_rules", 
                 qdrant_url: str = None, 
                 qdrant_path: str = "qdrant_storage",
                 embedding_provider: Optional[EmbeddingProvider] = None,
                 bm25_index: Optional[BM25Index] = None,
                 reranker: Optional[Reranker] = None):
        self.collection_name = collection_name
        try:
            if qdrant_url:
                self.client = QdrantClient(url=qdrant_url)
            else:
                self.client = QdrantClient(path=qdrant_path)
        except Exception:
            # Fallback to in-memory if path fails
            self.client = QdrantClient(location=":memory:")
            
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.bm25 = bm25_index or BM25Index()
        self.reranker = reranker or Reranker()
        
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_provider.dimensions,
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"Warning: Could not connect to Qdrant or create collection: {e}")

    def ingest(self, documents: List[Dict[str, Any]]):
        """
        Ingest a list of documents.
        Each document should be a dict like:
        {"text": "GST Rule...", "metadata": {"source": "CGST Act 2017", "section": "16"}}
        """
        if not documents:
            return

        texts = [doc["text"] for doc in documents]
        embeddings = self.embedding_provider.encode(texts).tolist()

        points = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            doc_id = str(uuid.uuid4())
            doc["document_id"] = doc_id
            
            payload = {
                "text": doc["text"],
                "document_id": doc_id,
            }
            # Spread metadata into payload for filtering
            if "metadata" in doc:
                payload.update(doc["metadata"])
                
            points.append(
                models.PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        # Build BM25 index
        self.bm25.build(documents)

    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Backward-compatible search method using only Qdrant vector search.
        """
        query_vector = self.embedding_provider.encode([query])[0].tolist()
        
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit
        ).points
        
        results = []
        for hit in search_result:
            payload = hit.payload or {}
            text = payload.get("text", "")
            metadata = {k: v for k, v in payload.items() if k not in ("text", "document_id")}
            results.append({
                "score": hit.score,
                "text": text,
                "metadata": metadata,
                "document_id": payload.get("document_id")
            })
            
        return results

    def search_hybrid(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Qdrant Vector search
        query_vector = self.embedding_provider.encode([query])[0].tolist()
        
        qdrant_filter = None
        if filters:
            must_conditions = []
            for k, v in filters.items():
                must_conditions.append(models.FieldCondition(key=k, match=models.MatchValue(value=v)))
            qdrant_filter = models.Filter(must=must_conditions)
            
        vector_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=20
        ).points
        
        vector_docs = {}
        for hit in vector_results:
            payload = hit.payload or {}
            doc_id = payload.get("document_id") or str(hit.id)
            metadata = {k: v for k, v in payload.items() if k not in ("text", "document_id")}
            vector_docs[doc_id] = {
                "document_id": doc_id,
                "text": payload.get("text", ""),
                "metadata": metadata,
                "vector_score": hit.score
            }
            
        # BM25 search
        bm25_results = self.bm25.search(query, limit=20)
        bm25_docs = {}
        for doc in bm25_results:
            doc_id = doc.get("document_id")
            if doc_id:
                # Apply filters manually for BM25 since we didn't add it to index directly
                if filters:
                    metadata = doc.get("metadata", {})
                    match = True
                    for k, v in filters.items():
                        if metadata.get(k) != v:
                            match = False
                            break
                    if not match:
                        continue
                bm25_docs[doc_id] = doc
                
        # RRF (Reciprocal Rank Fusion)
        k = 60
        merged_docs = {}
        
        for rank, doc_id in enumerate(vector_docs.keys()):
            if doc_id not in merged_docs:
                merged_docs[doc_id] = vector_docs[doc_id].copy()
                merged_docs[doc_id]["rrf_score"] = 0.0
            merged_docs[doc_id]["rrf_score"] += 1.0 / (k + rank + 1)
            
        for rank, (doc_id, doc) in enumerate(bm25_docs.items()):
            if doc_id not in merged_docs:
                merged_docs[doc_id] = {
                    "document_id": doc_id,
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "vector_score": 0.0,
                    "rrf_score": 0.0
                }
            merged_docs[doc_id]["bm25_score"] = doc.get("score", 0.0)
            merged_docs[doc_id]["rrf_score"] += 1.0 / (k + rank + 1)
            
        # Get top 20 by RRF score
        candidates = list(merged_docs.values())
        candidates.sort(key=lambda x: x["rrf_score"], reverse=True)
        top_candidates = candidates[:20]
        
        # Rerank
        final_results = self.reranker.rerank(query, top_candidates, limit=limit)
        return final_results

    def search_with_filters(self, query: str, document_type: str = None, financial_year: str = None, section: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        filters = {}
        if document_type:
            filters["document_type"] = document_type
        if financial_year:
            filters["financial_year"] = financial_year
        if section:
            filters["section"] = section
            
        return self.search_hybrid(query, limit=limit, filters=filters)

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id)
                )
            ]
        )
        
        result, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filter_condition,
            limit=1
        )
        
        if result:
            payload = result[0].payload or {}
            metadata = {k: v for k, v in payload.items() if k not in ("text", "document_id")}
            return {
                "document_id": payload.get("document_id", document_id),
                "text": payload.get("text", ""),
                "metadata": metadata
            }
        return None

# Singleton instance for the application to reuse
_rag_pipeline = None

def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        qdrant_url = os.environ.get("QDRANT_URL", None)
        _rag_pipeline = RAGPipeline(qdrant_url=qdrant_url)
    return _rag_pipeline
