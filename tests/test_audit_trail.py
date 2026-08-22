import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.security.audit_trail import SecureAuditTrail

def test_audit_trail_valid_chain():
    audit = SecureAuditTrail()
    
    # Append 3 events
    id1 = audit.append("tenant_A", "RECON_DECISION", {"status": "matched"})
    id2 = audit.append("tenant_A", "LLM_EXPLANATION", {"reason": "Valid ITC"})
    id3 = audit.append("tenant_B", "RECON_DECISION", {"status": "abstained"})
    
    # Verify chain
    assert audit.verify_chain() is True

def test_audit_trail_tampering_breaks_chain():
    audit = SecureAuditTrail()
    
    id1 = audit.append("tenant_A", "RECON_DECISION", {"status": "matched"})
    id2 = audit.append("tenant_A", "LLM_EXPLANATION", {"reason": "Valid ITC"})
    
    # Verify initially
    assert audit.verify_chain() is True
    
    # Tamper with the first record
    audit.tamper(id1, {"status": "UNMATCHED_MALICIOUS_CHANGE"})
    
    # Verification should now fail
    assert audit.verify_chain() is False
