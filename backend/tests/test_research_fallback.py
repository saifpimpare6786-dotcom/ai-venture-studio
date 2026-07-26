from unittest.mock import patch
from app.pipeline.research_agent import research_agent_node

def test_research_agent_live_tavily_path():
    mock_state = {
        "project_id": "test-proj-live",
        "plan": "Business Plan: EcoSphere carbon audit SaaS.\nWeb Research Recommendations:\n1. UK SECR compliance requirements 2026",
        "force_refresh": True,
    }

    mock_search = {
        "answer": "SECR mandates energy disclosure for large UK companies.",
        "results": [{"title": "SECR Guide", "url": "https://gov.uk/secr", "content": "Detailed SECR rules..."}]
    }

    with patch('app.pipeline.research_agent.call_llm', return_value="UK SECR compliance requirements 2026"), \
         patch('app.pipeline.research_agent.execute_tavily_search', return_value=mock_search), \
         patch('app.pipeline.research_agent.ingest_chunks', return_value=None), \
         patch('app.pipeline.research_agent.get_supabase_client', side_effect=Exception("DB skip")):
        
        res = research_agent_node(mock_state)
        output = res.get("research_results", "")
        assert "[Live Tavily Search]" in output
        assert "SECR mandates energy disclosure" in output
        print("[Test 1] Live Tavily Search path PASSED!")


def test_research_agent_local_rag_fallback_path():
    mock_state = {
        "project_id": "test-proj-rag-fallback",
        "plan": "Business Plan: EcoSphere carbon audit SaaS.\nWeb Research Recommendations:\n1. UK Environment Act carbon audit rules",
        "force_refresh": True,
    }

    mock_rag_chunks = [
        "National carbon emission accounting policies in 2026 enforce strict deadlines.",
        "UK Environment Act 2021 mandates carbon disclosures for companies above 250 employees."
    ]

    with patch('app.pipeline.research_agent.call_llm', return_value="UK Environment Act carbon audit rules"), \
         patch('app.pipeline.research_agent.execute_tavily_search', return_value={}), \
         patch('app.pipeline.research_agent.retrieve_context', return_value=mock_rag_chunks), \
         patch('app.pipeline.research_agent.get_supabase_client', side_effect=Exception("DB skip")):
        
        res = research_agent_node(mock_state)
        output = res.get("research_results", "")
        assert "[RESEARCH STATUS WARNING: Local RAG Fallback Active" in output
        assert "[Local RAG Fallback]" in output
        assert "National carbon emission accounting policies" in output
        print("[Test 2] Local RAG Fallback path PASSED!")


def test_research_agent_degraded_empty_context_path():
    mock_state = {
        "project_id": "test-proj-degraded",
        "plan": "Business Plan: Niche Quantum SaaS.\nWeb Research Recommendations:\n1. Obscure quantum computing metric",
        "force_refresh": True,
    }

    with patch('app.pipeline.research_agent.call_llm', return_value="Obscure quantum computing metric"), \
         patch('app.pipeline.research_agent.execute_tavily_search', return_value={}), \
         patch('app.pipeline.research_agent.retrieve_context', return_value=[]), \
         patch('app.pipeline.research_agent.get_supabase_client', side_effect=Exception("DB skip")):
        
        res = research_agent_node(mock_state)
        output = res.get("research_results", "")
        assert "[DEGRADED INPUT WARNING]" in output
        assert "Tavily search failed and local RAG knowledge base contained no relevant chunks" in output
        print("[Test 3] Degraded Empty Context warning path PASSED!")


if __name__ == "__main__":
    test_research_agent_live_tavily_path()
    test_research_agent_local_rag_fallback_path()
    test_research_agent_degraded_empty_context_path()
    print("\nALL RESEARCH AGENT FALLBACK TESTS PASSED SUCCESSFULLY!")
