import pytest
from datetime import date
from recongraph.learning.knowledge_base import KnowledgeBaseBuilder, GSTDocument

def test_temporal_retrieval_active_rule():
    builder = KnowledgeBaseBuilder()
    
    # Old rule
    builder.add_document(GSTDocument(
        document_id="RULE_A_v1", document_type="RULE", section=None, subsection=None, rule="A",
        title="Rule A (Old)", effective_from="2017-07-01", effective_to="2021-12-31",
        source="GST", authority="CBIC", jurisdiction="India", financial_year=None,
        version="1", url=None, text="Old rule A."
    ))
    
    # New rule
    builder.add_document(GSTDocument(
        document_id="RULE_A_v2", document_type="RULE", section=None, subsection=None, rule="A",
        title="Rule A (New)", effective_from="2022-01-01", effective_to=None,
        source="GST", authority="CBIC", jurisdiction="India", financial_year=None,
        version="2", url=None, text="New rule A."
    ))

    # Querying in 2020 should return v1
    docs_2020 = builder.get_documents_for_date(date(2020, 5, 1))
    assert len(docs_2020) == 1
    assert docs_2020[0].document_id == "RULE_A_v1"

    # Querying in 2023 should return v2
    docs_2023 = builder.get_documents_for_date(date(2023, 5, 1))
    assert len(docs_2023) == 1
    assert docs_2023[0].document_id == "RULE_A_v2"

def test_resolve_financial_year():
    builder = KnowledgeBaseBuilder()
    assert builder.resolve_financial_year(date(2025, 3, 31)) == "2024-25"
    assert builder.resolve_financial_year(date(2025, 4, 1)) == "2025-26"
