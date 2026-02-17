# retrAI Project Memory

## Stack & Tooling
- **Frontend**: Vue 3 + Vite — use **bun** (not npm/pnpm) for installs and scripts
- **Backend**: Python 3.14, uv for dependency management
- **Docs**: MkDocs Material with purple→dark-blue gradient theme

## Key Preferences
- Purple-to-dark-blue gradient aesthetic throughout (TUI logo, Vue dashboard, MkDocs)
- Modern, sleek UI — clean panels, glassmorphism cards, minimal clutter
- Goal system is generic: pytest, shell-goal, perf-check, sql-benchmark + YAML config

## Project Structure
- `retrai/` — Python package
- `frontend/` — Vue 3 app (bun)
- `docs/` — MkDocs site

## Important File Paths
- `retrai/goals/registry.py` — add new goals here
- `retrai/agent/nodes/plan.py` — tool definitions and system prompt
- `frontend/src/style.css` — global CSS variables (colors)
- `docs/stylesheets/extra.css` — MkDocs custom theme

## Dev Commands
- `uv run retrai run pytest` — run CLI
- `cd frontend && bun run dev` — frontend dev server (proxies /api → :8000)
- `uv run retrai serve` — FastAPI server on :8000
- `mkdocs serve` — docs dev server
