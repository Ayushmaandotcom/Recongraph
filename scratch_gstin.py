def calculate_gstin_checksum(gstin: str) -> str:
    """Standard Indian GSTIN Mod36 Checksum"""
    charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    factor = 1
    sum = 0
    for char in gstin[:-1]:
        val = charset.index(char)
        product = val * factor
        sum += (product // 36) + (product % 36)
        factor = 2 if factor == 1 else 1
    
    checksum_val = (36 - (sum % 36)) % 36
    return charset[checksum_val]
