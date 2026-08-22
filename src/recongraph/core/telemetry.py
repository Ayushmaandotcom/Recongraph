import time
from typing import Callable, Any, Optional
import functools
import logging

# We mock OpenTelemetry interfaces here so we don't force a massive dependency on the system yet,
# but the architecture supports it natively.
class MockSpan:
    def __init__(self, name: str):
        self.name = name
        self.start_time = 0
        self.attributes = {}
        
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type:
            self.set_attribute("error", True)
            self.set_attribute("error.message", str(exc_val))
        logging.getLogger("recongraph.telemetry").debug(f"Span {self.name} completed in {duration:.4f}s - {self.attributes}")

class Tracer:
    def __init__(self, name: str):
        self.name = name
        
    def start_as_current_span(self, name: str) -> MockSpan:
        return MockSpan(name)

def get_tracer(name: str) -> Tracer:
    """Returns an OpenTelemetry tracer for the given module name."""
    return Tracer(name)

def trace_function(span_name: Optional[str] = None):
    """Decorator to trace a function execution."""
    def decorator(func: Callable):
        name = span_name or func.__name__
        tracer = get_tracer(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name) as span:
                span.set_attribute("function.args", str(args))
                return func(*args, **kwargs)
                
        # Handle async functions as well
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name) as span:
                span.set_attribute("function.args", str(args))
                return await func(*args, **kwargs)
                
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator
