import pytest
import time
from dataclasses import FrozenInstanceError
from recongraph.graph.trace import TraceBuilder, TraceStage

def test_trace_builder_chronology():
    builder = TraceBuilder(trace_id="TRC-001", engine_version="1.0.0", config_hash="abcd")
    
    # Simulate a pipeline execution
    builder.record_event(TraceStage.CANDIDATE_GENERATION, {"edge": "P1-G1"})
    time.sleep(0.01) # Ensure timestamp increment
    builder.record_event(TraceStage.GRAPH_BUILDING, {"nodes": 2})
    time.sleep(0.01)
    builder.record_event(TraceStage.DECISION_EVALUATION, {"action": "AUTO_MATCH"})
    
    trace = builder.build()
    
    assert trace.trace_id == "TRC-001"
    assert len(trace.events) == 3
    
    # Verify strict chronology
    assert trace.events[0].timestamp < trace.events[1].timestamp < trace.events[2].timestamp
    
    # Verify stages
    assert trace.events[0].stage == TraceStage.CANDIDATE_GENERATION
    assert trace.events[1].stage == TraceStage.GRAPH_BUILDING
    assert trace.events[2].stage == TraceStage.DECISION_EVALUATION
    
    # Verify payload preservation
    assert trace.events[0].payload["edge"] == "P1-G1"
    
    # Verify filtering
    assert len(trace.get_events_for_stage(TraceStage.CANDIDATE_GENERATION)) == 1
    assert len(trace.get_events_for_stage(TraceStage.HYPOTHESIS_SEARCH)) == 0

def test_trace_immutability():
    builder = TraceBuilder(trace_id="TRC-002", engine_version="1.0.0", config_hash="abcd")
    builder.record_event(TraceStage.COMPONENT_EXTRACTION, "Component A")
    
    trace = builder.build()
    
    # DecisionTrace is frozen
    with pytest.raises(FrozenInstanceError):
        trace.trace_id = "TRC-003"
        
    # Appending to builder after build does not mutate the frozen trace
    builder.record_event(TraceStage.HYPOTHESIS_SEARCH, "Hypothesis 1")
    assert len(trace.events) == 1
