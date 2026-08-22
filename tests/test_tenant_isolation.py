import pytest
from recongraph.learning.copilot_tools import get_invoice_details, get_decision_trace, set_runs_store

def test_tenant_isolation_invoice_details():
    mock_store = {
        "run_123": {
            "status": "success",
            "tenant_id": "tenant_A",
            "result": {
                "auto_matches": [],
                "review_packets": [
                    {
                        "packet_id": "pkt_1",
                        "purchases": [{"record_id": "inv_1"}],
                        "gsts": []
                    }
                ]
            }
        }
    }
    
    set_runs_store(mock_store)
    
    # Should work for same tenant
    res1 = get_invoice_details("run_123", "inv_1", tenant_id="tenant_A")
    assert res1.get("error") is None
    assert res1.get("found_in") == "review_packets"
    
    # Should fail for different tenant
    res2 = get_invoice_details("run_123", "inv_1", tenant_id="tenant_B")
    assert res2.get("error") == "Access denied: Tenant mismatch."
    
def test_tenant_isolation_decision_trace():
    mock_store = {
        "run_123": {
            "status": "success",
            "tenant_id": "tenant_A",
            "result": {
                "review_packets": [
                    {
                        "packet_id": "pkt_1",
                        "decision": "REVIEW",
                        "polarity": "NONE"
                    }
                ]
            }
        }
    }
    
    set_runs_store(mock_store)
    
    # Should work for same tenant
    res1 = get_decision_trace("run_123", "pkt_1", tenant_id="tenant_A")
    assert res1.get("error") is None
    assert res1.get("packet_id") == "pkt_1"
    
    # Should fail for different tenant
    res2 = get_decision_trace("run_123", "pkt_1", tenant_id="tenant_B")
    assert res2.get("error") == "Access denied: Tenant mismatch."
