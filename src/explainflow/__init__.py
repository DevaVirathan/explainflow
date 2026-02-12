"""
ExplainFlow - Code Execution Visualizer & Explainer

Generate step-by-step visual explanations of Python code execution.
"""

__version__ = "1.0.0"
__author__ = "DevaVirathan"

from explainflow.models import (
    ExecutionTrace,
    ExecutionStep,
    StepType,
    Variable,
    HeapObject,
    StackFrame,
)
from explainflow.core import explain, explain_function
from explainflow.tracer import Tracer, trace
from explainflow.visualizer import Visualizer, register_theme, get_theme
from explainflow.exporter import (
    export_image,
    export_gif,
    export_html,
    export_video,
    export_markdown,
)

__all__ = [
    # Core API
    "explain",
    "explain_function",
    # Tracer
    "trace",
    "Tracer",
    # Visualizer
    "Visualizer",
    "register_theme",
    "get_theme",
    # Models
    "ExecutionTrace",
    "ExecutionStep",
    "StepType",
    "Variable",
    "HeapObject",
    "StackFrame",
    # Exporters
    "export_image",
    "export_gif",
    "export_html",
    "export_video",
    "export_markdown",
]
