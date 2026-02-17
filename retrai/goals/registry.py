"""Goal registry: maps goal name strings to GoalBase instances."""

from __future__ import annotations

from retrai.goals.base import GoalBase
from retrai.goals.perf_goal import PerfCheckGoal
from retrai.goals.pytest_goal import PytestGoal
from retrai.goals.shell_goal import ShellGoal
from retrai.goals.sql_goal import SqlBenchmarkGoal

_REGISTRY: dict[str, GoalBase] = {
    "pytest": PytestGoal(),
    "shell-goal": ShellGoal(),
    "perf-check": PerfCheckGoal(),
    "sql-benchmark": SqlBenchmarkGoal(),
}


def get_goal(name: str) -> GoalBase:
    """Return a goal by name, raising KeyError if not found."""
    if name not in _REGISTRY:
        available = ", ".join(_REGISTRY.keys())
        raise KeyError(f"Unknown goal: '{name}'. Available: {available}")
    return _REGISTRY[name]


def list_goals() -> list[str]:
    return list(_REGISTRY.keys())
