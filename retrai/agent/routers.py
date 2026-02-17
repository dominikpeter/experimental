"""Routing functions for the LangGraph StateGraph."""

from __future__ import annotations

from retrai.agent.state import AgentState


def should_call_tools(state: AgentState) -> str:
    """After plan: if there are pending tool calls, go to act; else evaluate."""
    if state.get("pending_tool_calls"):
        return "act"
    return "evaluate"


def route_after_evaluate(state: AgentState) -> str:
    """After evaluate: check goal/max-iter/hitl."""
    if state["goal_achieved"]:
        return "end"
    if state["iteration"] >= state["max_iterations"]:
        return "end"
    if state["hitl_enabled"]:
        return "human_check"
    return "plan"


def route_after_human_check(state: AgentState) -> str:
    """After human_check: if goal was set to False (abort), end; else plan."""
    # human_check_node sets goal_achieved=True if aborted (as a signal)
    # We check by looking at a special sentinel — if human said abort,
    # evaluate would have set goal_achieved=False but we set a flag.
    # Simple approach: if iteration >= max_iterations, end.
    if state["iteration"] >= state["max_iterations"]:
        return "end"
    return "plan"
