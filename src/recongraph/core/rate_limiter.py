import time
import threading
from typing import Dict

class RateLimitExceeded(Exception):
    pass

class TokenBucketRateLimiter:
    """
    In-memory Token Bucket rate limiter.
    In production, this would be backed by Redis.
    """
    
    def __init__(self, capacity: int = 100, refill_rate_per_sec: float = 10.0):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self._buckets: Dict[str, dict] = {}
        self._lock = threading.Lock()
        
    def _refill(self, bucket: dict):
        now = time.time()
        elapsed = now - bucket['last_refill']
        tokens_to_add = elapsed * self.refill_rate
        
        if tokens_to_add > 0:
            bucket['tokens'] = min(self.capacity, bucket['tokens'] + tokens_to_add)
            bucket['last_refill'] = now

    def acquire(self, tenant_id: str, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens for a tenant.
        Raises RateLimitExceeded if insufficient tokens.
        """
        with self._lock:
            if tenant_id not in self._buckets:
                self._buckets[tenant_id] = {
                    'tokens': self.capacity,
                    'last_refill': time.time()
                }
                
            bucket = self._buckets[tenant_id]
            self._refill(bucket)
            
            if bucket['tokens'] >= tokens:
                bucket['tokens'] -= tokens
                return True
            else:
                raise RateLimitExceeded(f"Rate limit exceeded for tenant {tenant_id}. Available: {bucket['tokens']:.1f}, Required: {tokens}")
