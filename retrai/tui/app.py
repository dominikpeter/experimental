"""Textual TUI for retrAI — with gradient logo and modern layout."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label, RichLog, Static

if TYPE_CHECKING:
    from retrai.config import RunConfig


LOGO_ART = r"""
 ██████╗ ███████╗████████╗██████╗  █████╗ ██╗
 ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║
 ██████╔╝█████╗     ██║   ██████╔╝███████║██║
 ██╔══██╗██╔══╝     ██║   ██╔══██╗██╔══██║██║
 ██║  ██║███████╗   ██║   ██║  ██║██║  ██║██║
 ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝
"""

STATUS_STYLES = {
    "IDLE": ("dim", "○"),
    "RUNNING": ("bold #a78bfa", "◉"),
    "ACHIEVED": ("bold #4ade80", "✓"),
    "FAILED": ("bold #f87171", "✗"),
}

CSS = """
Screen {
    background: #050b1f;
    layers: base overlay;
}

#logo-container {
    width: 100%;
    height: auto;
    align: center middle;
    padding: 1 2;
    border-bottom: heavy #2e1065;
}

#logo-label {
    width: auto;
    text-align: center;
}

#layout {
    width: 100%;
    height: 1fr;
}

#sidebar {
    width: 36;
    height: 100%;
    border-right: heavy #2e1065;
    background: #0f0a2e;
    padding: 1 2;
}

#log-container {
    height: 100%;
    padding: 0 1;
}

#status-title {
    color: #a78bfa;
    text-style: bold;
    margin-bottom: 1;
    text-align: center;
}

.info-row {
    color: #64748b;
    margin-bottom: 0;
    text-style: none;
}

.info-val {
    color: #e2e8f0;
}

#status-badge {
    margin-top: 1;
    margin-bottom: 1;
    text-align: center;
}

#iter-bar {
    width: 100%;
    height: 1;
    background: #1e1b4b;
    margin-bottom: 1;
}

#iter-fill {
    height: 1;
    width: 0%;
    background: $accent;
}

#divider {
    border-top: heavy #2e1065;
    height: 1;
    margin: 1 0;
}

