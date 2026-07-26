# Troubleshooting

**Issue: My custom provider isn't changing the score.**
Check if the provider returns a scalar or `EvidenceSummary`. Make sure you've registered it in the `ReconGraphEngine` constructor.

**Issue: OCR_AMOUNT_WARNING appears but OCR is perfect.**
Check the `ReliabilityEnvelope` on your input record. The `ExtractionQuality` must be `AUTHORITATIVE` or `HIGH` to bypass attenuation.
