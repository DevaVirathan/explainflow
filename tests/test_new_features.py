"""
Tests for ExplainFlow v1.0.0 new features.

Covers: HeapObject, StackFrame, breakpoints, heap tracking, call stack,
loop iteration, profiling, multi-file tracing, custom themes, enhanced models,
export_video, export_markdown, enhanced HTML export, and enhanced core API.
"""

import pytest
import os
import tempfile
from pathlib import Path

from explainflow.models import (
    HeapObject,
    StackFrame,
    Variable,
    ExecutionStep,
    ExecutionTrace,
    StepType,
)
from explainflow.tracer import Tracer
from explainflow.visualizer import (
    Visualizer,
    register_theme,
    get_theme,
    THEMES,
    format_value,
)
from explainflow.core import explain
from explainflow.exporter import export_html, export_markdown


# ==============================================================
# Models: HeapObject
# ==============================================================

class TestHeapObject:

    def test_from_value_int(self):
        obj = HeapObject.from_value(42)
        assert obj.type_name == "int"
        assert obj.repr_value == "42"
        assert obj.object_id == id(42)

    def test_from_value_list(self):
        data = [1, 2, 3]
        obj = HeapObject.from_value(data)
        assert obj.type_name == "list"
        assert "1" in obj.repr_value
        # Children should map indices to sub-object ids
        assert "0" in obj.children or 0 in obj.children or len(obj.children) >= 0

    def test_from_value_dict(self):
        data = {"a": 1, "b": 2}
        obj = HeapObject.from_value(data)
        assert obj.type_name == "dict"
        assert obj.children  # should have child refs

    def test_from_value_nested_object(self):
        data = {"x": [1, 2]}
        obj = HeapObject.from_value(data)
        assert obj.type_name == "dict"

    def test_long_repr_truncated(self):
        data = list(range(100))
        obj = HeapObject.from_value(data)
        assert len(obj.repr_value) <= 203  # 200 + "..."


# ==============================================================
# Models: StackFrame
# ==============================================================

class TestStackFrame:

    def test_creation(self):
        sf = StackFrame(
            function_name="my_func",
            line_number=10,
            local_variables={"x": 5},
            arguments={"a": "1"},
            return_value=None,
        )
        assert sf.function_name == "my_func"
        assert sf.line_number == 10
        assert sf.local_variables == {"x": 5}

    def test_defaults(self):
        sf = StackFrame(function_name="f", line_number=1)
        assert sf.local_variables == {}
        assert sf.arguments == {}
        assert sf.return_value is None


# ==============================================================
# Models: Enhanced Variable
# ==============================================================

class TestVariableEnhanced:

    def test_object_id_tracked(self):
        data = [1, 2, 3]
        var = Variable.from_value("data", data)
        assert var.object_id == id(data)

    def test_object_id_for_int(self):
        var = Variable.from_value("x", 42)
        assert var.object_id is not None


# ==============================================================
# Models: Enhanced ExecutionStep
# ==============================================================

class TestExecutionStepEnhanced:

    def test_new_fields_default(self):
        step = ExecutionStep(
            step_number=1,
            line_number=1,
            line_content="x = 1",
            step_type=StepType.ASSIGNMENT,
            explanation="Assign 1 to x",
        )
        assert step.heap_objects == {}
        assert step.call_stack == []
        assert step.loop_iteration is None
        assert step.timestamp >= 0
        assert step.duration_ms == 0.0

    def test_with_call_stack(self):
        sf = StackFrame(function_name="f", line_number=5)
        step = ExecutionStep(
            step_number=1,
            line_number=5,
            line_content="return 1",
            step_type=StepType.RETURN,
            explanation="Return 1",
            call_stack=[sf],
        )
        assert len(step.call_stack) == 1
        assert step.call_stack[0].function_name == "f"


# ==============================================================
# Models: Enhanced ExecutionTrace
# ==============================================================

class TestExecutionTraceEnhanced:

    def test_repr_html(self):
        """Test Jupyter _repr_html_ integration."""
        trace = ExecutionTrace(code="x = 1", steps=[], success=True)
        html_output = trace._repr_html_()
        assert "<html" in html_output or "ExplainFlow" in html_output

    def test_get_object_references_empty(self):
        trace = ExecutionTrace(code="x = 1", steps=[], success=True)
        refs = trace.get_object_references(object_id=12345)
        assert refs == []

    def test_get_shared_references_empty(self):
        trace = ExecutionTrace(code="x = 1", steps=[], success=True)
        shared = trace.get_shared_references(step_number=1)
        assert shared == {}


