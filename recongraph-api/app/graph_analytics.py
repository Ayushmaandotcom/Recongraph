from fastapi import APIRouter
from typing import Dict, List, Any

router = APIRouter(prefix="/analytics", tags=["Graph Analytics"])

@router.get("/network/{run_id}")
async def get_supply_chain_network(run_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Serializes a specific reconciliation run into a Node-Edge format
    optimized for WebGL 3D Graph rendering in the frontend.
    """
    # Mocking a graph response based on a run_id
    # In reality, this would query Postgres or Neo4j for the actual graph data
    
    nodes = [
        {"id": "V001", "label": "Supplier: ACME Corp", "group": "supplier", "risk_score": 0.85},
        {"id": "V002", "label": "Supplier: Globex", "group": "supplier", "risk_score": 0.12},
        {"id": "PUR_1", "label": "Invoice 1 (PR)", "group": "purchase", "amount": 15000},
        {"id": "PUR_2", "label": "Invoice 2 (PR)", "group": "purchase", "amount": 3000},
        {"id": "GST_1", "label": "Invoice 1 (GST)", "group": "gst", "amount": 15000},
    ]
    
    edges = [
        # Supplier owns invoices
        {"source": "V001", "target": "PUR_1", "type": "issued"},
        {"source": "V001", "target": "GST_1", "type": "issued"},
        {"source": "V002", "target": "PUR_2", "type": "issued"},
        
        # Reconciliation links
        {"source": "PUR_1", "target": "GST_1", "type": "matched", "confidence": 0.99},
        # PUR_2 is unmatched (orphan node)
    ]
    
    return {
        "nodes": nodes,
        "edges": edges
    }
