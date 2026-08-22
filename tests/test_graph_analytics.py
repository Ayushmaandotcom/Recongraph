import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "recongraph-api"))

from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.graph_analytics import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_graph_analytics_endpoint():
    response = client.get("/analytics/network/run_123")
    assert response.status_code == 200
    
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    
    # Verify serialization format
    assert len(data["nodes"]) == 5
    assert len(data["edges"]) == 4
    
    # Check that supplier node has a risk score
    supplier = next(n for n in data["nodes"] if n["id"] == "V001")
    assert supplier["group"] == "supplier"
    assert "risk_score" in supplier
