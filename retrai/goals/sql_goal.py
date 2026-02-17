"""SQL benchmark goal: run a query and check timing / result correctness."""

from __future__ import annotations

import time
from pathlib import Path

import yaml

from retrai.goals.base import GoalBase, GoalResult

_CONFIG_FILE = ".retrai.yml"


def _load_config(cwd: str) -> dict:
    path = Path(cwd) / _CONFIG_FILE
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


class SqlBenchmarkGoal(GoalBase):
    """Optimise a SQL query to run under a time limit.

    `.retrai.yml`:

    ```yaml
    goal: sql-benchmark
    dsn: "sqlite:///mydb.sqlite"   # SQLAlchemy DSN
    query_file: "query.sql"        # path to the SQL file (relative to cwd)
    # or inline:
    query: "SELECT * FROM orders WHERE ..."
    max_ms: 50                     # milliseconds
    expected_rows: 42              # optional: check row count
    ```
    """

    name = "sql-benchmark"

    async def check(self, state: dict, cwd: str) -> GoalResult:
        try:
            from sqlalchemy import create_engine, text
        except ImportError:
            return GoalResult(
                achieved=False,
                reason="sqlalchemy is not installed. Run: pip install sqlalchemy",
                details={"error": "missing_dependency"},
            )

        cfg = _load_config(cwd)
        dsn = cfg.get("dsn")
        if not dsn:
            return GoalResult(
                achieved=False,
                reason="No 'dsn' configured in .retrai.yml",
                details={"error": "missing_config"},
            )

        # Load query
        query_file = cfg.get("query_file")
        if query_file:
            qpath = Path(cwd) / query_file
            if not qpath.exists():
                return GoalResult(
                    achieved=False,
                    reason=f"Query file not found: {query_file}",
                    details={"error": "file_not_found"},
                )
            query = qpath.read_text()
        else:
            query = cfg.get("query", "SELECT 1")

        max_ms = float(cfg.get("max_ms", 100))
        expected_rows = cfg.get("expected_rows")

        try:
            import asyncio

            def _run_query():
                engine = create_engine(dsn)
                with engine.connect() as conn:
                    start = time.perf_counter()
                    result = conn.execute(text(query))
                    rows = result.fetchall()
                    elapsed_ms = (time.perf_counter() - start) * 1000
                return rows, elapsed_ms

            rows, elapsed_ms = await asyncio.get_event_loop().run_in_executor(None, _run_query)
        except Exception as e:
            return GoalResult(
                achieved=False,
                reason=f"Query execution failed: {e}",
                details={"error": str(e)},
            )

        failures = []
        if elapsed_ms > max_ms:
            failures.append(f"query took {elapsed_ms:.1f}ms (limit: {max_ms}ms)")
        if expected_rows is not None and len(rows) != expected_rows:
            failures.append(f"returned {len(rows)} rows (expected {expected_rows})")

        if failures:
            return GoalResult(
                achieved=False,
                reason="; ".join(failures),
                details={"elapsed_ms": elapsed_ms, "row_count": len(rows), "dsn": dsn},
            )

        return GoalResult(
            achieved=True,
            reason=f"Query completed in {elapsed_ms:.1f}ms (limit: {max_ms}ms), {len(rows)} rows",
            details={"elapsed_ms": elapsed_ms, "row_count": len(rows)},
        )

    def system_prompt(self, cwd: str = ".") -> str:  # type: ignore[override]
        cfg = _load_config(cwd)
        custom = cfg.get("system_prompt", "")
        max_ms = cfg.get("max_ms", 100)
        qfile = cfg.get("query_file", "the SQL query")
        base = (
            f"Your goal is to optimise {qfile} so it executes in under {max_ms}ms.\n\n"
            "Strategy:\n"
            "1. Read the current SQL query.\n"
            "2. Analyse the query plan (EXPLAIN ANALYZE or equivalent).\n"
            "3. Identify bottlenecks: missing indexes, full-table scans, inefficient JOINs.\n"
            "4. Propose targeted changes: add indexes, rewrite the query, add CTEs, etc.\n"
            "5. Write the improved query back to the file.\n"
            "6. Re-run the benchmark to verify improvement.\n"
            "Rules:\n"
            "- Do NOT change the expected result set (same rows, same columns).\n"
            "- You may create indexes (DDL) if needed.\n"
            "- Prefer query rewrites over schema changes.\n"
        )
        return (custom + "\n\n" + base).strip() if custom else base