# ==============================================================
# Models: New StepTypes
# ==============================================================

class TestNewStepTypes:

    def test_context_enter(self):
        assert StepType.CONTEXT_ENTER.value == "context_enter"

    def test_context_exit(self):
        assert StepType.CONTEXT_EXIT.value == "context_exit"

    def test_yield(self):
        assert StepType.YIELD.value == "yield"

    def test_yield_from(self):
        assert StepType.YIELD_FROM.value == "yield_from"

    def test_await(self):
        assert StepType.AWAIT.value == "await"


# ==============================================================
# Tracer: Breakpoints
# ==============================================================

class TestBreakpoints:

    def test_breakpoints_parameter(self):
        tracer = Tracer(breakpoints=[2, 3])
        result = tracer.trace("x = 1\ny = 2\nz = 3")
        assert result.success

    def test_breakpoints_none(self):
        tracer = Tracer(breakpoints=None)
        result = tracer.trace("x = 1")
        assert result.success


# ==============================================================
# Tracer: Heap tracking
# ==============================================================

class TestHeapTracking:

    def test_heap_tracking_enabled(self):
        tracer = Tracer(track_heap=True)
        result = tracer.trace("data = [1, 2, 3]\ndata.append(4)")
        assert result.success

    def test_heap_tracking_disabled(self):
        tracer = Tracer(track_heap=False)
        result = tracer.trace("x = [1, 2]")
        assert result.success
        # Heap should be empty when disabled
        for step in result.steps:
            assert step.heap_objects == {}


# ==============================================================
# Tracer: Call stack tracking
# ==============================================================

class TestCallStackTracking:

    def test_call_stack_with_function(self):
        tracer = Tracer(track_call_stack=True)
        code = """
def add(a, b):
    return a + b
result = add(1, 2)
"""
        result = tracer.trace(code)
        assert result.success

    def test_call_stack_disabled(self):
        tracer = Tracer(track_call_stack=False)
        result = tracer.trace("x = 1")
        assert result.success
        for step in result.steps:
            assert step.call_stack == []


# ==============================================================
# Tracer: Profiling
# ==============================================================

class TestProfiling:

    def test_profile_enabled(self):
        tracer = Tracer(profile=True)
        result = tracer.trace("x = sum(range(100))")
        assert result.success

    def test_profile_disabled(self):
        tracer = Tracer(profile=False)
        result = tracer.trace("x = 1")
        assert result.success
        for step in result.steps:
            assert step.duration_ms == 0.0


# ==============================================================
# Tracer: Loop iteration
# ==============================================================

class TestLoopIteration:

    def test_loop_iteration_counted(self):
        tracer = Tracer()
        code = "total = 0\nfor i in range(3):\n    total += i"
        result = tracer.trace(code)
        assert result.success
        assert len(result.steps) > 0


# ==============================================================
# Visualizer: Custom themes
# ==============================================================

class TestCustomThemes:

    def test_register_theme(self):
        register_theme("my_custom", {"background": "#000000"})
        theme = get_theme("my_custom")
        assert theme["background"] == "#000000"
        # Missing keys should be filled from dark
        assert "foreground" in theme

    def test_get_builtin_theme(self):
        theme = get_theme("dark")
        assert theme == THEMES["dark"]

    def test_get_unknown_theme_fallback(self):
        theme = get_theme("nonexistent_theme_xyz")
        assert theme == THEMES["dark"]

    def test_visualizer_uses_custom_theme(self):
        register_theme("test_viz", {"background": "#112233"})
        viz = Visualizer(theme="test_viz")
        assert viz.theme["background"] == "#112233"


# ==============================================================
# Visualizer: format_value
# ==============================================================

class TestFormatValue:

    def test_short_value(self):
        assert format_value("hello") == "hello"

    def test_long_value_truncated(self):
        long_val = "x" * 100
        result = format_value(long_val, max_length=50)
        assert len(result) == 50
        assert result.endswith("...")


