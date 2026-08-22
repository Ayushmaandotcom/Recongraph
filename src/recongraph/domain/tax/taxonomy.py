"""Indian tax-identifier taxonomy and format validators.

Ported from India Compliance (`india_compliance/gst_india/constants/__init__.py`),
Resilient Tech, GPL v3. See the project NOTICE for attribution.

The patterns classify GSTINs by taxpayer category (Registered Regular,
Composition, SEZ, Overseas, UIN, Tax Deductor, Tax Collector, ISD) and validate
PAN, PIN code, and GST invoice-number formats.
"""

import re
from enum import Enum


# --- GSTIN category patterns (source: developer.gst.gov.in) -----------------
#
# A 15-char GSTIN is laid out as:
#   SS PPPPP CCCC E P Z D
#   SS    = state code (2 digits)
#   PPPPP = PAN-derived (10 chars, positions 3-12)
#   CCCC  = entity code
#   E     = entity type (letter)
#   P     = position (letter/digit)
#   Z     = 'Z' (or category-specific letter)
#   D     = check digit (mod-36)

# Normal taxpayer (not TCS)
NORMAL = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z1-9ABD-J]{1}[0-9A-Z]{1}$"
# Government department ID
GOVT_DEPTID = r"^[0-9]{2}[A-Z]{4}[0-9]{5}[A-Z]{1}[0-9]{1}[Z]{1}[0-9]{1}$"
REGISTERED = re.compile(rf"{NORMAL}|{GOVT_DEPTID}")

# Not allowed in GSTR-1 B2B
NRI_ID = r"^[0-9]{4}[A-Z]{3}[0-9]{5}[N][R][0-9A-Z]{1}$"
OIDAR = r"^[9][9][0-9]{2}[A-Z]{3}[0-9]{5}[O][S][0-9A-Z]{1}$"
OVERSEAS = re.compile(rf"{NRI_ID}|{OIDAR}")

# UIN Holders (UN bodies / other notified persons)
UNBODY = re.compile(r"^[0-9]{4}[A-Z]{3}[0-9]{5}[UO]{1}[N][A-Z0-9]{1}$")

# Tax Deductor (TDS) — position 14 is 'D'
TDS = re.compile(r"^[0-9]{2}[A-Z]{4}[A-Z0-9]{1}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[D][0-9A-Z]$")

# Tax Collector (TCS) — position 14 is 'C'
TCS = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[C]{1}[0-9A-Z]{1}$")

# Generic "looks like a GSTIN" pattern
GSTIN_FORMAT = re.compile(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}")

GSTIN_FORMATS: dict[str, re.Pattern[str]] = {
    "Registered Regular": REGISTERED,
    "Registered Composition": REGISTERED,
    "SEZ": REGISTERED,
    "Overseas": OVERSEAS,
    "Deemed Export": REGISTERED,
    "UIN Holders": UNBODY,
    "Tax Deductor": TDS,
    "Tax Collector": TCS,
    "Input Service Distributor": REGISTERED,
}

# --- PAN / PIN / invoice-number formats -------------------------------------

PAN_NUMBER = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
PINCODE_FORMAT = re.compile(r"^[1-9][0-9]{5}$")

# Max length 16; first char alphanumeric; rest alphanumeric, hyphens or slashes.
GST_INVOICE_NUMBER_FORMAT = re.compile(r"^[^\W_][A-Za-z0-9\-\/]{0,15}$")


class GstinCategory(str, Enum):
    """High-level GSTIN taxpayer categories.

    Multiple `GSTIN_FORMATS` keys collapse onto a single category because they
    share an identical regex (e.g. Registered Regular / Composition / SEZ all
    use `REGISTERED`). Classification returns the *most specific* match.
    """

    REGISTERED = "Registered"
    OVERSEAS = "Overseas"
    UIN_HOLDERS = "UIN Holders"
    TAX_DEDUCTOR = "Tax Deductor"
    TAX_COLLECTOR = "Tax Collector"
    UNKNOWN = "Unknown"


# Ordered so that the more specific categories win. TDS/TCS/UIN/Overseas have
# distinct check-position letters; REGISTERED is the fallback.
_CATEGORY_ORDER: tuple[tuple[GstinCategory, re.Pattern[str]], ...] = (
    (GstinCategory.TAX_DEDUCTOR, TDS),
    (GstinCategory.TAX_COLLECTOR, TCS),
    (GstinCategory.UIN_HOLDERS, UNBODY),
    (GstinCategory.OVERSEAS, OVERSEAS),
    (GstinCategory.REGISTERED, REGISTERED),
)


def classify_gstin_category(gstin: str | None) -> GstinCategory | None:
    """Classify a raw GSTIN string into a taxpayer category.

    Returns ``None`` when the input is empty or matches no known category.
    """
    if not gstin:
        return None
    value = str(gstin).strip().upper()
    if not value:
        return None
    for category, pattern in _CATEGORY_ORDER:
        if pattern.match(value):
            return category
    return None


def is_valid_gstin_format(gstin: str | None) -> bool:
    """True if the string matches *any* known GSTIN category pattern."""
    return classify_gstin_category(gstin) is not None


def validate_pan(pan: str | None) -> bool:
    if not pan:
        return False
    return bool(PAN_NUMBER.match(str(pan).strip().upper()))


def validate_pincode(pincode: str | None) -> bool:
    if not pincode:
        return False
    return bool(PINCODE_FORMAT.match(str(pincode).strip()))


def validate_invoice_number(invoice_number: str | None) -> bool:
    if not invoice_number:
        return False
    return bool(GST_INVOICE_NUMBER_FORMAT.match(str(invoice_number).strip()))
