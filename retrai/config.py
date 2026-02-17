"""Run configuration dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Popular providers and their models for interactive setup
PROVIDER_MODELS: dict[str, dict[str, Any]] = {
    "Anthropic (Claude)": {
        "models": [
            "claude-sonnet-4-6",
            "claude-opus-4",
            "claude-sonnet-4-20250514",
            "claude-haiku-3-5",
        ],
        "env_var": "ANTHROPIC_API_KEY",
    },
    "OpenAI": {
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "o3",
            "o3-mini",
            "o4-mini",
        ],
        "env_var": "OPENAI_API_KEY",
    },
    "Google (Gemini)": {
        "models": [
            "gemini/gemini-2.5-pro",
            "gemini/gemini-2.5-flash",
            "gemini/gemini-2.0-flash",
        ],
        "env_var": "GEMINI_API_KEY",
    },
    "Azure OpenAI": {
        "models": ["azure/gpt-4o", "azure/gpt-4o-mini"],
        "env_var": "AZURE_API_KEY",
        "extra_env": ["AZURE_API_BASE", "AZURE_API_VERSION"],
    },
    "Ollama (local)": {
        "models": [
            "ollama/llama3.1:70b",
            "ollama/qwen2.5-coder:32b",
            "ollama/deepseek-coder-v2",
        ],
        "env_var": None,
        "api_base": "http://localhost:11434",
    },
    "Other (custom)": {
        "models": [],
        "env_var": None,
    },
}


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


def load_config(cwd: str) -> dict[str, Any] | None:
    """Load config from .retrai.yml if it exists, else return None."""
    import yaml

    config_path = Path(cwd) / ".retrai.yml"
    if not config_path.exists():
        return None
    with config_path.open() as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else None

