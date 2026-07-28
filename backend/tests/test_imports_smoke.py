import os
import sys
import unittest

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)


class TestPipelineImports(unittest.TestCase):
    """Smoke test: Verify all pipeline modules import cleanly without NameError or AttributeError."""

    def test_pipeline_imports(self):
        import app.pipeline.report_generator as report_gen
        import app.pipeline.research_agent as research
        import app.pipeline.specialized_agents as specialized
        import app.pipeline.rules_engine as rules
        import app.pipeline.cache as cache
        import app.pipeline.state as state
        import services.llm as llm

        # Assert critical top-level imports and symbols exist
        self.assertTrue(hasattr(report_gen, "report_generator_node"))
        self.assertTrue(hasattr(report_gen, "time"))
        self.assertTrue(hasattr(research, "research_agent_node"))
        self.assertTrue(hasattr(specialized, "strategy_agent_node"))
        self.assertTrue(hasattr(specialized, "finance_agent_node"))
        self.assertTrue(hasattr(rules, "business_rules_engine_node"))
        self.assertTrue(hasattr(cache, "fetch_cached_agent_outputs"))
        self.assertTrue(hasattr(llm, "call_llm"))
        print("\n[Smoke Test] All pipeline modules and services imported successfully!")


if __name__ == "__main__":
    unittest.main()
