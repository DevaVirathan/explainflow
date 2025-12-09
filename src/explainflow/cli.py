"""
CLI module for ExplainFlow.

Provides command-line interface using Typer.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def main():
    """Main entry point for CLI."""
    try:
        import typer
    except ImportError:
        print("CLI requires typer. Install with: pip install explainflow[cli]")
        sys.exit(1)
    
    app = typer.Typer(
        name="explainflow",
        help="ExplainFlow - Code Execution Visualizer & Explainer",
        add_completion=False
    )
    
    @app.command()
    def run(
        file: Path = typer.Argument(
            ...,
            help="Python file to explain",
            exists=True,
            readable=True
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output", "-o",
            help="Output file (png, gif, or html)"
        ),
        theme: str = typer.Option(
            "dark",
            "--theme", "-t",
            help="Color theme (dark, light, colorblind)"
        ),
        max_steps: int = typer.Option(
            1000,
            "--max-steps", "-m",
            help="Maximum execution steps"
        ),
        fps: float = typer.Option(
            1.0,
            "--fps",
            help="Frames per second for GIF output"
        ),
        quiet: bool = typer.Option(
            False,
            "--quiet", "-q",
            help="Suppress terminal output"
        ),
        simple: bool = typer.Option(
            False,
            "--simple", "-s",
            help="Use simple output (no colors)"
        )
    ):
        """
        Run and explain a Python file step-by-step.
        
        Examples:
            explainflow run script.py
            explainflow run script.py -o output.png
            explainflow run script.py -o animation.gif --fps 2
            explainflow run script.py -o trace.html
        """
        from explainflow import explain, export_image, export_gif, export_html
        
        # Read the file
        code = file.read_text()
        
        # Determine output mode
        if quiet:
            output_mode = "silent"
        elif simple:
            output_mode = "simple"
        else:
            output_mode = "rich"
        
        # Execute and trace
        typer.echo(f"🔍 Tracing execution of {file.name}...")
        trace = explain(code, output=output_mode, max_steps=max_steps, theme=theme)
        
        # Export if requested
        if output:
            suffix = output.suffix.lower()
            
            if suffix == ".png":
                export_image(trace, str(output), theme=theme)
                typer.echo(f"✅ Exported to {output}")
            elif suffix == ".gif":
                export_gif(trace, str(output), fps=fps, theme=theme)
                typer.echo(f"✅ Exported GIF to {output}")
            elif suffix in (".html", ".htm"):
                export_html(trace, str(output), theme=theme)
                typer.echo(f"✅ Exported HTML to {output}")
            else:
                typer.echo(f"❌ Unknown output format: {suffix}", err=True)
                raise typer.Exit(1)
        
        # Show summary
        if trace.success:
            typer.echo(f"✅ Execution completed: {len(trace.steps)} steps")
        else:
            typer.echo(f"❌ Execution failed: {trace.error_message}", err=True)
            raise typer.Exit(1)
    
    @app.command()
    def explain_code(
        code: str = typer.Argument(
            ...,
            help="Python code string to explain"
        ),
        theme: str = typer.Option(
            "dark",
            "--theme", "-t",
            help="Color theme"
        )
    ):
        """
        Explain a code snippet directly.
        
        Example:
            explainflow explain-code "x = 5; y = 10; print(x + y)"
        """
        from explainflow import explain
        
        # Replace semicolons with newlines for multi-statement code
        code = code.replace("; ", "\n").replace(";", "\n")
        
        explain(code, output="rich", theme=theme)
    
    @app.command()
    def watch(
        file: Path = typer.Argument(
            ...,
            help="Python file to watch",
            exists=True
        ),
        theme: str = typer.Option(
            "dark",
            "--theme", "-t",
            help="Color theme"
        )
    ):
        """
        Watch a file and re-run explanation on changes.
        
        Example:
            explainflow watch script.py
        """
        import time
        from explainflow import explain
        
        typer.echo(f"👀 Watching {file.name} for changes... (Ctrl+C to stop)")
        
        last_mtime = 0
        
        try:
            while True:
                current_mtime = file.stat().st_mtime
                
                if current_mtime != last_mtime:
                    last_mtime = current_mtime
                    
                    # Clear screen
                    typer.clear()
                    typer.echo(f"🔄 File changed, re-running...\n")
                    
                    code = file.read_text()
                    explain(code, output="rich", theme=theme)
                
                time.sleep(0.5)
        except KeyboardInterrupt:
            typer.echo("\n👋 Stopped watching.")
    
    @app.command()
    def version():
        """Show the version of ExplainFlow."""
        from explainflow import __version__
        typer.echo(f"ExplainFlow version {__version__}")
    
    app()


if __name__ == "__main__":
    main()
