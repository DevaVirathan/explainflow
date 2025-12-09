"""
Visualizer module for ExplainFlow.

Handles displaying execution traces in various formats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from explainflow.core import ExecutionTrace, ExecutionStep

# Theme definitions
THEMES = {
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


class Visualizer:
    """
    Visualizes execution traces in the terminal or as data for export.
    """
    
    def __init__(self, theme: str = "dark", show_types: bool = True):
        """
        Initialize the visualizer.
        
        Args:
            theme: Color theme name ("dark", "light", "colorblind")
            show_types: Whether to show variable types
        """
        self.theme_name = theme
        self.theme = THEMES.get(theme, THEMES["dark"])
        self.show_types = show_types
    
    def display_rich(self, trace: "ExecutionTrace") -> None:
        """
        Display trace using Rich library for beautiful terminal output.
        
        Args:
            trace: ExecutionTrace to display
        """
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table
            from rich.syntax import Syntax
            from rich.text import Text
            from rich.columns import Columns
            from rich import box
        except ImportError:
            print("Rich library not installed. Using simple output.")
            self.display_simple(trace)
            return
        
        console = Console()
        
        # Title
        console.print()
        console.print(Panel.fit(
            "[bold blue]ExplainFlow[/bold blue] - Code Execution Trace",
            border_style="blue"
        ))
        console.print()
        
        # Show the code with syntax highlighting
        console.print(Panel(
            Syntax(trace.code, "python", theme="monokai", line_numbers=True),
            title="[bold]Source Code[/bold]",
            border_style="dim"
        ))
        console.print()
        
        # Show each step
        for step in trace.steps:
            self._display_step_rich(console, step, trace)
        
        # Final summary
        self._display_summary_rich(console, trace)
    
    def _display_step_rich(self, console, step: "ExecutionStep", trace: "ExecutionTrace") -> None:
        """Display a single step using Rich."""
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
        from rich import box
        
        # Step header
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
        }
        
        color = step_type_colors.get(step.step_type.value, "white")
        
        # Create step panel content
        content = Text()
        
        # Line info
        content.append(f"Line {step.line_number}: ", style="dim")
        content.append(step.line_content.strip(), style="bold white")
        content.append("\n\n")
        
        # Explanation
        content.append("→ ", style=f"bold {color}")
        content.append(step.explanation, style=color)
        
        # Variables table if any
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
                var_text.append(var.repr_value, style="green")
                
                if self.show_types:
                    var_text.append(f" ({var.type_name})", style="dim italic")
                var_text.append("\n")
            
            content.append_text(var_text)
        
        # Create panel
        panel = Panel(
            content,
            title=f"[bold]Step {step.step_number}[/bold] [{color}]{step.step_type.value.upper()}[/{color}]",
            border_style=color,
            box=box.ROUNDED
        )
        
        console.print(panel)
    
    def _display_summary_rich(self, console, trace: "ExecutionTrace") -> None:
        """Display final summary using Rich."""
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        
        console.print()
        
        # Output
        if trace.final_output:
            console.print(Panel(
                trace.final_output.rstrip(),
                title="[bold]Program Output[/bold]",
                border_style="green"
            ))
        
        # Final variables
        if trace.final_variables:
            table = Table(title="Final Variables", box=box.SIMPLE)
            table.add_column("Name", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Type", style="dim")
            
            for var in trace.final_variables.values():
                table.add_row(var.name, var.repr_value, var.type_name)
            
            console.print(table)
        
        # Status
        if trace.success:
            console.print(f"\n[bold green]✓ Execution completed successfully[/bold green]")
        else:
            console.print(f"\n[bold red]✗ Execution failed: {trace.error_message}[/bold red]")
        
        console.print(f"[dim]Total steps: {len(trace.steps)}[/dim]\n")
    
    def display_simple(self, trace: "ExecutionTrace") -> None:
        """
        Display trace using simple print statements.
        
        Args:
            trace: ExecutionTrace to display
        """
        print("\n" + "=" * 60)
        print("ExplainFlow - Code Execution Trace")
        print("=" * 60)
        
        print("\nSource Code:")
        print("-" * 40)
        for i, line in enumerate(trace.code.split('\n'), 1):
            print(f"{i:3} | {line}")
        print("-" * 40)
        print()
        
        for step in trace.steps:
            self._display_step_simple(step)
        
        self._display_summary_simple(trace)
    
    def _display_step_simple(self, step: "ExecutionStep") -> None:
        """Display a single step using print."""
        print(f"\n[Step {step.step_number}] {step.step_type.value.upper()}")
        print(f"  Line {step.line_number}: {step.line_content.strip()}")
        print(f"  → {step.explanation}")
        
        if step.variables:
            print("  Variables:")
            for var in step.variables.values():
                marker = "⟳" if var.changed else " "
                type_info = f" ({var.type_name})" if self.show_types else ""
                print(f"    {marker} {var.name} = {var.repr_value}{type_info}")
    
    def _display_summary_simple(self, trace: "ExecutionTrace") -> None:
        """Display final summary using print."""
        print("\n" + "=" * 60)
        
        if trace.final_output:
            print("\nProgram Output:")
            print("-" * 40)
            print(trace.final_output.rstrip())
            print("-" * 40)
        
        if trace.final_variables:
            print("\nFinal Variables:")
            for var in trace.final_variables.values():
                print(f"  {var.name} = {var.repr_value} ({var.type_name})")
        
        if trace.success:
            print("\n✓ Execution completed successfully")
        else:
            print(f"\n✗ Execution failed: {trace.error_message}")
        
        print(f"Total steps: {len(trace.steps)}")
        print("=" * 60 + "\n")
    
    def to_frames(self, trace: "ExecutionTrace") -> list[dict]:
        """
        Convert trace to frame data for export.
        
        Args:
            trace: ExecutionTrace to convert
            
        Returns:
            List of frame dictionaries suitable for image/video generation
        """
        frames = []
        
        for step in trace.steps:
            frame = {
                "step_number": step.step_number,
                "line_number": step.line_number,
                "line_content": step.line_content,
                "step_type": step.step_type.value,
                "explanation": step.explanation,
                "variables": {
                    name: {
                        "value": var.repr_value,
                        "type": var.type_name,
                        "changed": var.changed
                    }
                    for name, var in step.variables.items()
                },
                "code_lines": trace.code.split('\n'),
                "theme": self.theme,
            }
            frames.append(frame)
        
        return frames


def format_value(value: str, max_length: int = 50) -> str:
    """Format a value string for display, truncating if necessary."""
    if len(value) > max_length:
        return value[:max_length - 3] + "..."
    return value
