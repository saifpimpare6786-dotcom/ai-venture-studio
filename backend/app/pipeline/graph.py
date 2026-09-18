import asyncio
from typing import Dict, Any
from app.pipeline.state import AgentState
from app.pipeline.planning_agent import planning_node
from app.pipeline.orchestrator_agent import orchestrator_node, research_node
from app.pipeline.specialized_agents import finance_node, parallel_domain_eval
from app.pipeline.council_agent import council_node
from app.pipeline.review_critic_agents import reviewer_node, critic_node
from app.pipeline.rules_engine import rules_node
from app.pipeline.scoring_engine import scoring_node
from app.pipeline.report_generator import report_generator_node
from app.database.db import db

# Per-node timeout configuration (seconds)
NODE_TIMEOUTS = {
    "planning":         120,   # Planning Agent
    "orchestrator":     60,    # Orchestrator Agent
    "research":         90,    # Research Agent (web search can be slow)
    "finance":          120,   # Finance Pricing Anchor (critical, needs headroom)
    "parallel_domain":  180,   # 3 concurrent agents — Strategy, Marketing, Risk
    "council":          120,   # LLM Council Debate
    "reviewer":         90,    # Reviewer Agent
    "critic":           90,    # Adversarial VC Critic
    "rules":            30,    # Deterministic Rules (no LLM, fast)
    "scoring":          15,    # Deterministic Scoring (no LLM, fast)
    "report_gen":       360,   # 13 concurrent reports — largest workload
}

# Total pipeline hard-stop timeout (15 minutes headroom)
PIPELINE_TIMEOUT = 900


async def _run_with_timeout(node_fn, state: AgentState, node_name: str, project_id: str) -> AgentState:
    """
    Wraps a pipeline node with asyncio.wait_for timeout and logs timeout events.
    """
    timeout = NODE_TIMEOUTS.get(node_name, 120)
    try:
        return await asyncio.wait_for(node_fn(state), timeout=timeout)
    except asyncio.TimeoutError:
        error_msg = f"Node '{node_name}' timed out after {timeout}s. Pipeline continuing with partial state."
        print(f"[Pipeline Timeout] {error_msg}")
        await db.add_agent_discussion(
            project_id=project_id,
            agent_name="Timeout Sentry",
            agent_role="Fault Detection",
            message=error_msg,
            step_index=98
        )
        # For non-critical nodes, allow pipeline to continue with existing state
        # For critical nodes (finance, report_gen), re-raise to halt
        critical_nodes = {"finance", "report_gen"}
        if node_name in critical_nodes:
            raise RuntimeError(error_msg)
        return state


class PipelineGraph:
    """
    ECC-Optimized Multi-Agent Deliberation Pipeline with 2 Sentry Gates
    and per-node timeout protection.
    """
    async def run(self, project_id: str, project_data: Dict[str, Any]) -> AgentState:
        # Initial State
        state: AgentState = {
            "project_id": project_id,
            "project_data": project_data,
            "status": "deliberating",
            "discussion_logs": []
        }

        await db.update_project(project_id, {"status": "deliberating"})
        
        # 0. Instant Session Initialization Message (zero latency user feedback)
        await db.add_agent_discussion(
            project_id=project_id,
            agent_name="Pipeline Orchestrator",
            agent_role="Session Initialization",
            message=f"Autonomous boardroom convened for venture '{project_data.get('name', 'Venture')}'. Dispatching Lead Planning Architect...",
            step_index=0
        )

        try:
            # Wrap entire pipeline with hard-stop timeout
            state = await asyncio.wait_for(
                self._run_pipeline(state, project_id),
                timeout=PIPELINE_TIMEOUT
            )
            state["status"] = "completed"
            return state

        except asyncio.TimeoutError:
            state["status"] = "failed"
            error_msg = f"Pipeline exceeded hard-stop timeout of {PIPELINE_TIMEOUT}s."
            print(f"[Pipeline Error] {error_msg}")
            await db.update_project(project_id, {"status": "failed"})
            await db.add_agent_discussion(
                project_id=project_id,
                agent_name="Pipeline Error Sentry",
                agent_role="Timeout Containment",
                message=error_msg,
                step_index=99
            )
            return state

        except Exception as e:
            state["status"] = "failed"
            print(f"[Pipeline Error] {e}")
            await db.update_project(project_id, {"status": "failed"})
            await db.add_agent_discussion(
                project_id=project_id,
                agent_name="Pipeline Error Sentry",
                agent_role="Fault Containment",
                message=f"Pipeline error halted execution: {str(e)}",
                step_index=99
            )
            return state

    async def _run_pipeline(self, state: AgentState, project_id: str) -> AgentState:
        """Core pipeline execution with per-node timeouts."""

        # 1. Planning -> Orchestration -> Research
        state = await _run_with_timeout(planning_node, state, "planning", project_id)
        state = await _run_with_timeout(orchestrator_node, state, "orchestrator", project_id)
        state = await _run_with_timeout(research_node, state, "research", project_id)

        # 2. Finance Pricing Anchor -> Parallel Domains (Strategy, Marketing, Risk)
        state = await _run_with_timeout(finance_node, state, "finance", project_id)
        state = await _run_with_timeout(parallel_domain_eval, state, "parallel_domain", project_id)

        # Gate 1 Sentry Check
        if not state.get("finance_assessment"):
            raise RuntimeError("Gate 1 Sentry Failure: Finance pricing anchor missing.")

        # 3. Boardroom Council -> Reviewer -> Adversarial Critic
        state = await _run_with_timeout(council_node, state, "council", project_id)
        state = await _run_with_timeout(reviewer_node, state, "reviewer", project_id)
        state = await _run_with_timeout(critic_node, state, "critic", project_id)

        # Gate 2 Sentry Check
        if not state.get("critic_assessment"):
            raise RuntimeError("Gate 2 Sentry Failure: Adversarial critique missing.")

        # 4. Deterministic Rules -> Weighted Scoring
        state = await _run_with_timeout(rules_node, state, "rules", project_id)
        state = await _run_with_timeout(scoring_node, state, "scoring", project_id)

        # 5. Concurrent 13-Report Generation
        state = await _run_with_timeout(report_generator_node, state, "report_gen", project_id)

        return state

pipeline_graph = PipelineGraph()
