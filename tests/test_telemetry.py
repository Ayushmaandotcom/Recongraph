import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.core.telemetry import trace_function

def test_telemetry_tracing(caplog):
    import logging
    caplog.set_level(logging.DEBUG, logger="recongraph.telemetry")
    
    @trace_function("test_operation")
    def dummy_func(a, b):
        return a + b
        
    result = dummy_func(2, 3)
    assert result == 5
    
    # Check that a log was emitted
    log_text = caplog.text
    assert "Span test_operation completed" in log_text
    assert "'function.args': '(2, 3)'" in log_text
