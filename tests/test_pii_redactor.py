import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.security.pii_redactor import PIIRedactor

def test_redact_and_restore_gstin():
    redactor = PIIRedactor()
    text = "The supplier with GSTIN 27AAACR4321A1Z5 failed to file returns."
    
    redacted, mapping = redactor.redact(text)
    
    assert "27AAACR4321A1Z5" not in redacted
    assert "<GSTIN_" in redacted
    
    restored = redactor.restore(redacted, mapping)
    assert restored == text

def test_redact_and_restore_pan():
    redactor = PIIRedactor()
    text = "Their PAN is ABCDE1234F. Please verify."
    
    redacted, mapping = redactor.redact(text)
    
    assert "ABCDE1234F" not in redacted
    assert "<PAN_" in redacted
    
    restored = redactor.restore(redacted, mapping)
    assert restored == text

def test_redact_multiple_entities():
    redactor = PIIRedactor()
    text = "Contact supplier@example.com or 9876543210. GSTIN: 27AAACR4321A1Z5"
    
    redacted, mapping = redactor.redact(text)
    
    assert "supplier@example.com" not in redacted
    assert "9876543210" not in redacted
    assert "27AAACR4321A1Z5" not in redacted
    
    assert len(mapping) == 3
    
    restored = redactor.restore(redacted, mapping)
    assert restored == text
