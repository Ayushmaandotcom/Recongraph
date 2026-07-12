LEGAL_SUFFIX_TOKENS = {
    "pvt",
    "private",
    "ltd",
    "limited",
}


def normalize_reference(reference: str) -> str:
    """Normalize a financial reference for deterministic comparison."""
    return "".join(
        character.lower()
        for character in reference
        if character.isalnum()
    )


def normalize_vendor_name(name: str) -> str:
    """Normalize a vendor name while preserving meaningful word boundaries."""
    cleaned_name = "".join(
        character.lower() if character.isalnum() else " "
        for character in name
    )

    tokens = cleaned_name.split()

    meaningful_tokens = [
        token
        for token in tokens
        if token not in LEGAL_SUFFIX_TOKENS
    ]

    return " ".join(meaningful_tokens)
