"""
Tests for ExplainFlow visualizer module.
"""

import pytest
from io import StringIO
import sys

from explainflow import explain
from explainflow.visualizer import Visualizer, THEMES


class TestThemes:
    """Tests for theme configurations."""
    
    def test_all_themes_exist(self):
        """Test that all expected themes exist."""
        assert "dark" in THEMES
        assert "light" in THEMES
        assert "colorblind" in THEMES
    
    def test_theme_has_required_colors(self):
        """Test that themes have all required color keys."""
        required_keys = [
            "background", "foreground", "line_number", "current_line",
            "variable", "value", "type", "keyword", "string", "number",
            "comment", "changed", "error", "success", "border", "header"
        ]
        
        for theme_name, theme in THEMES.items():
            for key in required_keys:
                assert key in theme, f"Theme '{theme_name}' missing key '{key}'"


class TestVisualizer:
    """Tests for the Visualizer class."""
    
    def test_init_with_default_theme(self):
        """Test initialization with default theme."""
        viz = Visualizer()
        
        assert viz.theme_name == "dark"
        assert viz.show_types is True
    
    def test_init_with_custom_theme(self):
        """Test initialization with custom theme."""
        viz = Visualizer(theme="light")
        
        assert viz.theme_name == "light"
        assert viz.theme == THEMES["light"]
    
    def test_init_with_invalid_theme(self):
        """Test that invalid theme falls back to dark."""
        viz = Visualizer(theme="nonexistent")
        
        assert viz.theme == THEMES["dark"]
    
    def test_display_simple(self):
        """Test simple display output."""
        code = "x = 42"
        trace = explain(code, output="silent")
        
        viz = Visualizer()
        
        # Capture stdout
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        try:
            viz.display_simple(trace)
        finally:
            sys.stdout = old_stdout
        
        output = captured.getvalue()
        
        assert "ExplainFlow" in output
        assert "x = 42" in output or "x" in output
    
    def test_to_frames(self):
        """Test frame generation for export."""
        code = """
x = 1
y = 2
"""
        trace = explain(code, output="silent")
        viz = Visualizer()
        
        frames = viz.to_frames(trace)
        
        assert len(frames) > 0
        assert all("step_number" in f for f in frames)
        assert all("line_number" in f for f in frames)
        assert all("variables" in f for f in frames)
        assert all("code_lines" in f for f in frames)
    
    def test_to_frames_includes_theme(self):
        """Test that frames include theme colors."""
        code = "x = 1"
        trace = explain(code, output="silent")
        viz = Visualizer(theme="light")
        
        frames = viz.to_frames(trace)
        
        assert frames[0]["theme"] == THEMES["light"]


class TestDisplayOutput:
    """Integration tests for display output."""
    
    def test_explain_with_rich_output(self):
        """Test that rich output doesn't crash."""
        code = "x = 42"
        # This should not raise an exception
        try:
            trace = explain(code, output="rich")
            assert trace.success
        except ImportError:
            # Rich not installed, that's fine
            pytest.skip("Rich library not installed")
    
    def test_explain_with_simple_output(self):
        """Test that simple output works."""
        code = "x = 42"
        
        # Capture stdout
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        try:
            trace = explain(code, output="simple")
        finally:
            sys.stdout = old_stdout
        
        assert trace.success
        output = captured.getvalue()
        assert len(output) > 0
    
    def test_explain_with_silent_output(self):
        """Test that silent output produces no output."""
        code = "x = 42"
        
        # Capture stdout
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        
        try:
            trace = explain(code, output="silent")
        finally:
            sys.stdout = old_stdout
        
        assert trace.success
        # Silent should produce no output
        assert captured.getvalue() == ""
