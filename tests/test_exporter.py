"""
Tests for ExplainFlow exporter module.
"""

import pytest
import tempfile
from pathlib import Path

from explainflow import explain
from explainflow.exporter import export_image, export_gif, export_html


class TestExportImage:
    """Tests for image export functionality."""
    
    def test_export_creates_file(self):
        """Test that export_image creates a PNG file."""
        code = "x = 42"
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"
            result = export_image(trace, str(output_path))
            
            assert result.exists()
            assert result.suffix == ".png"
    
    def test_export_with_theme(self):
        """Test export with different themes."""
        code = "x = 42"
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for theme in ["dark", "light", "colorblind"]:
                output_path = Path(tmpdir) / f"test_{theme}.png"
                result = export_image(trace, str(output_path), theme=theme)
                
                assert result.exists()
    
    def test_export_specific_step(self):
        """Test exporting a specific step."""
        code = """
x = 1
y = 2
z = 3
"""
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "step2.png"
            result = export_image(trace, str(output_path), step=2)
            
            assert result.exists()


class TestExportGif:
    """Tests for GIF export functionality."""
    
    @pytest.mark.slow
    def test_export_creates_gif(self):
        """Test that export_gif creates a GIF file."""
        code = """
x = 1
y = 2
"""
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.gif"
            result = export_gif(trace, str(output_path))
            
            assert result.exists()
            assert result.suffix == ".gif"
    
    @pytest.mark.slow
    def test_export_with_fps(self):
        """Test export with custom FPS."""
        code = "x = 1"
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.gif"
            result = export_gif(trace, str(output_path), fps=2.0)
            
            assert result.exists()


class TestExportHtml:
    """Tests for HTML export functionality."""
    
    def test_export_creates_html(self):
        """Test that export_html creates an HTML file."""
        code = "x = 42"
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            result = export_html(trace, str(output_path))
            
            assert result.exists()
            assert result.suffix == ".html"
    
    def test_html_contains_code(self):
        """Test that HTML contains the source code."""
        code = "magic_number = 42"
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            export_html(trace, str(output_path))
            
            content = output_path.read_text()
            assert "magic_number" in content
            assert "42" in content
    
    def test_html_contains_steps(self):
        """Test that HTML contains step information."""
        code = """
a = 1
b = 2
c = a + b
"""
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            export_html(trace, str(output_path))
            
            content = output_path.read_text()
            # Should have JavaScript with steps data
            assert "const steps" in content
    
    def test_html_interactive_controls(self):
        """Test that HTML has interactive controls."""
        code = "x = 1"
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            export_html(trace, str(output_path))
            
            content = output_path.read_text()
            # Should have navigation buttons
            assert "nextBtn" in content
            assert "prevBtn" in content
            assert "playBtn" in content
    
    def test_html_with_different_themes(self):
        """Test HTML export with different themes."""
        code = "x = 1"
        trace = explain(code, output="silent")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for theme in ["dark", "light", "colorblind"]:
                output_path = Path(tmpdir) / f"test_{theme}.html"
                result = export_html(trace, str(output_path), theme=theme)
                
                assert result.exists()
