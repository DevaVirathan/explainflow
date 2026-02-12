"""Visualizer module for ExplainFlow.

Handles displaying execution traces in various formats.
Supports: call stack display, heap/memory diagrams, data structure
visualization, loop iteration counters, performance timing, and custom themes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from explainflow.models import ExecutionStep, ExecutionTrace

# Built-in theme definitions
THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "background": "#1e1e1e",
        "foreground": "#d4d4d4",
        "line_number": "#858585",
        "current_line": "#264f78",
        "variable": "#9cdcfe",
        "value": "#ce9178",
        "type": "#4ec9b0",
        "keyword": "#569cd6",
        "string": "#ce9178",
        "number": "#b5cea8",
        "comment": "#6a9955",
        "changed": "#dcdcaa",
        "error": "#f44747",
        "success": "#4ec9b0",
        "border": "#3c3c3c",
        "header": "#569cd6",
    },
    "light": {
        "background": "#ffffff",
        "foreground": "#1e1e1e",
        "line_number": "#858585",
        "current_line": "#fff3cd",
        "variable": "#001080",
        "value": "#a31515",
        "type": "#267f99",
        "keyword": "#0000ff",
        "string": "#a31515",
        "number": "#098658",
        "comment": "#008000",
        "changed": "#795e26",
        "error": "#d73a49",
        "success": "#22863a",
        "border": "#d4d4d4",
        "header": "#0000ff",
    },
    "colorblind": {
        "background": "#1e1e1e",
        "foreground": "#d4d4d4",
        "line_number": "#858585",
        "current_line": "#3d5a80",
        "variable": "#98c1d9",
        "value": "#ee6c4d",
        "type": "#e0fbfc",
        "keyword": "#98c1d9",
        "string": "#ee6c4d",
        "number": "#e0fbfc",
        "comment": "#858585",
        "changed": "#ffd166",
        "error": "#ef476f",
        "success": "#06d6a0",
        "border": "#3c3c3c",
        "header": "#98c1d9",
    },
}

# Registry for user-defined custom themes
_custom_themes: dict[str, dict[str, str]] = {}


def register_theme(name: str, colors: dict[str, str]) -> None:
    """Register a custom color theme.

    Args:
        name: Theme name
        colors: Dictionary of color key -> hex color value.
                Must contain at least the keys in the "dark" theme.
    """
    required = set(THEMES["dark"].keys())
    missing = required - set(colors.keys())
    if missing:
        # Fill missing keys from dark theme
        full = dict(THEMES["dark"])
        full.update(colors)
        colors = full
    _custom_themes[name] = colors


def get_theme(name: str) -> dict[str, str]:
    """Retrieve a theme by name (built-in or custom)."""
    if name in _custom_themes:
        return _custom_themes[name]
    return THEMES.get(name, THEMES["dark"])


class Visualizer:
    """Visualizes execution traces in the terminal or as data for export."""

    def __init__(self, theme: str = "dark", show_types: bool = True):
        self.theme_name = theme
        self.theme = get_theme(theme)
        self.show_types = show_types

    # ------------------------------------------------------------------
    # Rich display
    # ------------------------------------------------------------------

    def display_rich(self, trace: ExecutionTrace) -> None:
        """Display trace using Rich library for beautiful terminal output."""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.syntax import Syntax
        except ImportError:
            print("Rich library not installed. Using simple output.")
            self.display_simple(trace)
            return

        console = Console()

        # Title
        console.print()
        console.print(
            Panel.fit(
                "[bold blue]ExplainFlow[/bold blue] - Code Execution Trace",
                border_style="blue",
            )
        )
        console.print()

        # Source code
        console.print(
            Panel(
                Syntax(trace.code, "python", theme="monokai", line_numbers=True),
                title="[bold]Source Code[/bold]",
                border_style="dim",
            )
        )
        console.print()

        # Steps
        for step in trace.steps:
            self._display_step_rich(console, step, trace)

        # Summary
        self._display_summary_rich(console, trace)

    def _display_step_rich(
        self,
        console,
        step: ExecutionStep,
        trace: ExecutionTrace,
    ) -> None:
        from rich import box
        from rich.panel import Panel
        from rich.text import Text

        step_type_colors = {
            "line": "white",
            "assignment": "yellow",
            "call": "cyan",
            "return": "magenta",
            "exception": "red",
            "loop_start": "green",
            "loop_iteration": "green",
            "loop_end": "green",
            "condition": "blue",
            "context_enter": "cyan",
            "context_exit": "cyan",
            "yield": "bright_magenta",
            "yield_from": "bright_magenta",
            "await": "bright_cyan",
        }

        color = step_type_colors.get(step.step_type.value, "white")

        content = Text()

        # Line info
        content.append(f"Line {step.line_number}: ", style="dim")
        content.append(step.line_content.strip(), style="bold white")
        content.append("\n\n")

        # Explanation
        content.append("→ ", style=f"bold {color}")
        content.append(step.explanation, style=color)

        # Loop iteration badge
        if step.loop_iteration is not None:
            content.append(f"  [iter {step.loop_iteration}]", style="bold green")

        # Performance timing
        if step.duration_ms > 0:
            content.append(f"  ({step.duration_ms:.2f}ms)", style="dim italic")

        # Variables
        if step.variables:
            content.append("\n\n")
            var_text = Text()
            var_text.append("Variables:\n", style="dim")
            for var in step.variables.values():
                if var.changed:
                    var_text.append("  ⟳ ", style="yellow")
                else:
                    var_text.append("    ", style="dim")
                var_text.append(var.name, style="cyan")
                var_text.append(" = ", style="dim")
                # Enhanced data structure display
                formatted = _format_rich_value(
                    var.repr_value,
                    var.type_name,
                )
                var_text.append(formatted, style="green")
                if self.show_types:
                    var_text.append(f" ({var.type_name})", style="dim italic")
                if var.object_id is not None:
                    var_text.append(f" @{var.object_id}", style="dim")
                var_text.append("\n")
            content.append_text(var_text)

        # Call stack
        if step.call_stack:
            content.append("\n")
            stack_text = Text()
            stack_text.append("Call Stack:\n", style="dim")
            for i, frame in enumerate(step.call_stack):
                indent = "  " * (i + 1)
                stack_text.append(f"{indent}↳ ", style="cyan")
                stack_text.append(frame.function_name, style="bold cyan")
                stack_text.append(f" (line {frame.line_number})", style="dim")
                if frame.return_value is not None:
                    stack_text.append(f" → {frame.return_value}", style="magenta")
                stack_text.append("\n")
            content.append_text(stack_text)

        # Heap objects
        if step.heap_objects:
            content.append("\n")
            heap_text = Text()
            heap_text.append("Heap Objects:\n", style="dim")
            for obj in step.heap_objects.values():
                heap_text.append("  📦 ", style="yellow")
                heap_text.append(f"{obj.type_name}", style="bold")
                heap_text.append(f" @{obj.object_id}", style="dim")
                heap_text.append(f" = {_truncate(obj.repr_value, 60)}", style="green")
                if obj.children:
                    heap_text.append(f" [{len(obj.children)} refs]", style="dim italic")
                heap_text.append("\n")
            content.append_text(heap_text)

        step_label = step.step_type.value.upper()
        title = (
            f"[bold]Step {step.step_number}[/bold]" f" [{color}]{step_label}[/{color}]"
        )
        panel = Panel(
            content,
            title=title,
            border_style=color,
            box=box.ROUNDED,
        )
        console.print(panel)

    def _display_summary_rich(self, console, trace: ExecutionTrace) -> None:
        from rich import box
        from rich.panel import Panel
        from rich.table import Table

        console.print()

        if trace.final_output:
            console.print(
                Panel(
                    trace.final_output.rstrip(),
                    title="[bold]Program Output[/bold]",
                    border_style="green",
                )
            )

        if trace.final_variables:
            table = Table(title="Final Variables", box=box.SIMPLE)
            table.add_column("Name", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Type", style="dim")
            table.add_column("Object ID", style="dim")
            for var in trace.final_variables.values():
                table.add_row(
                    var.name,
                    var.repr_value,
                    var.type_name,
                    str(var.object_id) if var.object_id else "",
                )
            console.print(table)

        # Shared references
        if trace.steps:
            shared = trace.get_shared_references(trace.steps[-1].step_number)
            if shared:
                console.print("\n[bold yellow]Shared Object References:[/bold yellow]")
                for oid, names in shared.items():
                    console.print(f"  @{oid} ← {', '.join(names)}")

        if trace.success:
            console.print(
                "\n[bold green]✓ Execution completed" " successfully[/bold green]",
            )
        else:
            console.print(
                f"\n[bold red]✗ Execution failed:" f" {trace.error_message}[/bold red]",
            )

        console.print(f"[dim]Total steps: {len(trace.steps)}[/dim]\n")

    # ------------------------------------------------------------------
    # Simple display
    # ------------------------------------------------------------------

    def display_simple(self, trace: ExecutionTrace) -> None:
        """Display trace using plain-text output (no Rich dependency)."""
        print("\n" + "=" * 60)
        print("ExplainFlow - Code Execution Trace")
        print("=" * 60)

        print("\nSource Code:")
        print("-" * 40)
        for i, line in enumerate(trace.code.split("\n"), 1):
            print(f"{i:3} | {line}")
        print("-" * 40)
        print()

        for step in trace.steps:
            self._display_step_simple(step)

        self._display_summary_simple(trace)

    def _display_step_simple(self, step: ExecutionStep) -> None:
        header = f"\n[Step {step.step_number}] {step.step_type.value.upper()}"
        if step.loop_iteration is not None:
            header += f" (iter {step.loop_iteration})"
        if step.duration_ms > 0:
            header += f" [{step.duration_ms:.2f}ms]"
        print(header)
        print(f"  Line {step.line_number}: {step.line_content.strip()}")
        print(f"  → {step.explanation}")

        if step.variables:
            print("  Variables:")
            for var in step.variables.values():
                marker = "⟳" if var.changed else " "
                type_info = f" ({var.type_name})" if self.show_types else ""
                oid = f" @{var.object_id}" if var.object_id else ""
                print(f"    {marker} {var.name} = {var.repr_value}{type_info}{oid}")

        if step.call_stack:
            print("  Call Stack:")
            for i, frame in enumerate(step.call_stack):
                indent = "    " + "  " * i
                rv = f" → {frame.return_value}" if frame.return_value else ""
                print(f"{indent}↳ {frame.function_name} (line {frame.line_number}){rv}")

        if step.heap_objects:
            print("  Heap:")
            for obj in step.heap_objects.values():
                children = f" [{len(obj.children)} refs]" if obj.children else ""
                val = _truncate(obj.repr_value, 50)
                print(f"    📦 {obj.type_name}" f" @{obj.object_id} = {val}{children}")

    def _display_summary_simple(self, trace: ExecutionTrace) -> None:
        print("\n" + "=" * 60)

        if trace.final_output:
            print("\nProgram Output:")
            print("-" * 40)
            print(trace.final_output.rstrip())
            print("-" * 40)

        if trace.final_variables:
            print("\nFinal Variables:")
            for var in trace.final_variables.values():
                oid = f" @{var.object_id}" if var.object_id else ""
                print(f"  {var.name} = {var.repr_value} ({var.type_name}){oid}")

        if trace.success:
            print("\n✓ Execution completed successfully")
        else:
            print(f"\n✗ Execution failed: {trace.error_message}")

        print(f"Total steps: {len(trace.steps)}")
        print("=" * 60 + "\n")

    # ------------------------------------------------------------------
    # Frame data for export
    # ------------------------------------------------------------------

    def to_frames(self, trace: ExecutionTrace) -> list[dict]:
        """Convert execution trace steps into serializable frame dicts."""
        frames = []
        for step in trace.steps:
            frame: dict[str, Any] = {
                "step_number": step.step_number,
                "line_number": step.line_number,
                "line_content": step.line_content,
                "step_type": step.step_type.value,
                "explanation": step.explanation,
                "variables": {
                    name: {
                        "value": var.repr_value,
                        "type": var.type_name,
                        "changed": var.changed,
                        "object_id": var.object_id,
                    }
                    for name, var in step.variables.items()
                },
                "code_lines": trace.code.split("\n"),
                "theme": self.theme,
                "call_stack": [
                    {
                        "function": sf.function_name,
                        "line": sf.line_number,
                        "return_value": sf.return_value,
                    }
                    for sf in step.call_stack
                ],
                "heap_objects": {
                    str(oid): {
                        "type": obj.type_name,
                        "repr": obj.repr_value,
                        "children": obj.children,
                    }
                    for oid, obj in step.heap_objects.items()
                },
                "loop_iteration": step.loop_iteration,
                "duration_ms": step.duration_ms,
            }
            frames.append(frame)
        return frames


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _truncate(value: str, max_length: int = 50) -> str:
    if len(value) > max_length:
        return value[: max_length - 3] + "..."
    return value


def _format_rich_value(repr_value: str, type_name: str) -> str:
    """Format a value for rich display with enhanced data structure hints."""
    if type_name == "list" and repr_value.startswith("["):
        try:
            items = repr_value.strip("[]").split(", ")
            if len(items) > 8:
                return f"[{', '.join(items[:6])}, ... +{len(items)-6} more]"
        except Exception:
            pass
    elif type_name == "dict" and repr_value.startswith("{"):
        try:
            if len(repr_value) > 60:
                return repr_value[:57] + "..."
        except Exception:
            pass
    return repr_value


def format_value(value: str, max_length: int = 50) -> str:
    """Format a value string for display, truncating if necessary."""
    return _truncate(value, max_length)
