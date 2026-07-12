from rapidfuzz import fuzz

from recongraph.normalization.text import normalize_vendor_name


VENDOR_PAIRS = [
    (
        "ABC Steel Private Limited",
        "ABC STEELS PVT. LTD.",
        True,
    ),
    (
        "Shree Balaji Enterprises",
        "SHREE BALAJI ENT.",
        True,
    ),
    (
        "Northstar Components Pvt Ltd",
        "Northstar Component Private Limited",
        True,
    ),
    (
        "Metro Office Solutions",
        "METRO OFFICE SOLUTION",
        True,
    ),
    (
        "Apex Industrial Supplies",
        "APEX INDUSTRIAL SUPPLY",
        True,
    ),
    (
        "ABC Steel Private Limited",
        "Metro Office Solutions",
        False,
    ),
    (
        "ABC Steel",
        "ABC Steel Trading",
        False,
    ),
    (
        "Shree Balaji Enterprises",
        "Shree Balaji Foods",
        False,
    ),
    (
        "Northstar Components",
        "Northstar Logistics",
        False,
    ),
    (
        "Apex Industrial Supplies",
        "Apex Industrial Services",
        False,
    ),
    (
        "Metro Office Solutions",
        "Metro Office Furniture",
        False,
    ),
]

METRICS = {
    "ratio": fuzz.ratio,
    "partial_ratio": fuzz.partial_ratio,
    "token_sort_ratio": fuzz.token_sort_ratio,
    "token_set_ratio": fuzz.token_set_ratio,
    "WRatio": fuzz.WRatio,
}

for metric_name, metric in METRICS.items():
    positive_scores = []
    negative_scores = []

    for vendor_a, vendor_b, expected_match in VENDOR_PAIRS:
        normalized_a = normalize_vendor_name(vendor_a)
        normalized_b = normalize_vendor_name(vendor_b)

        score = metric(normalized_a, normalized_b)

        if expected_match:
            positive_scores.append(score)
        else:
            negative_scores.append(score)

    minimum_positive = min(positive_scores)
    maximum_negative = max(negative_scores)

    print("=" * 72)
    print(f"Metric: {metric_name}")
    print(f"Minimum positive score: {minimum_positive:.2f}")
    print(f"Maximum negative score: {maximum_negative:.2f}")
    print(
        "Separation gap: "
        f"{minimum_positive - maximum_negative:.2f}"
    )
