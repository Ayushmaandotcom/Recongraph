import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.agents.orchestrator import AgentOrchestrator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autonomous_audit")

def run_audit(gstin: str, context: str):
    logger.info("Initializing Agent Swarm Orchestrator...")
    orchestrator = AgentOrchestrator()
    
    logger.info(f"Triggering deep autonomous audit for supplier {gstin}")
    report = orchestrator.run_autonomous_audit(gstin, context)
    
    print("\n" + "="*50)
    print(report.strip())
    print("="*50 + "\n")
    logger.info("Audit completed and saved to Enterprise Risk Database.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gstin", type=str, default="27AAACR4321A1Z5", help="Supplier GSTIN to audit")
    parser.add_argument("--context", type=str, default="Supplier has 15 unmatched high-value invoices.", help="Context for the audit")
    args = parser.parse_args()
    
    run_audit(args.gstin, args.context)
