import time
from typing import Callable, Any

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED" # CLOSED (ok), OPEN (failing, halt requests), HALF_OPEN (testing recovery)
        
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN. Failing fast.")
                
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self._reset()
            return result
        except Exception as e:
            self._record_failure()
            raise e
            
    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            
    def _reset(self):
        self.failure_count = 0
        self.state = "CLOSED"