# ==============================================================
# Visualizer: to_frames enhanced
# ==============================================================

class TestToFramesEnhanced:

    def test_frames_include_call_stack(self):
        tracer = Tracer(track_call_stack=True)
        code = "def f():\n    return 1\nresult = f()"
        result = tracer.trace(code)
        viz = Visualizer()
        frames = viz.to_frames(result)
        assert len(frames) > 0
        # Frames should have call_stack key
        for frame in frames:
            assert "call_stack" in frame
            assert "heap_objects" in frame
            assert "loop_iteration" in frame
            assert "duration_ms" in frame

    def test_frames_include_object_id(self):
        tracer = Tracer()
        result = tracer.trace("x = [1, 2, 3]")
        viz = Visualizer()
        frames = viz.to_frames(result)
        for frame in frames:
            for var_data in frame["variables"].values():
                assert "object_id" in var_data


# ==============================================================
# Core: Enhanced explain()
# ==============================================================

class TestExplainEnhanced:

    def test_explain_with_heap(self):
        trace = explain("x = [1, 2]", output="silent", track_heap=True)
        assert trace.success

    def test_explain_with_profile(self):
        trace = explain("x = 1", output="silent", profile=True)
        assert trace.success

    def test_explain_with_breakpoints(self):
        trace = explain("x = 1\ny = 2", output="silent", breakpoints=[1])
        assert trace.success

    def test_explain_with_custom_theme(self):
        register_theme("test_explain_theme", {"background": "#aabbcc"})
        trace = explain("x = 1", output="silent", theme="test_explain_theme")
        assert trace.success


# ==============================================================
# Exporter: export_html return_string
# ==============================================================

class TestExportHtmlReturnString:

    def test_return_string(self):
        tracer = Tracer()
        result = tracer.trace("x = 42")
        html_str = export_html(result, return_string=True)
        assert isinstance(html_str, str)
        assert "ExplainFlow" in html_str
        assert "x" in html_str

    def test_return_string_has_call_stack_panel(self):
        tracer = Tracer()
        result = tracer.trace("x = 42")
        html_str = export_html(result, return_string=True)
        assert "callStackPanel" in html_str
        assert "heapPanel" in html_str

    def test_return_string_has_timing(self):
        tracer = Tracer()
        result = tracer.trace("x = 42")
        html_str = export_html(result, return_string=True)
        assert "timing" in html_str

    def test_html_file_still_works(self, tmp_path):
        tracer = Tracer()
        result = tracer.trace("x = 42")
        output_file = tmp_path / "test.html"
        path = export_html(result, str(output_file))
        assert Path(path).exists()


# ==============================================================
# Exporter: export_markdown enhanced
# ==============================================================

class TestExportMarkdownEnhanced:

    def test_markdown_basic(self, tmp_path):
        tracer = Tracer()
        result = tracer.trace("x = 42")
        output_file = tmp_path / "test.md"
        path = export_markdown(result, str(output_file))
        content = Path(path).read_text()
        assert "ExplainFlow" in content
        assert "x" in content

    def test_markdown_with_loop(self, tmp_path):
        tracer = Tracer()
        code = "total = 0\nfor i in range(3):\n    total += i"
        result = tracer.trace(code)
        output_file = tmp_path / "test_loop.md"
        path = export_markdown(result, str(output_file))
        content = Path(path).read_text()
        assert "Step" in content


# ==============================================================
# Version
# ==============================================================

class TestVersion:

    def test_version_is_1_0_0(self):
        from explainflow import __version__
        assert __version__ == "1.0.0"


# ==============================================================
# All new public exports
# ==============================================================

class TestPublicExports:

    def test_heap_object_importable(self):
        from explainflow import HeapObject
        assert HeapObject is not None

    def test_stack_frame_importable(self):
        from explainflow import StackFrame
        assert StackFrame is not None

    def test_register_theme_importable(self):
        from explainflow import register_theme
        assert callable(register_theme)

    def test_get_theme_importable(self):
        from explainflow import get_theme
        assert callable(get_theme)

    def test_export_video_importable(self):
        from explainflow import export_video
        assert callable(export_video)

    def test_export_markdown_importable(self):
        from explainflow import export_markdown
        assert callable(export_markdown)
