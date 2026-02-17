"""Plan node: calls the LLM and extracts pending tool calls."""

from __future__ import annotations

import inspect
from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from retrai.agent.state import AgentState, ToolCall
from retrai.events.types import AgentEvent
from retrai.llm.factory import get_llm

# Tools available to the agent
TOOL_DEFINITIONS = [
    {
        "name": "bash_exec",
        "description": (
            "Execute a shell command in the project directory. "
            "Use for running tests, installing packages, etc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run"},
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds (default 60)",
                    "default": 60,
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "file_read",
        "description": "Read the contents of a file (path relative to project root)",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to project root"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "file_list",
        "description": "List files and directories at a path relative to project root",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to project root (default '.')",
                    "default": ".",
                }
            },
            "required": [],
        },
    },
    {
        "name": "file_write",
        "description": "Write content to a file (path relative to project root). Creates parent dirs.",  # noqa: E501
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to project root"},
                "content": {"type": "string", "description": "Full file content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_pytest",
        "description": "Run the pytest test suite and return structured results with failures",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


async def plan_node(state: AgentState, config: RunnableConfig) -> dict:
    """Call the LLM to decide next actions."""
    cfg = config.get("configurable", {})
    event_bus = cfg.get("event_bus")
    goal = cfg.get("goal")
    run_id = state["run_id"]
    iteration = state["iteration"]

    if event_bus:
        await event_bus.publish(
            AgentEvent(
                kind="step_start",
                run_id=run_id,
                iteration=iteration,
                payload={"node": "plan", "iteration": iteration},
            )
        )

    llm = get_llm(state["model_name"])

    # Build messages — start with system prompt on first iteration
    messages = list(state["messages"])
    if not messages:
        system_content = _build_system_prompt(goal, state)
        messages = [SystemMessage(content=system_content)]

    # Bind tools to the model
    llm_with_tools = llm.bind_tools(TOOL_DEFINITIONS)  # type: ignore[attr-defined]

    response: AIMessage = await llm_with_tools.ainvoke(messages)

    # Extract tool calls from the response
    pending: list[ToolCall] = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            pending.append(
                ToolCall(
                    id=str(tc.get("id") or ""),
                    name=tc.get("name", ""),
                    args=tc.get("args", {}),
                )
            )

    return {
        "messages": [response],
        "pending_tool_calls": pending,
        "tool_results": [],
    }


def _build_system_prompt(goal: Any, state: AgentState) -> str:
    if goal is None:
        goal_prompt = "Complete the task."
    else:
        sig = inspect.signature(goal.system_prompt)
        if len(sig.parameters) > 0:
            goal_prompt = goal.system_prompt(state.get("cwd", "."))
        else:
            goal_prompt = goal.system_prompt()
    return (
        f"You are retrAI, an autonomous software agent.\n\n"
        f"Project directory: {state['cwd']}\n"
        f"Max iterations: {state['max_iterations']}\n\n"
        f"## Goal\n{goal_prompt}\n\n"
        "## Available Tools\n"
        "- `bash_exec`: run shell commands\n"
        "- `file_read`: read a file\n"
        "- `file_list`: list directory contents\n"
        "- `file_write`: write/overwrite a file\n"
        "- `run_pytest`: run the test suite\n\n"
        "Always think step-by-step. Be methodical and precise."
    )
