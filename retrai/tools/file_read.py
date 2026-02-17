"""Async file read tool (cwd-relative paths)."""

from __future__ import annotations

import asyncio
from pathlib import Path


async def file_read(path: str, cwd: str, max_bytes: int = 200_000) -> str:
    """Read a file relative to cwd. Returns content as string.

    Truncates to max_bytes to avoid overwhelming the LLM context.
    """
    full_path = Path(cwd) / path

    def _read() -> str:
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path} (resolved: {full_path})")
        if not full_path.is_file():
            raise IsADirectoryError(f"Path is a directory: {path}")
        raw = full_path.read_bytes()
        text = raw[:max_bytes].decode("utf-8", errors="replace")
        if len(raw) > max_bytes:
            text += f"\n\n[... truncated at {max_bytes} bytes ...]"
        return text

    return await asyncio.get_event_loop().run_in_executor(None, _read)


async def file_list(path: str, cwd: str) -> list[str]:
    """List files/directories at path relative to cwd."""
    full_path = Path(cwd) / path

    def _list() -> list[str]:
        if not full_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        if full_path.is_file():
            return [str(full_path.relative_to(cwd))]
        entries = []
        for p in sorted(full_path.iterdir()):
            rel = str(p.relative_to(Path(cwd)))
            suffix = "/" if p.is_dir() else ""
            entries.append(rel + suffix)
        return entries

    return await asyncio.get_event_loop().run_in_executor(None, _list)
