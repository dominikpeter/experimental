"""Run configuration dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunConfig:
    """Configuration for a single agent run."""

    goal: str
    cwd: str = field(default_factory=lambda: str(Path.cwd()))
    model_name: str = "claude-sonnet-4-6"
    max_iterations: int = 20
    hitl_enabled: bool = False
    run_id: str = ""

    def __post_init__(self) -> None:
        if not self.run_id:
            import uuid

            self.run_id = str(uuid.uuid4())
        # Resolve to absolute path
        self.cwd = str(Path(self.cwd).resolve())
