import re
import uuid
from typing import Dict, Tuple

class PIIRedactor:
    """
    Redacts sensitive Indian financial PII (GSTIN, PAN, Emails, Phone Numbers)
    from text before sending it to external LLM providers.
    Maintains a mapping to restore the PII in the final response.
    """
    
    # Patterns for sensitive Indian data
    # GSTIN format: 2 digits, 10 char PAN, 1 alphanumeric, 'Z', 1 alphanumeric
    GSTIN_PATTERN = r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b'
    PAN_PATTERN = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
    EMAIL_PATTERN = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    PHONE_PATTERN = r'\b(?:(?:\+|0{0,2})91(?:\s*[\-]\s*)?|[0]?)?[6789]\d{9}\b'
    
    def __init__(self):
        self._patterns = {
            "GSTIN": re.compile(self.GSTIN_PATTERN, re.IGNORECASE),
            "PAN": re.compile(self.PAN_PATTERN, re.IGNORECASE),
            "EMAIL": re.compile(self.EMAIL_PATTERN, re.IGNORECASE),
            "PHONE": re.compile(self.PHONE_PATTERN)
        }

    def redact(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replaces sensitive entities in the text with placeholder tokens.
        Returns the redacted text and a mapping of token -> original value.
        """
        mapping = {}
        redacted_text = text
        
        for entity_type, pattern in self._patterns.items():
            matches = set(pattern.findall(redacted_text))
            
            for match in matches:
                # Create a unique placeholder like <GSTIN_1234>
                token = f"<{entity_type}_{uuid.uuid4().hex[:6]}>"
                mapping[token] = match
                
                # Replace exactly the matched string
                redacted_text = redacted_text.replace(match, token)
                
        return redacted_text, mapping

    def restore(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Restores the original PII into the LLM's response using the mapping.
        """
        restored_text = text
        for token, original_value in mapping.items():
            restored_text = restored_text.replace(token, original_value)
            
        return restored_text
