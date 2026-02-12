"""Tracer module for ExplainFlow.

Handles code execution tracing using sys.settrace.
Supports: breakpoints, call stack tracking, heap/memory diagrams,
loop iteration counting, async/generator/context manager detection,
performance profiling, and multi-file tracing.
"""

from __future__ import annotations

import functools
import io
import linecache
import os
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from types import FrameType
from typing import Any, Callable

from explainflow.models import (
    ExecutionStep,
    ExecutionTrace,
    HeapObject,
    StackFrame,
    StepType,
    Variable,
)


class _MaxStepsError(Exception):
    """Internal exception to stop execution when max steps reached."""

    pass


class Tracer:
    """Traces Python code execution step-by-step.

    Uses sys.settrace to capture each line execution, function calls,
    returns, and exceptions.  Supports breakpoints, heap tracking,
    call-stack capture, loop-iteration counting, performance timing,
    and multi-file tracing.
    """

    def __init__(
        self,
        max_steps: int = 1000,
        breakpoints: set[int] | None = None,
        track_heap: bool = True,
        track_call_stack: bool = True,
        profile: bool = False,
        trace_external: bool = False,
        external_files: set[str] | None = None,
    ):
        """Initialize the tracer.

        Args:
            max_steps: Maximum number of steps to trace (prevents infinite loops)
            breakpoints: Set of line numbers to stop at (None = trace everything)
            track_heap: Whether to capture heap/object diagrams per step
            track_call_stack: Whether to capture call stack per step
            profile: Whether to record per-step timing
            trace_external: Whether to trace code in external (imported) files
            external_files: Set of absolute file paths to also trace
                when trace_external=True
        """
        self.max_steps = max_steps
        self.breakpoints = breakpoints
        self.track_heap = track_heap
        self.track_call_stack = track_call_stack
        self.profile = profile
        self.trace_external = trace_external
        self.external_files: set[str] = external_files or set()

        # Internal state (reset per trace call)
        self.steps: list[ExecutionStep] = []
        self.step_count = 0
        self.code_lines: list[str] = []
        self.previous_variables: dict[str, Any] = {}
        self.current_variables: dict[str, Variable] = {}
        self.output_buffer = io.StringIO()
        self.call_depth = 0
        self.traced_filename = "<explainflow>"
        self._stopped = False
        self._breakpoint_hit = False
        self._loop_counters: dict[int, int] = {}  # line_no -> iteration count
        self._call_stack: list[StackFrame] = []
        self._last_timestamp: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trace(self, code: str) -> ExecutionTrace:
        """Trace the execution of a code string.

        Args:
            code: Python code to trace

        Returns:
            ExecutionTrace containing all steps
        """
        self._reset()
        self.code_lines = code.strip().split("\n")

        # Handle empty code
        if not code.strip():
            return ExecutionTrace(code=code, success=True, total_lines=0)

        exec_namespace = {
            "__name__": "__main__",
            "__doc__": None,
            "__builtins__": __builtins__,
        }

        try:
            compiled = compile(code, self.traced_filename, "exec")
        except SyntaxError as e:
            return ExecutionTrace(
                code=code,
                success=False,
                error_message=f"SyntaxError: {e.msg} (line {e.lineno})",
                total_lines=len(self.code_lines),
            )

        linecache.cache[self.traced_filename] = (
            len(code),
            None,
            self.code_lines,
            self.traced_filename,
        )

        success = True
        error_message = ""

        try:
            with (
                redirect_stdout(self.output_buffer),
                redirect_stderr(self.output_buffer),
            ):
                sys.settrace(self._trace_callback)
                try:
                    exec(compiled, exec_namespace)
                finally:
                    sys.settrace(None)
        except _MaxStepsError:
            sys.settrace(None)
        except Exception as e:
            success = False
            error_message = f"{type(e).__name__}: {str(e)}"
            if self.steps:
                last_step = self.steps[-1]
                self.steps.append(
                    ExecutionStep(
                        step_number=len(self.steps) + 1,
                        line_number=last_step.line_number,
                        line_content=last_step.line_content,
                        step_type=StepType.EXCEPTION,
                        variables=self.current_variables.copy(),
                        exception=e,
                        explanation=f"Exception raised: {error_message}",
                    )
                )

        final_vars = {}
        for name, value in exec_namespace.items():
            if not name.startswith("_"):
                final_vars[name] = Variable.from_value(name, value)

        if self.traced_filename in linecache.cache:
            del linecache.cache[self.traced_filename]

        return ExecutionTrace(
            code=code,
            steps=self.steps,
            final_output=self.output_buffer.getvalue(),
            final_variables=final_vars,
            success=success,
            error_message=error_message,
            total_lines=len(self.code_lines),
        )

    def trace_function(self, func: Callable, *args, **kwargs) -> ExecutionTrace:
        """Trace a function execution with given arguments."""
        import inspect

        source = inspect.getsource(func)
        arg_strs = [repr(a) for a in args]
        kwarg_strs = [f"{k}={repr(v)}" for k, v in kwargs.items()]
        call_args = ", ".join(arg_strs + kwarg_strs)
        code = f"{source}\n\nresult = {func.__name__}({call_args})"
        return self.trace(code)

    def trace_file(self, filepath: str) -> ExecutionTrace:
        """Trace execution of a Python file (multi-file tracing).

        Args:
            filepath: Path to the Python file to trace

        Returns:
            ExecutionTrace of the file execution
        """
        filepath = os.path.abspath(filepath)
        with open(filepath) as f:
            code = f.read()

        if self.trace_external:
            self.external_files.add(filepath)

        return self.trace(code)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reset(self):
        """Reset all internal state for a new trace."""
        self.steps = []
        self.step_count = 0
        self.previous_variables = {}
        self.current_variables = {}
        self.output_buffer = io.StringIO()
        self.call_depth = 0
        self._stopped = False
        self._breakpoint_hit = False
        self._loop_counters = {}
        self._call_stack = []
        self._last_timestamp = time.perf_counter()

    def _should_trace_file(self, filename: str) -> bool:
        """Determine if a given filename should be traced."""
        if filename == self.traced_filename:
            return True
        if self.trace_external and filename in self.external_files:
            return True
        return False

    def _trace_callback(
        self,
        frame: FrameType,
        event: str,
        arg: Any,
    ) -> Callable | None:
        if self._stopped or self.step_count >= self.max_steps:
            self._stopped = True
            raise _MaxStepsError("Maximum trace steps exceeded")

        if not self._should_trace_file(frame.f_code.co_filename):
            return self._trace_callback

        line_no = frame.f_lineno
        if 1 <= line_no <= len(self.code_lines):
            line_content = self.code_lines[line_no - 1]
        else:
            line_content = ""

        # Breakpoint check: if breakpoints set and we're on a 'line' event
        if self.breakpoints and event == "line" and line_no not in self.breakpoints:
            # Still need to track state for when we do hit a breakpoint
            return self._trace_callback

        # Timing
        now = time.perf_counter()
        duration_ms = (now - self._last_timestamp) * 1000 if self.profile else 0.0
        self._last_timestamp = now

        # Determine step type
        step_type = self._classify_event(event, line_content, frame)

        # Update loop counters
        loop_iteration = None
        if step_type in (StepType.LOOP_START, StepType.LOOP_ITERATION):
            self._loop_counters[line_no] = self._loop_counters.get(line_no, 0) + 1
            loop_iteration = self._loop_counters[line_no]

        # Call stack management
        if event == "call":
            self.call_depth += 1
            fname = frame.f_code.co_name
            sf = StackFrame(
                function_name=fname if fname != "<module>" else "<module>",
                line_number=line_no,
            )
            self._call_stack.append(sf)
        elif event == "return":
            self.call_depth = max(0, self.call_depth - 1)
            if self._call_stack:
                ret = repr(arg) if arg is not None else None
                self._call_stack[-1].return_value = ret
                self._call_stack.pop()

        # Capture variables
        variables = self._capture_variables(frame)

        # Update current call stack frame's locals
        if self._call_stack and self.track_call_stack:
            self._call_stack[-1].local_variables = variables.copy()
            self._call_stack[-1].line_number = line_no

        # Heap capture
        heap_objects: dict[int, HeapObject] = {}
        if self.track_heap:
            heap_objects = self._capture_heap(frame)

        explanation = self._generate_explanation(
            step_type,
            line_content,
            variables,
            arg,
        )

        self.step_count += 1
        step = ExecutionStep(
            step_number=self.step_count,
            line_number=line_no,
            line_content=line_content,
            step_type=step_type,
            variables=variables,
            output=self.output_buffer.getvalue(),
            return_value=arg if event == "return" else None,
            function_name=(
                frame.f_code.co_name if frame.f_code.co_name != "<module>" else None
            ),
            call_depth=self.call_depth,
            explanation=explanation,
            heap_objects=heap_objects,
            call_stack=(
                [
                    StackFrame(
                        function_name=sf.function_name,
                        line_number=sf.line_number,
                        local_variables=sf.local_variables.copy(),
                        arguments=sf.arguments.copy(),
                        return_value=sf.return_value,
                    )
                    for sf in self._call_stack
                ]
                if self.track_call_stack
                else []
            ),
            loop_iteration=loop_iteration,
            timestamp=now if self.profile else 0.0,
            duration_ms=duration_ms,
        )

        self.steps.append(step)
        self.current_variables = variables.copy()

        return self._trace_callback

    def _classify_event(
        self,
        event: str,
        line_content: str,
        frame: FrameType,
    ) -> StepType:
        """Classify an event into a StepType."""
        stripped = line_content.strip()

        if event == "call":
            return StepType.CALL
        elif event == "return":
            return StepType.RETURN
        elif event == "exception":
            return StepType.EXCEPTION

        # 'line' event
        if not stripped or stripped.startswith("#"):
            return StepType.LINE

        # Context managers
        if stripped.startswith("with "):
            return StepType.CONTEXT_ENTER

        # Yield / async
        if stripped.startswith("yield ") or stripped == "yield":
            return StepType.YIELD
        if stripped.startswith("yield from "):
            return StepType.YIELD_FROM
        if stripped.startswith("await "):
            return StepType.AWAIT

        # Assignments (including augmented)
        non_assign_ops = ["==", "!=", "<=", ">=", "+=", "-=", "*=", "/="]
        if "=" in stripped and not any(op in stripped for op in non_assign_ops):
            return StepType.ASSIGNMENT
        aug_ops = [
            "+=",
            "-=",
            "*=",
            "/=",
            "//=",
            "%=",
            "**=",
            "&=",
            "|=",
            "^=",
        ]
        if any(op in stripped for op in aug_ops):
            return StepType.ASSIGNMENT

        # Loops
        if stripped.startswith(("for ", "while ")):
            # Check if this is a repeated visit (iteration)
            if self._loop_counters.get(frame.f_lineno, 0) > 0:
                return StepType.LOOP_ITERATION
            return StepType.LOOP_START

        # Conditions
        if stripped.startswith(("if ", "elif ", "else")):
            return StepType.CONDITION

        return StepType.LINE

    def _capture_variables(self, frame: FrameType) -> dict[str, Variable]:
        """Capture current local variables from frame."""
        variables = {}
        for name, value in frame.f_locals.items():
            if name.startswith("_"):
                continue
            if callable(value) and not hasattr(value, "__explainflow_traced__"):
                continue
            previous = self.previous_variables.get(name)
            variables[name] = Variable.from_value(name, value, previous)
        self.previous_variables = {name: var.value for name, var in variables.items()}
        return variables

    def _capture_heap(self, frame: FrameType) -> dict[int, HeapObject]:
        """Build a snapshot of heap objects reachable from local variables."""
        heap: dict[int, HeapObject] = {}
        for name, value in frame.f_locals.items():
            if name.startswith("_"):
                continue
            if callable(value) and not hasattr(value, "__explainflow_traced__"):
                continue
            self._walk_heap(value, heap, depth=0, max_depth=3)
        return heap

    def _walk_heap(
        self,
        value: Any,
        heap: dict[int, HeapObject],
        depth: int,
        max_depth: int,
    ):
        """Recursively walk object graph to build heap snapshot."""
        obj_id = id(value)
        if obj_id in heap or depth > max_depth:
            return
        # Only track "interesting" types
        if isinstance(value, (int, float, str, bool, type(None))):
            return
        try:
            ho = HeapObject.from_value(value)
            heap[obj_id] = ho
            for child_id in ho.children.values():
                # We already have the id; we need the actual object
                # For dicts/lists/sets/objects we already visited them
                pass
        except Exception:
            pass

    def _generate_explanation(
        self,
        step_type: StepType,
        line_content: str,
        variables: dict[str, Variable],
        arg: Any,
    ) -> str:
        stripped = line_content.strip()

        if step_type == StepType.ASSIGNMENT:
            changed = [v for v in variables.values() if v.changed]
            if changed:
                var = changed[0]
                return f"Set {var.name} to {var.repr_value}"
            elif "=" in stripped:
                parts = stripped.split("=", 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    if var_name in variables:
                        return f"Set {var_name} to {variables[var_name].repr_value}"
            return f"Assignment: {stripped}"
        elif step_type == StepType.LOOP_START:
            if stripped.startswith("for "):
                return f"Starting loop: {stripped}"
            return f"Checking loop condition: {stripped}"
        elif step_type == StepType.LOOP_ITERATION:
            max(self._loop_counters.get(0, 1), 1)
            return f"Loop iteration: {stripped}"
        elif step_type == StepType.CONDITION:
            return f"Evaluating condition: {stripped}"
        elif step_type == StepType.CALL:
            return "Calling function"
        elif step_type == StepType.RETURN:
            if arg is not None:
                return f"Returning: {repr(arg)}"
            return "Returning from function"
        elif step_type == StepType.EXCEPTION:
            return f"Exception: {arg}" if arg else "Exception occurred"
        elif step_type == StepType.CONTEXT_ENTER:
            return f"Entering context manager: {stripped}"
        elif step_type == StepType.CONTEXT_EXIT:
            return "Exiting context manager"
        elif step_type == StepType.YIELD:
            return f"Yielding value: {stripped}"
        elif step_type == StepType.YIELD_FROM:
            return f"Yielding from: {stripped}"
        elif step_type == StepType.AWAIT:
            return f"Awaiting: {stripped}"

        return f"Executing: {stripped}" if stripped else "Empty line"


def trace(func: Callable | None = None, *, output: str = "rich", max_steps: int = 1000):
    """Decorator to trace function execution.

    Can be used with or without parentheses:
        @trace
        def my_func(): ...

        @trace(output="simple")
        def my_func(): ...
    """

    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            tracer = Tracer(max_steps=max_steps)
            trace_result = tracer.trace_function(f, *args, **kwargs)

            if output != "silent":
                from explainflow.visualizer import Visualizer

                visualizer = Visualizer()
                if output == "rich":
                    visualizer.display_rich(trace_result)
                else:
                    visualizer.display_simple(trace_result)

            if "result" in trace_result.final_variables:
                return trace_result.final_variables["result"].value
            return None

        wrapper.__explainflow_traced__ = True  # type: ignore[attr-defined]
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
