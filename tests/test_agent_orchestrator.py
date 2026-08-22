import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.agents.orchestrator import AgentOrchestrator

def test_agent_orchestrator():
    orchestrator = AgentOrchestrator()
    report = orchestrator.run_autonomous_audit("27AAACR4321A1Z5", "High value invoice discrepancy")
    
    # Verify the conversation history recorded the steps
    history = orchestrator.conversation_history
    assert len(history) == 4
    assert history[0].role == "Orchestrator"
    assert history[1].role == "Vendor_Risk_Analyst"
    assert history[2].role == "GST_Law_Expert"
    
    # Verify the final synthesis contains the output from the sub-agents
    assert "Risk of default" in report or "risk of default" in report.lower()
    assert "ITC blocked" in report or "itc blocked" in report.lower()
