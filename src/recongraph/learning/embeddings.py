from typing import Protocol, List
import numpy as np

class EmbeddingProvider(Protocol):
    def encode(self, texts: List[str]) -> np.ndarray: ...
    @property
    def dimensions(self) -> int: ...
    @property
    def name(self) -> str: ...

class MiniLMProvider:
    def __init__(self):
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('all-MiniLM-L6-v2')

    def encode(self, texts: List[str]) -> np.ndarray:
        self._load()
        return self._model.encode(texts)

    @property
    def dimensions(self) -> int:
        return 384

    @property
    def name(self) -> str:
        return 'all-MiniLM-L6-v2'

class BGEProvider:
    def __init__(self):
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('BAAI/bge-small-en-v1.5')

    def encode(self, texts: List[str]) -> np.ndarray:
        self._load()
        return self._model.encode(texts)

    @property
    def dimensions(self) -> int:
        return 384

    @property
    def name(self) -> str:
        return 'bge-small-en-v1.5'

def get_embedding_provider(name: str = 'minilm') -> EmbeddingProvider:
    if name.lower() == 'bge':
        return BGEProvider()
    return MiniLMProvider()
