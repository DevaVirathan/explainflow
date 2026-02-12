"""Data models for ExplainFlow.

Contains data structures for execution traces.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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
    CONTEXT_ENTER = "context_enter"
    CONTEXT_EXIT = "context_exit"
    YIELD = "yield"
    YIELD_FROM = "yield_from"
    AWAIT = "await"


@dataclass
class HeapObject:
    """Represents an object on the heap with its identity."""

    object_id: int
    type_name: str
    repr_value: str
    value: Any = field(repr=False, default=None)
    ref_count: int = 0
    children: dict[str, int] = field(default_factory=dict)  # attr/key -> object_id

    @classmethod
    def from_value(cls, value: Any) -> HeapObject:
        """Create a HeapObject from a value."""
        obj_id = id(value)
        type_name = type(value).__name__

        try:
            repr_val = repr(value)
            if len(repr_val) > 200:
                repr_val = repr_val[:197] + "..."
        except Exception:
            repr_val = "<repr error>"

        children: dict[str, int] = {}
        try:
            if isinstance(value, dict):
                for k, v in value.items():
                    children[repr(k)] = id(v)
            elif isinstance(value, (list, tuple)):
                for i, v in enumerate(value):
                    children[str(i)] = id(v)
            elif isinstance(value, set):
                for i, v in enumerate(value):
                    children[str(i)] = id(v)
            elif hasattr(value, "__dict__") and not isinstance(value, type):
                for k, v in value.__dict__.items():
                    if not k.startswith("__"):
                        children[k] = id(v)
        except Exception:
            pass

        return cls(
            object_id=obj_id,
            type_name=type_name,
            repr_value=repr_val,
            value=copy.deepcopy(value) if _is_copyable(value) else None,
            children=children,
        )


@dataclass
class StackFrame:
    """Represents a call stack frame."""

    function_name: str
    line_number: int
    local_variables: dict[str, Variable] = field(default_factory=dict)
    arguments: dict[str, str] = field(default_factory=dict)
    return_value: str | None = None


@dataclass
class Variable:
    """Represents a variable at a point in time."""

    name: str
    value: Any
    type_name: str
    repr_value: str
    changed: bool = False
    object_id: int | None = None

    @classmethod
    def from_value(cls, name: str, value: Any, previous_value: Any = None) -> Variable:
        """Create a Variable from a name and value."""
        try:
            repr_val = repr(value)
            if len(repr_val) > 100:
                repr_val = repr_val[:97] + "..."
        except Exception:
            repr_val = "<repr error>"

        # Safer comparison that handles complex objects
        changed = False
        if previous_value is not None:
            try:
                changed = previous_value != value
                # Handle numpy-like objects that return arrays
                if hasattr(changed, "__iter__") and not isinstance(
                    changed,
                    (str, bytes),
                ):
                    changed = True
            except Exception:
                # If comparison fails, assume changed
                changed = True

        return cls(
            name=name,
            value=copy.deepcopy(value) if _is_copyable(value) else value,
            type_name=type(value).__name__,
            repr_value=repr_val,
            changed=changed,
            object_id=id(value),
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
    return_value: Any | None = None
    exception: Exception | None = None
    function_name: str | None = None
    call_depth: int = 0
    explanation: str = ""
    # Enhanced fields
    heap_objects: dict[int, HeapObject] = field(default_factory=dict)
    call_stack: list[StackFrame] = field(default_factory=list)
    loop_iteration: int | None = None
    timestamp: float = 0.0
    duration_ms: float = 0.0

    def get_variable_summary(self) -> str:
        """Get a summary of current variables."""
        if not self.variables:
            return "No variables"

        parts = []
        for var in self.variables.values():
            marker = "→ " if var.changed else "  "
            parts.append(f"{marker}{var.name} = {var.repr_value}")
        return "\n".join(parts)

    def get_heap_summary(self) -> str:
        """Get a summary of heap objects at this step."""
        if not self.heap_objects:
            return "No heap objects"
        parts = []
        for obj in self.heap_objects.values():
            parts.append(f"  id={obj.object_id} {obj.type_name}: {obj.repr_value}")
        return "\n".join(parts)

    def get_call_stack_summary(self) -> str:
        """Get a summary of the call stack at this step."""
        if not self.call_stack:
            return "No call stack"
        parts = []
        for i, frame in enumerate(self.call_stack):
            indent = "  " * i
            parts.append(f"{indent}→ {frame.function_name} (line {frame.line_number})")
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

    def get_step(self, step_number: int) -> ExecutionStep | None:
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

    def get_object_references(self, object_id: int) -> list[tuple[int, str]]:
        """Get all variable names that reference a specific object ID across steps."""
        refs = []
        for step in self.steps:
            for var in step.variables.values():
                if var.object_id == object_id:
                    refs.append((step.step_number, var.name))
        return refs

    def get_shared_references(self, step_number: int) -> dict[int, list[str]]:
        """Find variables sharing the same object at a given step."""
        step = self.get_step(step_number)
        if not step:
            return {}
        id_to_names: dict[int, list[str]] = {}
        for var in step.variables.values():
            if var.object_id is not None:
                if var.object_id not in id_to_names:
                    id_to_names[var.object_id] = []
                id_to_names[var.object_id].append(var.name)
        return {oid: names for oid, names in id_to_names.items() if len(names) > 1}

    def summary(self) -> str:
        """Get a summary of the execution."""
        lines = [
            "Execution Summary",
            "=" * 40,
            f"Total steps: {len(self.steps)}",
            f"Lines in code: {self.total_lines}",
            f"Success: {self.success}",
        ]

        if self.final_output:
            lines.append(f"\nOutput:\n{self.final_output}")

        if not self.success:
            lines.append(f"\nError: {self.error_message}")

        if self.final_variables:
            lines.append("\nFinal Variables:")
            for var in self.final_variables.values():
                lines.append(f"  {var.name} = {var.repr_value} ({var.type_name})")

        return "\n".join(lines)

    def _repr_html_(self) -> str:
        """IPython/Jupyter display integration."""
        from explainflow.exporter import export_html

        result = export_html(self, return_string=True)
        # When return_string=True, export_html returns str
        assert isinstance(result, str)
        return result
