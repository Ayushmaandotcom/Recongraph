import re
from datetime import date
from typing import Dict, Any, List
from rapidfuzz import fuzz, distance

def get_val(obj, key1, key2, default=""):
    if isinstance(obj, dict):
        return obj.get(key1, obj.get(key2, default))
    return getattr(obj, key1, getattr(obj, key2, default))

def extract_features(pr: Any, gstr2b: Any, graph_context: Dict[str, Any] = None) -> Dict[str, float]:
    """
    Extracts a comprehensive set of features for AI matching.
    """
    features = {}
    if not graph_context:
        graph_context = {"pr_node_degree": 1, "gst_node_degree": 1, "component_size": 2, "candidate_count": 1}

    # Extract raw values
    pr_inv = str(get_val(pr, "pr_invoice_no", "reference", ""))
    gs_inv = str(get_val(gstr2b, "gstr2b_invoice_no", "reference", ""))
    
    pr_sup = str(get_val(pr, "pr_supplier_name", "supplier_name", ""))
    gs_sup = str(get_val(gstr2b, "gstr2b_supplier_name", "supplier_name", ""))
    
    pr_gstin = str(get_val(pr, "pr_gstin", "tax_identity", ""))
    gs_gstin = str(get_val(gstr2b, "gstr2b_gstin", "tax_identity", ""))
    
    pr_date_val = get_val(pr, "pr_date", "record_date", "")
    gs_date_val = get_val(gstr2b, "gstr2b_date", "record_date", "")
    
    def parse_tax(val):
        try:
            if not val: return 0.0
            return float(val)
        except (ValueError, TypeError):
            return 0.0
            
    pr_taxable = parse_tax(get_val(pr, "pr_taxable", "amount", 0.0))
    gs_taxable = parse_tax(get_val(gstr2b, "gstr2b_taxable", "amount", 0.0))
    pr_cgst = parse_tax(get_val(pr, "pr_cgst", "cgst", 0.0))
    gs_cgst = parse_tax(get_val(gstr2b, "gstr2b_cgst", "cgst", 0.0))
    pr_sgst = parse_tax(get_val(pr, "pr_sgst", "sgst", 0.0))
    gs_sgst = parse_tax(get_val(gstr2b, "gstr2b_sgst", "sgst", 0.0))
    pr_igst = parse_tax(get_val(pr, "pr_igst", "igst", 0.0))
    gs_igst = parse_tax(get_val(gstr2b, "gstr2b_igst", "igst", 0.0))

    # --- Invoice Features ---
    pr_inv_norm = re.sub(r'[^A-Z0-9]', '', pr_inv.upper())
    gs_inv_norm = re.sub(r'[^A-Z0-9]', '', gs_inv.upper())
    pr_inv_digits = re.sub(r'[^0-9]', '', pr_inv)
    gs_inv_digits = re.sub(r'[^0-9]', '', gs_inv)
    
    features['inv_exact_eq'] = 1.0 if pr_inv and pr_inv == gs_inv else 0.0
    features['inv_norm_eq'] = 1.0 if pr_inv_norm and pr_inv_norm == gs_inv_norm else 0.0
    features['inv_levenshtein_dist'] = float(distance.Levenshtein.distance(pr_inv_norm, gs_inv_norm))
    features['inv_levenshtein_sim'] = fuzz.ratio(pr_inv_norm, gs_inv_norm) / 100.0
    features['inv_jaro_winkler'] = distance.JaroWinkler.similarity(pr_inv_norm, gs_inv_norm)
    features['inv_prefix_sim'] = 1.0 if pr_inv_norm and gs_inv_norm and pr_inv_norm[:3] == gs_inv_norm[:3] else 0.0
    features['inv_suffix_sim'] = 1.0 if pr_inv_norm and gs_inv_norm and pr_inv_norm[-3:] == gs_inv_norm[-3:] else 0.0
    features['inv_digit_sim'] = fuzz.ratio(pr_inv_digits, gs_inv_digits) / 100.0

    # --- Supplier Features ---
    features['gstin_exact_eq'] = 1.0 if pr_gstin and pr_gstin == gs_gstin else 0.0
    
    pr_sup_norm = re.sub(r'[^A-Z0-9\s]', '', pr_sup.upper())
    gs_sup_norm = re.sub(r'[^A-Z0-9\s]', '', gs_sup.upper())
    features['sup_name_sim'] = fuzz.token_sort_ratio(pr_sup_norm, gs_sup_norm) / 100.0
    features['sup_token_set_sim'] = fuzz.token_set_ratio(pr_sup_norm, gs_sup_norm) / 100.0

    # --- Date Features ---
    def parse_date(d_val):
        if isinstance(d_val, str):
            try: return date.fromisoformat(d_val)
            except: return date(2000, 1, 1)
        elif isinstance(d_val, date):
            return d_val
        return date(2000, 1, 1)
        
    d1 = parse_date(pr_date_val)
    d2 = parse_date(gs_date_val)
    date_diff = abs((d1 - d2).days) if d1 and d2 else 999
    
    features['date_exact_eq'] = 1.0 if date_diff == 0 else 0.0
    features['date_diff_days'] = float(date_diff)

    # --- Monetary Features ---
    features['taxable_diff'] = abs(pr_taxable - gs_taxable)
    features['taxable_pct_diff'] = features['taxable_diff'] / (max(pr_taxable, gs_taxable) + 1e-5)
    features['cgst_diff'] = abs(pr_cgst - gs_cgst)
    features['sgst_diff'] = abs(pr_sgst - gs_sgst)
    features['igst_diff'] = abs(pr_igst - gs_igst)
    features['total_tax_diff'] = abs((pr_cgst + pr_sgst + pr_igst) - (gs_cgst + gs_sgst + gs_igst))

    # --- Graph Features ---
    features['pr_node_degree'] = float(graph_context.get("pr_node_degree", 1))
    features['gs_node_degree'] = float(graph_context.get("gst_node_degree", 1))
    features['component_size'] = float(graph_context.get("component_size", 2))
    features['candidate_count'] = float(graph_context.get("candidate_count", 1))

    return features

def extract_feature_vector(pr: Any, gstr2b: Any, graph_context: Dict[str, Any] = None) -> List[float]:
    """Returns the features as an ordered list for model input."""
    feat_dict = extract_features(pr, gstr2b, graph_context)
    # Define canonical ordering
    keys = sorted(feat_dict.keys())
    return [feat_dict[k] for k in keys]

def get_feature_names() -> List[str]:
    # Dummy call to get keys in order
    feat_dict = extract_features({}, {})
    return sorted(feat_dict.keys())
