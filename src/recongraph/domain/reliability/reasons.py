from enum import Enum

class ReliabilityReason(str, Enum):
    # --- Extraction Reasons ---
    OCR_HIGH_CONFIDENCE = "ocr_high_confidence"           # OCR engine reported >= 0.90
    OCR_MEDIUM_CONFIDENCE = "ocr_medium_confidence"       # OCR engine reported 0.70–0.90
    OCR_LOW_CONFIDENCE = "ocr_low_confidence"             # OCR engine reported 0.50–0.70
    OCR_UNREADABLE = "ocr_unreadable"                     # OCR engine reported < 0.50
    BARCODE_SCAN_SUCCESS = "barcode_scan_success"         # Barcode decoded successfully
    BARCODE_SCAN_PARTIAL = "barcode_scan_partial"         # Barcode partially decoded
    QR_DECODE_SUCCESS = "qr_decode_success"               # QR code fully decoded
    QR_DECODE_PARTIAL = "qr_decode_partial"               # QR code partially decoded
    API_RESPONSE_OK = "api_response_ok"                   # API returned 200 with valid payload
    API_RESPONSE_DEGRADED = "api_response_degraded"       # API returned data but with warnings
    DIGITAL_TEXT_LAYER = "digital_text_layer"              # Extracted from PDF text layer (not image)
    LLM_EXTRACTION = "llm_extraction"                     # Value extracted by an LLM
    MANUAL_TRANSCRIPTION = "manual_transcription"         # Human typed the value
    EXTERNAL_SYSTEM_IMPORT = "external_system_import"     # Imported from external vendor system

    # --- Parser Reasons ---
    PARSER_CANONICAL = "parser_canonical"                  # Standard parser succeeded
    PARSER_NORMALIZED = "parser_normalized"                # Normalization rules applied
    PARSER_FALLBACK = "parser_fallback"                    # Fallback heuristic used
    PARSER_RECOVERED = "parser_recovered"                  # Value reconstructed from partial data
    PARSER_FAILED = "parser_failed"                        # Parser could not produce a value

    # --- Completeness Reasons ---
    FIELD_PRESENT = "field_present"                        # Field fully observed
    FIELD_PARTIAL = "field_partial"                        # Field partially observed
    FIELD_ABSENT_EXPECTED = "field_absent_expected"        # Required field missing
    FIELD_ABSENT_OPTIONAL = "field_absent_optional"        # Optional field missing
    FIELD_NOT_APPLICABLE = "field_not_applicable"          # Field irrelevant for record type

    # --- Verification Reasons ---
    CROSS_SYSTEM_VERIFIED = "cross_system_verified"       # Confirmed by independent system
    MULTI_DOCUMENT_MATCH = "multi_document_match"         # Same value across multiple documents
    MANUAL_REVIEW_CONFIRMED = "manual_review_confirmed"   # Human reviewer confirmed correctness
    MANUAL_REVIEW_OVERRIDE = "manual_review_override"     # Human reviewer overrode extracted value
    NO_VERIFICATION_AVAILABLE = "no_verification_available" # Single-source, unverified

    # --- Contradiction / Conflict Reasons ---
    CONTRADICTED_BY_OTHER_SOURCE = "contradicted_by_other_source" # Different value from another source
    CONTRADICTED_BY_CHECKSUM = "contradicted_by_checksum"         # Value fails checksum validation
    DERIVED_FROM_CALCULATION = "derived_from_calculation"         # Value was computed, not observed
