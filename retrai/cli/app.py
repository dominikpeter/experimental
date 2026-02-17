"""Typer CLI for retrAI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()
app = typer.Typer(
    name="retrai",
    help="Self-solving AI agent loop. Run a goal, watch it fix itself.",
    add_completion=False,
    no_args_is_help=True,
)


@app.command()
def run(
    goal: str = typer.Argument(..., help="Goal to achieve (e.g. 'pytest')"),
    cwd: str = typer.Option(".", "--cwd", "-C", help="Project directory (default: current dir)"),
    model: str = typer.Option(
        "claude-sonnet-4-6", "--model", "-m", help="LLM model name (LiteLLM format)"
    ),
    max_iter: int = typer.Option(20, "--max-iter", "-n", help="Maximum agent iterations"),
    hitl: bool = typer.Option(False, "--hitl", help="Enable human-in-the-loop checkpoints"),
) -> None:
    """Run an agent goal loop in the terminal."""
    from retrai.config import RunConfig
    from retrai.goals.registry import list_goals

    # Validate goal
    available = list_goals()
    if goal not in available:
        console.print(f"[red]Unknown goal: '{goal}'. Available: {', '.join(available)}[/red]")
        raise typer.Exit(code=1)

    resolved_cwd = str(Path(cwd).resolve())
    cfg = RunConfig(
        goal=goal,
        cwd=resolved_cwd,
        model_name=model,
        max_iterations=max_iter,
        hitl_enabled=hitl,
    )

    console.print(
        Panel(
            Text.from_markup(
                f"[bold cyan]retrAI[/bold cyan]  [dim]—[/dim]  goal=[bold]{goal}[/bold]  "
                f"model=[bold]{model}[/bold]  max-iter=[bold]{max_iter}[/bold]  "
                f"hitl=[bold]{'on' if hitl else 'off'}[/bold]\n"
                f"[dim]cwd: {resolved_cwd}[/dim]"
            ),
            border_style="cyan",
        )
    )

    exit_code = asyncio.run(_run_cli(cfg))
    raise typer.Exit(code=exit_code)


async def _run_cli(cfg) -> int:
    """Run the agent loop and stream events to the terminal."""
    from retrai.agent.graph import build_graph
    from retrai.events.bus import AsyncEventBus
    from retrai.goals.registry import get_goal

    goal = get_goal(cfg.goal)
    bus = AsyncEventBus()
    graph = build_graph(hitl_enabled=cfg.hitl_enabled)

    initial_state = {
        "messages": [],
        "pending_tool_calls": [],
        "tool_results": [],
        "goal_achieved": False,
        "goal_reason": "",
        "iteration": 0,
        "max_iterations": cfg.max_iterations,
        "hitl_enabled": cfg.hitl_enabled,
        "model_name": cfg.model_name,
        "cwd": cfg.cwd,
        "run_id": cfg.run_id,
    }

    run_config = {
        "configurable": {
            "thread_id": cfg.run_id,
            "event_bus": bus,
            "goal": goal,
        }
    }

    q = await bus.subscribe()

    # Run graph and consume events concurrently
    graph_task = asyncio.create_task(graph.ainvoke(initial_state, config=run_config))  # type: ignore[arg-type]
    final_state = None
    exit_code = 1

    async def consume_events() -> None:
        nonlocal exit_code
        async for event in bus.iter_events(q):
            _render_event(event)
            if event.kind == "run_end":
                payload = event.payload
                if payload.get("status") == "achieved":
                    exit_code = 0

    consumer_task = asyncio.create_task(consume_events())

    try:
        final_state = await graph_task
    except Exception as e:
        console.print(f"\n[red]Run failed: {e}[/red]")
    finally:
        await bus.close()
        await consumer_task

    if final_state:
        achieved = final_state.get("goal_achieved", False)
        reason = final_state.get("goal_reason", "")
        iters = final_state.get("iteration", 0)
        if achieved:
            console.print(
                Panel(
                    f"[bold green]GOAL ACHIEVED[/bold green] after {iters} iteration(s)\n{reason}",
                    border_style="green",
                )
            )
            exit_code = 0
        else:
            console.print(
                Panel(
                    f"[bold red]GOAL NOT ACHIEVED[/bold red] after {iters} iteration(s)\n{reason}",
                    border_style="red",
                )
            )
            exit_code = 1

    return exit_code


def _render_event(event) -> None:
    """Render an AgentEvent to the terminal."""
    kind = event.kind
    payload = event.payload
    iteration = event.iteration

    if kind == "step_start":
        node = payload.get("node", "?")
        console.print(f"\n[bold blue]▶ [{iteration}] {node.upper()}[/bold blue]")

    elif kind == "tool_call":
        tool = payload.get("tool", "?")
        args = payload.get("args", {})
        args_str = _fmt_args(args)
        console.print(f"  [cyan]⟶ {tool}[/cyan]({args_str})")

    elif kind == "tool_result":
        tool = payload.get("tool", "?")
        err = payload.get("error", False)
        content = payload.get("content", "")[:200]
        color = "red" if err else "green"
        icon = "✗" if err else "✓"
        console.print(f"  [{color}]{icon} {tool}[/{color}]: {content!r}")

    elif kind == "goal_check":
        achieved = payload.get("achieved", False)
        reason = payload.get("reason", "")
        color = "green" if achieved else "yellow"
        icon = "✓" if achieved else "…"
        console.print(f"  [{color}]{icon} Goal: {reason}[/{color}]")

    elif kind == "human_check_required":
        console.print("\n[bold yellow]⏸  Human check required[/bold yellow]")
        console.print("  [dim]Use 'retrai serve' and the web UI to approve/abort.[/dim]")

    elif kind == "iteration_complete":
        iteration = payload.get("iteration", 0)
        console.print(f"  [dim]--- iteration {iteration} complete ---[/dim]")

    elif kind == "run_end":
        status = payload.get("status", "?")
        console.print(f"\n[bold]Run ended: {status}[/bold]")

    elif kind == "error":
        err = payload.get("error", "unknown error")
        console.print(f"\n[bold red]ERROR: {err}[/bold red]")


def _fmt_args(args: dict) -> str:
    parts = []
    for k, v in args.items():
        v_str = repr(v) if not isinstance(v, str) else repr(v[:80])
        parts.append(f"{k}={v_str}")
    return ", ".join(parts)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (dev mode)"),
) -> None:
    """Start the retrAI web dashboard (FastAPI + Vue)."""
    import uvicorn

    console.print(
        Panel(
            f"[bold cyan]retrAI server[/bold cyan] starting on [bold]http://{host}:{port}[/bold]",
            border_style="cyan",
        )
    )
    uvicorn.run(
        "retrai.server.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@app.command()
def tui(
    goal: str = typer.Argument(..., help="Goal to run in the TUI"),
    cwd: str = typer.Option(".", "--cwd", "-C", help="Project directory"),
    model: str = typer.Option("claude-sonnet-4-6", "--model", "-m", help="LLM model"),
    max_iter: int = typer.Option(20, "--max-iter", "-n", help="Max iterations"),
) -> None:
    """Launch the interactive Textual TUI."""
    from retrai.config import RunConfig
    from retrai.tui.app import RetrAITUI

    resolved_cwd = str(Path(cwd).resolve())
    cfg = RunConfig(goal=goal, cwd=resolved_cwd, model_name=model, max_iterations=max_iter)
    tui_app = RetrAITUI(cfg=cfg)
    tui_app.run()