#log-title {
    color: #a78bfa;
    text-style: bold;
    padding: 0 1 1 1;
    border-bottom: heavy #2e1065;
}
"""


def _gradient_logo() -> Text:
    """Return the ASCII logo as a Rich Text with purple→blue gradient."""
    colors = [
        "#c084fc",
        "#b57bf5",
        "#a872ee",
        "#9b69e7",
        "#8e60e0",
        "#7c3aed",
        "#6d28d9",
        "#5b21b6",
        "#4c1d95",
        "#3b1677",
    ]
    text = Text(justify="center")
    lines = LOGO_ART.strip("\n").split("\n")
    for i, line in enumerate(lines):
        color = colors[min(i, len(colors) - 1)]
        text.append(line + "\n", style=f"bold {color}")
    subtitle = Text("  self-solving AI agent loop  ", style="italic #64748b", justify="center")
    text.append_text(subtitle)
    return text


class StatusPanel(Static):
    status: reactive[str] = reactive("IDLE")
    iteration: reactive[int] = reactive(0)

    def __init__(self, cfg: RunConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self._max = cfg.max_iterations

    def compose(self) -> ComposeResult:
        from rich.markup import escape

        yield Label("retrAI", id="status-title")
        yield Label(f"[dim]Goal:[/dim]  {escape(self.cfg.goal)}", classes="info-row")
        yield Label(f"[dim]Model:[/dim] {escape(self.cfg.model_name[:22])}", classes="info-row")
        yield Label(f"[dim]CWD:[/dim]   {escape(self.cfg.cwd[:22])}", classes="info-row")
        yield Label("", id="status-badge")
        yield Label("", id="iter-label", classes="info-row")

    def on_mount(self) -> None:
        self._refresh_badge()

    def watch_status(self, value: str) -> None:
        self._refresh_badge()

    def watch_iteration(self, value: int) -> None:
        pct = min(100, round((value / max(self._max, 1)) * 100))
        try:
            self.query_one("#iter-label", Label).update(
                f"[dim]Iter:[/dim]  [{value}/{self._max}]  [dim]{pct}%[/dim]"
            )
        except Exception:
            pass

    def _refresh_badge(self) -> None:
        style, icon = STATUS_STYLES.get(self.status, ("white", "?"))
        try:
            self.query_one("#status-badge", Label).update(
                f"[{style}] {icon}  {self.status} [{style}]"
            )
        except Exception:
            pass


class RetrAITUI(App):
    """Modern Textual TUI with gradient logo."""

    CSS = CSS
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, cfg: RunConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self._status_panel: StatusPanel | None = None
        self._rich_log: RichLog | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        # Big gradient logo at the top
        logo = Static(_gradient_logo(), id="logo-label")
        yield Container(logo, id="logo-container")
        # Main layout
        with Horizontal(id="layout"):
            with Vertical(id="sidebar"):
                self._status_panel = StatusPanel(self.cfg)
                yield self._status_panel
            with Vertical(id="log-container"):
                yield Label("◈ Event Log", id="log-title")
                self._rich_log = RichLog(highlight=True, markup=True, wrap=True)
                yield self._rich_log
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"retrAI — {self.cfg.goal}"
        self.sub_title = self.cfg.model_name
        self.run_worker(self._run_agent(), exclusive=True)

    async def _run_agent(self) -> None:
        from retrai.agent.graph import build_graph
        from retrai.events.bus import AsyncEventBus
        from retrai.goals.registry import get_goal

        self._write("[bold #a78bfa]▶ Starting agent…[/bold #a78bfa]")

        goal = get_goal(self.cfg.goal)
        bus = AsyncEventBus()
        graph = build_graph(hitl_enabled=self.cfg.hitl_enabled)

        initial_state = {
            "messages": [],
            "pending_tool_calls": [],
            "tool_results": [],
            "goal_achieved": False,
            "goal_reason": "",
            "iteration": 0,
            "max_iterations": self.cfg.max_iterations,
            "hitl_enabled": self.cfg.hitl_enabled,
            "model_name": self.cfg.model_name,
            "cwd": self.cfg.cwd,
            "run_id": self.cfg.run_id,
        }
        run_config = {
            "configurable": {
                "thread_id": self.cfg.run_id,
                "event_bus": bus,
                "goal": goal,
            }
        }

        if self._status_panel:
            self._status_panel.status = "RUNNING"

        q = await bus.subscribe()
        graph_task = asyncio.create_task(graph.ainvoke(initial_state, config=run_config))  # type: ignore[arg-type]

        async def consume() -> None:
            async for event in bus.iter_events(q):
                self._handle_event(event)

        consumer_task = asyncio.create_task(consume())

        try:
            final_state = await graph_task
        except Exception as e:
            self._write(f"[bold red]✗ ERROR: {e}[/bold red]")
            final_state = None
        finally:
            await bus.close()
            await consumer_task

        if final_state:
            achieved = final_state.get("goal_achieved", False)
            if self._status_panel:
                self._status_panel.status = "ACHIEVED" if achieved else "FAILED"
                self._status_panel.iteration = final_state.get("iteration", 0)
            color = "#4ade80" if achieved else "#f87171"
            icon = "✓" if achieved else "✗"
            self._write(
                f"\n[bold {color}]{icon} Run {'ACHIEVED' if achieved else 'FAILED'}[/bold {color}]"
            )

    def _handle_event(self, event) -> None:
        kind = event.kind
        payload = event.payload
        iteration = event.iteration

        if kind == "step_start":
            node = payload.get("node", "?")
            header = (
                f"\n[bold #7c3aed]┌─[/bold #7c3aed]"
                f" [bold #a78bfa]iter {iteration}[/bold #a78bfa]"
                f" [dim #64748b]▸[/dim #64748b]"
                f" [bold #e2e8f0]{node.upper()}[/bold #e2e8f0]"
            )
            self._write(header)
            if self._status_panel:
                self._status_panel.iteration = iteration

        elif kind == "tool_call":
            tool = payload.get("tool", "?")
            args = payload.get("args", {})
            arg_str = str(args)[:70]
            self._write(f"  [#38bdf8]⟶ {tool}[/#38bdf8] [dim]{arg_str}[/dim]")

        elif kind == "tool_result":
            tool = payload.get("tool", "?")
            err = payload.get("error", False)
            content = str(payload.get("content", ""))[:150]
            if err:
                self._write(f"  [#f87171]✗ {tool}[/#f87171] [dim]{content!r}[/dim]")
            else:
                self._write(f"  [#4ade80]✓ {tool}[/#4ade80] [dim]{content!r}[/dim]")

        elif kind == "goal_check":
            achieved = payload.get("achieved", False)
            reason = payload.get("reason", "")
            if achieved:
                self._write(f"  [bold #4ade80]◉ GOAL: {reason}[/bold #4ade80]")
            else:
                self._write(f"  [#fbbf24]◌ {reason}[/#fbbf24]")

        elif kind == "human_check_required":
            self._write("[bold #fb923c]⏸  Human approval required[/bold #fb923c]")

        elif kind == "iteration_complete":
            n = payload.get("iteration", 0)
            self._write(f"[dim #2e1065]└─────────────────────────── iteration {n} ──[/dim #2e1065]")
            if self._status_panel:
                self._status_panel.iteration = n

        elif kind == "run_end":
            status = payload.get("status", "?")
            self._write(f"\n[bold]Run ended: {status}[/bold]")

        elif kind == "error":
            err = payload.get("error", "?")
            self._write(f"[bold #f87171]ERROR: {err}[/bold #f87171]")

    def _write(self, text: str) -> None:
        if self._rich_log:
            self._rich_log.write(text)
