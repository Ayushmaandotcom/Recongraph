import math
import re
from typing import List, Dict, Any
from collections import Counter

class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self.avgdl = 0
        self.corpus_size = 0

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        # Keep alphanumeric, especially for section numbers, rule numbers, GSTINs
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'as', 'is', 'are', 'was', 'were'}
        return [t for t in tokens if t not in stopwords]

    def build(self, documents: List[Dict[str, Any]]):
        self.documents = documents
        self.corpus_size = len(documents)
        self.doc_len = []
        self.doc_freqs = []
        
        df = Counter()
        num_tokens = 0
        
        for doc in documents:
            # Generate UUID if not present to ensure document_id is there
            if "document_id" not in doc:
                import uuid
                doc["document_id"] = str(uuid.uuid4())
                
            tokens = self._tokenize(doc.get("text", ""))
            self.doc_len.append(len(tokens))
            num_tokens += len(tokens)
            
            freqs = Counter(tokens)
            self.doc_freqs.append(freqs)
            
            for token in freqs:
                df[token] += 1
                
        self.avgdl = num_tokens / self.corpus_size if self.corpus_size > 0 else 0
        
        self.idf = {}
        for token, freq in df.items():
            self.idf[token] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.documents:
            return []
            
        query_tokens = self._tokenize(query)
        scores = []
        
        for idx in range(self.corpus_size):
            score = 0.0
            doc_len = self.doc_len[idx]
            if doc_len == 0:
                scores.append((score, idx))
                continue
                
            doc_freq = self.doc_freqs[idx]
            
            for token in query_tokens:
                if token not in self.doc_freqs[idx]:
                    continue
                    
                freq = doc_freq[token]
                num = freq * (self.k1 + 1)
                den = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score += self.idf.get(token, 0) * (num / den)
                
            scores.append((score, idx))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, idx in scores[:limit]:
            doc = self.documents[idx].copy()
            doc["score"] = score
            results.append(doc)
            
        return results
