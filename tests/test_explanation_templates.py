import pytest
from pathlib import Path
from recongraph.graph.explanation_templates import ExplanationTemplateRegistry

def test_explanation_template_registry_default():
    registry = ExplanationTemplateRegistry()
    assert registry.get_template("MISSING", "Default text.") == "Default text."
    
def test_explanation_template_registry_render():
    registry = ExplanationTemplateRegistry({
        "EXECUTIVE_MATCH": "The match was {decision} with {coverage} coverage."
    })
    
    rendered = registry.render("EXECUTIVE_MATCH", {"decision": "MATCH", "coverage": "100%"}, default="")
    assert rendered == "The match was MATCH with 100% coverage."
    
def test_explanation_template_registry_safe_render_missing_keys():
    registry = ExplanationTemplateRegistry({
        "EXECUTIVE_MATCH": "The match was {decision} with {coverage} coverage."
    })
    
    # Missing coverage key should not raise KeyError
    rendered = registry.render("EXECUTIVE_MATCH", {"decision": "MATCH"}, default="")
    assert rendered == "The match was MATCH with {coverage} coverage."

def test_explanation_template_registry_from_file(tmp_path: Path):
    template_file = tmp_path / "templates.json"
    template_file.write_text('{"TRACE_NODE": "Trace {node_id}"}')
    
    registry = ExplanationTemplateRegistry.from_file(template_file)
    rendered = registry.render("TRACE_NODE", {"node_id": "TRACE_123"}, default="")
    assert rendered == "Trace TRACE_123"

def test_explanation_template_registry_from_missing_file():
    registry = ExplanationTemplateRegistry.from_file(Path("/does/not/exist.json"))
    rendered = registry.render("TRACE_NODE", {"node_id": "TRACE_123"}, default="Fallback {node_id}")
    assert rendered == "Fallback TRACE_123"
