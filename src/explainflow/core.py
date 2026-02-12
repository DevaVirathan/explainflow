"""Core module for ExplainFlow.

Contains the main explain() function.
"""

from __future__ import annotations

from typing import Literal

from explainflow.models import ExecutionTrace
from explainflow.tracer import Tracer

OutputMode = Literal["rich", "simple", "silent"]


def explain(
    code: str,
    output: OutputMode = "rich",
    max_steps: int = 1000,
    show_types: bool = True,
    theme: str = "dark",
    breakpoints: list[int] | None = None,
    track_heap: bool = False,
    track_call_stack: bool = True,
    profile: bool = False,
) -> ExecutionTrace:
    """Execute and explain code step-by-step.

    Args:
        code: Python code string to explain
        output: Output mode - "rich" (terminal), "simple" (basic), "silent" (no output)
        max_steps: Maximum execution steps to trace
        show_types: Whether to show variable types
        theme: Color theme ("dark", "light", "colorblind", or custom)
        breakpoints: Optional list of line numbers to pause at
        track_heap: Whether to track heap objects
        track_call_stack: Whether to track the call stack
        profile: Whether to record execution timing per step

    Returns:
        ExecutionTrace object containing all execution steps

    Example:
        >>> trace = explain('''
        ... x = 5
        ... y = 10
        ... result = x + y
        ... ''')
    """
    tracer = Tracer(
        max_steps=max_steps,
        breakpoints=breakpoints,
        track_heap=track_heap,
        track_call_stack=track_call_stack,
        profile=profile,
    )
    trace_result = tracer.trace(code)

    if output != "silent":
        from explainflow.visualizer import Visualizer

        visualizer = Visualizer(theme=theme, show_types=show_types)
        if output == "rich":
            visualizer.display_rich(trace_result)
        else:
            visualizer.display_simple(trace_result)

    return trace_result


def explain_function(func, *args, **kwargs) -> ExecutionTrace:
    """Explain a function execution with given arguments.

    Args:
        func: Function to trace
        *args: Positional arguments to pass to function
        **kwargs: Keyword arguments to pass to function

    Returns:
        ExecutionTrace object
    """
    tracer = Tracer()
    return tracer.trace_function(func, *args, **kwargs)
