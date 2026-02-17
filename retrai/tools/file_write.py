"""Async file write tool (cwd-relative paths)."""

from __future__ import annotations

import asyncio
from pathlib import Path


async def file_write(path: str, content: str, cwd: str) -> str:
    """Write content to a file relative to cwd. Creates parent dirs as needed.

    Returns the resolved path string on success.
    """
    full_path = Path(cwd) / path

    def _write() -> str:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return str(full_path)

    return await asyncio.get_event_loop().run_in_executor(None, _write)
