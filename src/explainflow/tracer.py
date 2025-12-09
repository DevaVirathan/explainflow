"""
Tracer module for ExplainFlow.

Handles code execution tracing using sys.settrace.
"""

from __future__ import annotations

import sys
import io
import linecache
import functools
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Callable, Optional
from types import FrameType

from explainflow.models import ExecutionTrace, ExecutionStep, StepType, Variable


class Tracer:
    """
    Traces Python code execution step-by-step.
    
    Uses sys.settrace to capture each line execution, function calls,
    returns, and exceptions.
    """
    
    def __init__(self, max_steps: int = 1000):
        """
        Initialize the tracer.
        
        Args:
            max_steps: Maximum number of steps to trace (prevents infinite loops)
        """
        self.max_steps = max_steps
        self.steps: list[ExecutionStep] = []
        self.step_count = 0
        self.code_lines: list[str] = []
        self.previous_variables: dict[str, Any] = {}
        self.current_variables: dict[str, Variable] = {}
        self.output_buffer = io.StringIO()
        self.call_depth = 0
        self.traced_filename = "<explainflow>"
        self._stopped = False
        
    def trace(self, code: str) -> ExecutionTrace:
        """
        Trace the execution of code string.
        
        Args:
            code: Python code to trace
            
        Returns:
            ExecutionTrace containing all steps
        """
        self.steps = []
        self.step_count = 0
        self.code_lines = code.strip().split('\n')
        self.previous_variables = {}
        self.current_variables = {}
        self.output_buffer = io.StringIO()
        self.call_depth = 0
        self._stopped = False
        
        # Prepare execution environment
        exec_globals = {
            '__name__': '__main__',
            '__doc__': None,
            '__builtins__': __builtins__,
        }
        exec_locals = {}
        
        # Compile code
        try:
            compiled = compile(code, self.traced_filename, 'exec')
        except SyntaxError as e:
            trace = ExecutionTrace(
                code=code,
                success=False,
                error_message=f"SyntaxError: {e.msg} (line {e.lineno})",
                total_lines=len(self.code_lines)
            )
            return trace
        
        # Add code to linecache for line retrieval
        linecache.cache[self.traced_filename] = (
            len(code),
            None,
            self.code_lines,
            self.traced_filename
        )
        
        success = True
        error_message = ""
        
        try:
            # Capture stdout and trace execution
            with redirect_stdout(self.output_buffer), redirect_stderr(self.output_buffer):
                sys.settrace(self._trace_callback)
                try:
                    exec(compiled, exec_globals, exec_locals)
                finally:
                    sys.settrace(None)
        except Exception as e:
            success = False
            error_message = f"{type(e).__name__}: {str(e)}"
            
            # Add exception step
            if self.steps:
                last_step = self.steps[-1]
                self.steps.append(ExecutionStep(
                    step_number=len(self.steps) + 1,
                    line_number=last_step.line_number,
                    line_content=last_step.line_content,
                    step_type=StepType.EXCEPTION,
                    variables=self.current_variables.copy(),
                    exception=e,
                    explanation=f"Exception raised: {error_message}"
                ))
        
        # Build final variables from exec_locals
        final_vars = {}
        for name, value in exec_locals.items():
            if not name.startswith('_'):
                final_vars[name] = Variable.from_value(name, value)
        
        # Clean up linecache
        if self.traced_filename in linecache.cache:
            del linecache.cache[self.traced_filename]
        
        return ExecutionTrace(
            code=code,
            steps=self.steps,
            final_output=self.output_buffer.getvalue(),
            final_variables=final_vars,
            success=success,
            error_message=error_message,
            total_lines=len(self.code_lines)
        )
    
    def _trace_callback(self, frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
        """
        Callback for sys.settrace.
        
        Args:
            frame: Current execution frame
            event: Event type ('line', 'call', 'return', 'exception')
            arg: Event-specific argument
            
        Returns:
            Self for continued tracing, None to stop
        """
        if self._stopped or self.step_count >= self.max_steps:
            self._stopped = True
            return None
        
        # Only trace our code
        if frame.f_code.co_filename != self.traced_filename:
            return self._trace_callback
        
        line_no = frame.f_lineno
        
        # Get line content safely
        if 1 <= line_no <= len(self.code_lines):
            line_content = self.code_lines[line_no - 1]
        else:
            line_content = ""
        
        # Determine step type
        if event == 'call':
            step_type = StepType.CALL
            self.call_depth += 1
        elif event == 'return':
            step_type = StepType.RETURN
            self.call_depth = max(0, self.call_depth - 1)
        elif event == 'exception':
            step_type = StepType.EXCEPTION
        else:  # 'line'
            step_type = self._determine_line_type(line_content)
        
        # Capture variables
        variables = self._capture_variables(frame)
        
        # Generate explanation
        explanation = self._generate_explanation(step_type, line_content, variables, arg)
        
        self.step_count += 1
        step = ExecutionStep(
            step_number=self.step_count,
            line_number=line_no,
            line_content=line_content,
            step_type=step_type,
            variables=variables,
            output=self.output_buffer.getvalue(),
            return_value=arg if event == 'return' else None,
            function_name=frame.f_code.co_name if frame.f_code.co_name != '<module>' else None,
            call_depth=self.call_depth,
            explanation=explanation
        )
        
        self.steps.append(step)
        self.current_variables = variables.copy()
        
        return self._trace_callback
    
    def _determine_line_type(self, line_content: str) -> StepType:
        """Determine the type of a line based on its content."""
        stripped = line_content.strip()
        
        if not stripped or stripped.startswith('#'):
            return StepType.LINE
        
        if '=' in stripped and not any(op in stripped for op in ['==', '!=', '<=', '>=', '+=', '-=', '*=', '/=']):
            return StepType.ASSIGNMENT
        
        if any(op in stripped for op in ['+=', '-=', '*=', '/=', '//=', '%=', '**=', '&=', '|=', '^=']):
            return StepType.ASSIGNMENT
        
        if stripped.startswith(('for ', 'while ')):
            return StepType.LOOP_START
        
        if stripped.startswith(('if ', 'elif ', 'else')):
            return StepType.CONDITION
        
        return StepType.LINE
    
    def _capture_variables(self, frame: FrameType) -> dict[str, Variable]:
        """Capture current local variables from frame."""
        variables = {}
        
        for name, value in frame.f_locals.items():
            # Skip internal variables
            if name.startswith('_'):
                continue
            
            # Skip modules and functions (unless user-defined in traced code)
            if callable(value) and not hasattr(value, '__explainflow_traced__'):
                continue
            
            previous = self.previous_variables.get(name)
            variables[name] = Variable.from_value(name, value, previous)
        
        # Update previous variables for next comparison
        self.previous_variables = {
            name: var.value for name, var in variables.items()
        }
        
        return variables
    
    def _generate_explanation(
        self,
        step_type: StepType,
        line_content: str,
        variables: dict[str, Variable],
        arg: Any
    ) -> str:
        """Generate a human-readable explanation for a step."""
        stripped = line_content.strip()
        
        if step_type == StepType.ASSIGNMENT:
            # Find changed variables
            changed = [v for v in variables.values() if v.changed]
            if changed:
                var = changed[0]
                return f"Set {var.name} to {var.repr_value}"
            elif '=' in stripped:
                parts = stripped.split('=', 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    if var_name in variables:
                        return f"Set {var_name} to {variables[var_name].repr_value}"
            return f"Assignment: {stripped}"
        
        elif step_type == StepType.LOOP_START:
            if stripped.startswith('for '):
                return f"Starting loop: {stripped}"
            else:
                return f"Checking loop condition: {stripped}"
        
        elif step_type == StepType.CONDITION:
            return f"Evaluating condition: {stripped}"
        
        elif step_type == StepType.CALL:
            return f"Calling function"
        
        elif step_type == StepType.RETURN:
            if arg is not None:
                return f"Returning: {repr(arg)}"
            return "Returning from function"
        
        elif step_type == StepType.EXCEPTION:
            if arg:
                return f"Exception: {arg}"
            return "Exception occurred"
        
        return f"Executing: {stripped}" if stripped else "Empty line"
    
    def trace_function(self, func: Callable, *args, **kwargs) -> ExecutionTrace:
        """
        Trace a function execution.
        
        Args:
            func: Function to trace
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            ExecutionTrace of the function execution
        """
        import inspect
        source = inspect.getsource(func)
        
        # Create call code
        arg_strs = [repr(a) for a in args]
        kwarg_strs = [f"{k}={repr(v)}" for k, v in kwargs.items()]
        call_args = ", ".join(arg_strs + kwarg_strs)
        
        code = f"{source}\n\nresult = {func.__name__}({call_args})"
        return self.trace(code)


def trace(func: Optional[Callable] = None, *, output: str = "rich", max_steps: int = 1000):
    """
    Decorator to trace function execution.
    
    Can be used with or without parentheses:
        @trace
        def my_func(): ...
        
        @trace(output="simple")
        def my_func(): ...
    
    Args:
        func: Function to decorate (when used without parentheses)
        output: Output mode ("rich", "simple", "silent")
        max_steps: Maximum steps to trace
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
            
            # Return the actual function result
            return f(*args, **kwargs)
        
        wrapper.__explainflow_traced__ = True
        return wrapper
    
    # Handle both @trace and @trace() syntax
    if func is not None:
        return decorator(func)
    return decorator
