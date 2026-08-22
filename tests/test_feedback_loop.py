import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.learning.feedback_loop import FeedbackLoop

def test_feedback_loop_logging():
    feedback = FeedbackLoop()
    
    fid = feedback.log_correction(
        tenant_id="tenant_X",
        user_id="user_123",
        purchase_id="PUR_999",
        gst_id="GST_999",
        is_match=True,
        features={"tfidf_score": 0.85, "amount_diff": 0}
    )
    
    assert fid is not None
    
    data = feedback.get_training_data()
    assert len(data) == 1
    assert data[0]["label"] == 1
    assert data[0]["tenant_id"] == "tenant_X"
    assert data[0]["features"]["tfidf_score"] == 0.85

def test_feedback_loop_multiple_entries():
    feedback = FeedbackLoop()
    
    feedback.log_correction("T1", "U1", "P1", "G1", True, {})
    feedback.log_correction("T1", "U1", "P2", "G2", False, {})
    
    data = feedback.get_training_data()
    assert len(data) == 2
    assert data[0]["label"] == 1
    assert data[1]["label"] == 0
