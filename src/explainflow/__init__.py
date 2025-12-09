"""
ExplainFlow - Code Execution Visualizer & Explainer

Generate step-by-step visual explanations of Python code execution.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from explainflow.models import ExecutionTrace, ExecutionStep, StepType, Variable
from explainflow.core import explain, explain_function
from explainflow.tracer import Tracer, trace
from explainflow.visualizer import Visualizer
from explainflow.exporter import export_image, export_gif, export_html

__all__ = [
    "explain",
    "explain_function",
    "trace",
    "Tracer",
    "Visualizer",
    "ExecutionTrace",
    "ExecutionStep",
    "StepType",
    "Variable",
    "export_image",
    "export_gif",
    "export_html",
]
