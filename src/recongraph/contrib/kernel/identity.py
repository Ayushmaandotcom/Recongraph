import re
import json
import unicodedata
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True, order=True)
class IdentityDomainId:
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError("IdentityDomainId must be a string.")
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid IdentityDomainId format: '{self.value}'")


@dataclass(frozen=True, slots=True, order=True)
class IdentitySchemaId:
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError("IdentitySchemaId must be a string.")
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid IdentitySchemaId format: '{self.value}'")


@dataclass(frozen=True, slots=True, order=True)
class IdentityDigest:
    value: str

    _PATTERN = re.compile(r"^[a-z0-9]+:[a-f0-9]{64}$")

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError("IdentityDigest must be a string.")
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid IdentityDigest format: '{self.value}'")
            
        algo, h = self.value.split(":")
        if algo != "sha256" or len(h) != 64:
            raise ValueError(f"Unsupported or malformed digest: '{self.value}'")


@dataclass(frozen=True, slots=True, order=True)
class KernelIdentityRef:
    """
    Explicit transport reference for a semantic DAG node.
    Not an owning identity. Transport does not imply trust.
    """
    domain: IdentityDomainId
    schema: IdentitySchemaId
    digest: IdentityDigest


def _validate_canonical_payload(value: Any, for_machine_key: bool = False):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        # Must be signed 64-bit int
        if value < -9223372036854775808 or value > 9223372036854775807:
            raise ValueError("Integer out of int64 bounds.")
        return value
    if isinstance(value, float):
        raise ValueError("Floats are forbidden in canonical semantic encoding.")
    if isinstance(value, str):
        if for_machine_key:
            if not value.isascii():
                raise ValueError("Machine keys must be ASCII.")
            return value
        return unicodedata.normalize("NFC", value)
    if isinstance(value, tuple) or isinstance(value, list):
        return tuple(_validate_canonical_payload(item) for item in value)
    if isinstance(value, dict):
        canon_dict = {}
        for k in sorted(value.keys()):
            if not isinstance(k, str):
                raise ValueError("Dict keys must be strings.")
            canon_k = _validate_canonical_payload(k, for_machine_key=True)
            canon_dict[canon_k] = _validate_canonical_payload(value[k])
        return canon_dict
    raise ValueError(f"Type {type(value)} is forbidden in canonical semantic encoding.")


def canonical_encode(data: Any) -> bytes:
    """
    Produces canonical JSON bytes for semantic identity preimage hashing.
    Enforces int64 bounds, string NFC normalization, and strict dictionary sorting.
    """
    validated_data = _validate_canonical_payload(data)
    return json.dumps(
        validated_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")
