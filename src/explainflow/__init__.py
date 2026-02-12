"""ExplainFlow - Code Execution Visualizer & Explainer.

Generate step-by-step visual explanations of Python code execution.
"""

__version__ = "1.0.0"
__author__ = "DevaVirathan"

from explainflow.core import explain, explain_function
from explainflow.exporter import (
    export_gif,
    export_html,
    export_image,
    export_markdown,
    export_video,
)
from explainflow.models import (
    ExecutionStep,
    ExecutionTrace,
    HeapObject,
    StackFrame,
    StepType,
    Variable,
)
from explainflow.tracer import Tracer, trace
from explainflow.visualizer import Visualizer, get_theme, register_theme

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
