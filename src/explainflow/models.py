"""
Data models for ExplainFlow.

Contains data structures for execution traces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
import copy


class StepType(Enum):
    """Types of execution steps."""
    LINE = "line"
    CALL = "call"
    RETURN = "return"
    EXCEPTION = "exception"
    ASSIGNMENT = "assignment"
    LOOP_START = "loop_start"
    LOOP_ITERATION = "loop_iteration"
    LOOP_END = "loop_end"
    CONDITION = "condition"


@dataclass
class Variable:
    """Represents a variable at a point in time."""
    name: str
    value: Any
    type_name: str
    repr_value: str
    changed: bool = False
    
    @classmethod
    def from_value(cls, name: str, value: Any, previous_value: Any = None) -> "Variable":
        """Create a Variable from a name and value."""
        try:
            repr_val = repr(value)
            if len(repr_val) > 100:
                repr_val = repr_val[:97] + "..."
        except Exception:
            repr_val = "<repr error>"
        
        changed = previous_value is not None and previous_value != value
        
        return cls(
            name=name,
            value=copy.deepcopy(value) if _is_copyable(value) else value,
            type_name=type(value).__name__,
            repr_value=repr_val,
            changed=changed
        )


def _is_copyable(value: Any) -> bool:
    """Check if a value can be deep copied."""
    try:
        copy.deepcopy(value)
        return True
    except Exception:
        return False


@dataclass
class ExecutionStep:
    """Represents a single step in code execution."""
    step_number: int
    line_number: int
    line_content: str
    step_type: StepType
    variables: dict[str, Variable] = field(default_factory=dict)
    output: str = ""
    return_value: Optional[Any] = None
    exception: Optional[Exception] = None
    function_name: Optional[str] = None
    call_depth: int = 0
    explanation: str = ""
    
    def get_variable_summary(self) -> str:
        """Get a summary of current variables."""
        if not self.variables:
            return "No variables"
        
        parts = []
        for var in self.variables.values():
            marker = "→ " if var.changed else "  "
            parts.append(f"{marker}{var.name} = {var.repr_value}")
        return "\n".join(parts)


@dataclass
class ExecutionTrace:
    """Complete trace of code execution."""
    code: str
    steps: list[ExecutionStep] = field(default_factory=list)
    final_output: str = ""
    final_variables: dict[str, Variable] = field(default_factory=dict)
    success: bool = True
    error_message: str = ""
    total_lines: int = 0
    
    def __len__(self) -> int:
        return len(self.steps)
    
    def __iter__(self):
        return iter(self.steps)
    
    def __getitem__(self, index: int) -> ExecutionStep:
        return self.steps[index]
    
    def get_step(self, step_number: int) -> Optional[ExecutionStep]:
        """Get a specific step by number."""
        for step in self.steps:
            if step.step_number == step_number:
                return step
        return None
    
    def get_variable_history(self, variable_name: str) -> list[tuple[int, Variable]]:
        """Get the history of a variable across all steps."""
        history = []
        for step in self.steps:
            if variable_name in step.variables:
                history.append((step.step_number, step.variables[variable_name]))
        return history
    
    def get_lines_executed(self) -> list[int]:
        """Get list of line numbers that were executed."""
        return [step.line_number for step in self.steps]
    
    def summary(self) -> str:
        """Get a summary of the execution."""
        lines = [
            f"Execution Summary",
            f"=" * 40,
            f"Total steps: {len(self.steps)}",
            f"Lines in code: {self.total_lines}",
            f"Success: {self.success}",
        ]
        
        if self.final_output:
            lines.append(f"\nOutput:\n{self.final_output}")
        
        if not self.success:
            lines.append(f"\nError: {self.error_message}")
        
        if self.final_variables:
            lines.append(f"\nFinal Variables:")
            for var in self.final_variables.values():
                lines.append(f"  {var.name} = {var.repr_value} ({var.type_name})")
        
        return "\n".join(lines)
