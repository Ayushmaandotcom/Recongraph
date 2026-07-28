import inspect, importlib, dataclasses
from recongraph.plugins import core_providers as cp
from recongraph.engine import ReconGraphEngine

for name in ["FinancialEvidenceProvider", "TemporalEvidenceProvider",
             "TaxEvidenceProvider", "VendorEvidenceProvider",
             "ReferenceEvidenceProvider"]:
    cls = getattr(cp, name, None)
    print(name, inspect.signature(cls.__init__) if cls else "MISSING")

print("ReconGraphEngine.__init__", inspect.signature(ReconGraphEngine.__init__))
print("ReconGraphEngine.reconcile", inspect.signature(ReconGraphEngine.reconcile))

try:
    from recongraph.engine import ReconciliationResult
    print("ReconciliationResult fields:",
          [f.name for f in dataclasses.fields(ReconciliationResult)])
except Exception as e:
    print("ReconciliationResult:", e)

for m in ["context", "corpus", "knowledge", "policy", "parser", "observation"]:
    try:
        mod = importlib.import_module(f"recongraph.domain.vendor.{m}")
        print(f"\nvendor.{m}:")
        for n in dir(mod):
            if n.startswith("_"):
                continue
            obj = getattr(mod, n)
            if inspect.isclass(obj) or inspect.isfunction(obj):
                try:
                    print("   ", n, inspect.signature(obj))
                except (ValueError, TypeError):
                    print("   ", n, "(no signature)")
    except ImportError as e:
        print(f"\nvendor.{m}: MISSING ({e})")
