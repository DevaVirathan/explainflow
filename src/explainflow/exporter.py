"""
Exporter module for ExplainFlow.

Handles exporting execution traces to images, GIFs, videos, and HTML.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from explainflow.core import ExecutionTrace


# Constants for image rendering
DEFAULT_FONT_SIZE = 14
CODE_FONT_SIZE = 13
PADDING = 20
LINE_HEIGHT = 22
CODE_LINE_HEIGHT = 20
HEADER_HEIGHT = 50
VARIABLE_PANEL_WIDTH = 300
MIN_CODE_PANEL_WIDTH = 400


def export_image(
    trace: "ExecutionTrace",
    filename: str,
    theme: str = "dark",
    step: Optional[int] = None,
    width: int = 1200,
    show_all_steps: bool = False
) -> Path:
    """
    Export execution trace as a PNG image.
    
    Args:
        trace: ExecutionTrace to export
        filename: Output filename (should end with .png)
        theme: Color theme ("dark", "light", "colorblind")
        step: Specific step to export (None for final state)
        width: Image width in pixels
        show_all_steps: If True, create a long image with all steps
        
    Returns:
        Path to the created image file
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ImportError("Pillow is required for image export. Install with: pip install pillow")
    
    from explainflow.visualizer import THEMES
    
    colors = THEMES.get(theme, THEMES["dark"])
    
    # Calculate dimensions
    code_lines = trace.code.split('\n')
    num_code_lines = len(code_lines)
    
    if show_all_steps:
        # Show all steps in one tall image
        num_steps = len(trace.steps)
        step_height = 150  # Height per step
        height = HEADER_HEIGHT + (num_code_lines * CODE_LINE_HEIGHT) + (num_steps * step_height) + PADDING * 4
    else:
        # Single step or final state
        height = HEADER_HEIGHT + (num_code_lines * CODE_LINE_HEIGHT) + 300 + PADDING * 3
    
    # Create image
    img = Image.new('RGB', (width, height), colors["background"])
    draw = ImageDraw.Draw(img)
    
    # Try to load a monospace font, fall back to default
    try:
        code_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", CODE_FONT_SIZE)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", DEFAULT_FONT_SIZE)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except (OSError, IOError):
        try:
            # Try macOS fonts
            code_font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", CODE_FONT_SIZE)
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", DEFAULT_FONT_SIZE)
            header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        except (OSError, IOError):
            # Fall back to default
            code_font = ImageFont.load_default()
            font = ImageFont.load_default()
            header_font = ImageFont.load_default()
    
    y_offset = PADDING
    
    # Draw header
    draw.text((PADDING, y_offset), "ExplainFlow - Code Execution Trace", fill=colors["header"], font=header_font)
    y_offset += HEADER_HEIGHT
    
    # Draw code section
    draw.rectangle(
        [(PADDING, y_offset), (width - PADDING, y_offset + num_code_lines * CODE_LINE_HEIGHT + PADDING)],
        outline=colors["border"],
        width=1
    )
    
    code_y = y_offset + PADDING // 2
    
    # Determine which line to highlight
    highlight_line = None
    current_step_data = None
    
    if step is not None and 1 <= step <= len(trace.steps):
        current_step_data = trace.steps[step - 1]
        highlight_line = current_step_data.line_number
    elif trace.steps:
        current_step_data = trace.steps[-1]
        highlight_line = current_step_data.line_number
    
    for i, line in enumerate(code_lines, 1):
        line_y = code_y + (i - 1) * CODE_LINE_HEIGHT
        
        # Highlight current line
        if i == highlight_line:
            draw.rectangle(
                [(PADDING + 1, line_y - 2), (width - PADDING - 1, line_y + CODE_LINE_HEIGHT - 2)],
                fill=colors["current_line"]
            )
        
        # Line number
        draw.text((PADDING + 5, line_y), f"{i:3}", fill=colors["line_number"], font=code_font)
        
        # Code line
        draw.text((PADDING + 50, line_y), line, fill=colors["foreground"], font=code_font)
    
    y_offset += num_code_lines * CODE_LINE_HEIGHT + PADDING * 2
    
    # Draw step info
    if current_step_data:
        _draw_step_info(draw, current_step_data, y_offset, width, colors, font, code_font)
        y_offset += 200
    
    # Draw all steps if requested
    if show_all_steps:
        for step_data in trace.steps:
            _draw_step_info(draw, step_data, y_offset, width, colors, font, code_font)
            y_offset += 150
    
    # Save image
    output_path = Path(filename)
    img.save(output_path, "PNG")
    
    return output_path


def _draw_step_info(draw, step, y_offset: int, width: int, colors: dict, font, code_font) -> None:
    """Draw information about a single step."""
    # Step header
    step_text = f"Step {step.step_number}: {step.step_type.value.upper()}"
    draw.text((PADDING, y_offset), step_text, fill=colors["header"], font=font)
    y_offset += LINE_HEIGHT
    
    # Line info
    line_text = f"Line {step.line_number}: {step.line_content.strip()}"
    draw.text((PADDING, y_offset), line_text, fill=colors["foreground"], font=code_font)
    y_offset += LINE_HEIGHT
    
    # Explanation
    draw.text((PADDING, y_offset), f"→ {step.explanation}", fill=colors["success"], font=font)
    y_offset += LINE_HEIGHT * 1.5
    
    # Variables
    if step.variables:
        draw.text((PADDING, y_offset), "Variables:", fill=colors["comment"], font=font)
        y_offset += LINE_HEIGHT
        
        for var in step.variables.values():
            marker = "⟳ " if var.changed else "  "
            color = colors["changed"] if var.changed else colors["variable"]
            var_text = f"{marker}{var.name} = {var.repr_value} ({var.type_name})"
            draw.text((PADDING + 10, y_offset), var_text, fill=color, font=code_font)
            y_offset += LINE_HEIGHT


def export_gif(
    trace: "ExecutionTrace",
    filename: str,
    fps: float = 1.0,
    theme: str = "dark",
    width: int = 1200,
    loop: bool = True
) -> Path:
    """
    Export execution trace as an animated GIF.
    
    Args:
        trace: ExecutionTrace to export
        filename: Output filename (should end with .gif)
        fps: Frames per second (lower = slower animation)
        theme: Color theme
        width: Image width in pixels
        loop: Whether the GIF should loop
        
    Returns:
        Path to the created GIF file
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow is required for GIF export. Install with: pip install pillow")
    
    # Generate frame for each step
    frames = []
    temp_files = []
    
    for i in range(1, len(trace.steps) + 1):
        temp_filename = f"/tmp/explainflow_frame_{i}.png"
        export_image(trace, temp_filename, theme=theme, step=i, width=width)
        frames.append(Image.open(temp_filename))
        temp_files.append(temp_filename)
    
    if not frames:
        raise ValueError("No steps to export")
    
    # Calculate duration per frame in milliseconds
    duration = int(1000 / fps)
    
    # Save as GIF
    output_path = Path(filename)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0 if loop else 1
    )
    
    # Clean up temp files
    import os
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except OSError:
            pass
    
    return output_path


def export_html(
    trace: "ExecutionTrace",
    filename: str,
    theme: str = "dark",
    interactive: bool = True
) -> Path:
    """
    Export execution trace as an interactive HTML file.
    
    Args:
        trace: ExecutionTrace to export
        filename: Output filename (should end with .html)
        theme: Color theme
        interactive: Whether to include step-through controls
        
    Returns:
        Path to the created HTML file
    """
    from explainflow.visualizer import THEMES
    
    colors = THEMES.get(theme, THEMES["dark"])
    
    # Escape HTML in code
    import html
    code_html = html.escape(trace.code)
    code_lines = trace.code.split('\n')
    
    # Build steps JSON
    steps_data = []
    for step in trace.steps:
        steps_data.append({
            "number": step.step_number,
            "line": step.line_number,
            "type": step.step_type.value,
            "content": step.line_content,
            "explanation": step.explanation,
            "variables": {
                name: {
                    "value": var.repr_value,
                    "type": var.type_name,
                    "changed": var.changed
                }
                for name, var in step.variables.items()
            }
        })
    
    import json
    steps_json = json.dumps(steps_data)
    
    # Build code lines HTML
    code_lines_html = []
    for i, line in enumerate(code_lines, 1):
        escaped_line = html.escape(line) or "&nbsp;"
        code_lines_html.append(f'<div class="code-line" data-line="{i}"><span class="line-number">{i}</span><span class="line-content">{escaped_line}</span></div>')
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ExplainFlow - Code Execution Trace</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {colors["background"]};
            color: {colors["foreground"]};
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 20px;
            border-bottom: 1px solid {colors["border"]};
            margin-bottom: 20px;
        }}
        .header h1 {{ color: {colors["header"]}; }}
        .main {{ display: flex; gap: 20px; }}
        .code-panel {{
            flex: 1;
            background: {colors["background"]};
            border: 1px solid {colors["border"]};
            border-radius: 8px;
            padding: 15px;
        }}
        .code-line {{
            display: flex;
            padding: 2px 0;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 14px;
        }}
        .code-line.active {{
            background: {colors["current_line"]};
            border-radius: 4px;
        }}
        .line-number {{
            color: {colors["line_number"]};
            width: 40px;
            text-align: right;
            padding-right: 15px;
            user-select: none;
        }}
        .line-content {{ flex: 1; white-space: pre; }}
        .info-panel {{
            width: 350px;
            background: {colors["background"]};
            border: 1px solid {colors["border"]};
            border-radius: 8px;
            padding: 15px;
        }}
        .step-info {{ margin-bottom: 20px; }}
        .step-header {{
            color: {colors["header"]};
            font-size: 18px;
            margin-bottom: 10px;
        }}
        .step-type {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            background: {colors["border"]};
            margin-left: 10px;
        }}
        .explanation {{
            color: {colors["success"]};
            margin: 10px 0;
            padding: 10px;
            background: rgba(78, 201, 176, 0.1);
            border-radius: 4px;
        }}
        .variables {{ margin-top: 15px; }}
        .variable {{
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            padding: 3px 0;
        }}
        .variable.changed {{ color: {colors["changed"]}; }}
        .variable .name {{ color: {colors["variable"]}; }}
        .variable .value {{ color: {colors["value"]}; }}
        .variable .type {{ color: {colors["type"]}; font-size: 11px; }}
        .controls {{
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 20px;
            padding: 15px;
            background: {colors["border"]};
            border-radius: 8px;
        }}
        .controls button {{
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            background: {colors["header"]};
            color: white;
        }}
        .controls button:hover {{ opacity: 0.9; }}
        .controls button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .step-counter {{ 
            font-size: 16px; 
            padding: 10px;
            min-width: 100px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 ExplainFlow</h1>
            <p>Code Execution Trace</p>
        </div>
        
        <div class="main">
            <div class="code-panel">
                <h3 style="margin-bottom: 15px;">Source Code</h3>
                {''.join(code_lines_html)}
            </div>
            
            <div class="info-panel">
                <div class="step-info">
                    <div class="step-header">
                        Step <span id="stepNum">1</span>
                        <span class="step-type" id="stepType">LINE</span>
                    </div>
                    <div id="lineInfo" style="color: {colors["comment"]}; margin: 5px 0;"></div>
                    <div class="explanation" id="explanation"></div>
                </div>
                
                <div class="variables">
                    <h4>Variables</h4>
                    <div id="variablesList"></div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button id="firstBtn">⏮ First</button>
            <button id="prevBtn">◀ Previous</button>
            <span class="step-counter"><span id="currentStep">1</span> / <span id="totalSteps">{len(trace.steps)}</span></span>
            <button id="nextBtn">Next ▶</button>
            <button id="lastBtn">Last ⏭</button>
            <button id="playBtn">▶ Play</button>
        </div>
    </div>
    
    <script>
        const steps = {steps_json};
        let currentStep = 0;
        let playing = false;
        let playInterval = null;
        
        function updateDisplay() {{
            const step = steps[currentStep];
            if (!step) return;
            
            // Update step info
            document.getElementById('stepNum').textContent = step.number;
            document.getElementById('stepType').textContent = step.type.toUpperCase();
            document.getElementById('lineInfo').textContent = 'Line ' + step.line + ': ' + step.content.trim();
            document.getElementById('explanation').textContent = '→ ' + step.explanation;
            document.getElementById('currentStep').textContent = currentStep + 1;
            
            // Highlight current line
            document.querySelectorAll('.code-line').forEach(el => el.classList.remove('active'));
            const activeLine = document.querySelector('.code-line[data-line="' + step.line + '"]');
            if (activeLine) activeLine.classList.add('active');
            
            // Update variables
            const varsList = document.getElementById('variablesList');
            varsList.innerHTML = '';
            for (const [name, info] of Object.entries(step.variables)) {{
                const div = document.createElement('div');
                div.className = 'variable' + (info.changed ? ' changed' : '');
                div.innerHTML = (info.changed ? '⟳ ' : '&nbsp;&nbsp;') +
                    '<span class="name">' + name + '</span> = ' +
                    '<span class="value">' + info.value + '</span> ' +
                    '<span class="type">(' + info.type + ')</span>';
                varsList.appendChild(div);
            }}
            
            // Update buttons
            document.getElementById('firstBtn').disabled = currentStep === 0;
            document.getElementById('prevBtn').disabled = currentStep === 0;
            document.getElementById('nextBtn').disabled = currentStep === steps.length - 1;
            document.getElementById('lastBtn').disabled = currentStep === steps.length - 1;
        }}
        
        function goTo(stepIndex) {{
            currentStep = Math.max(0, Math.min(steps.length - 1, stepIndex));
            updateDisplay();
        }}
        
        function togglePlay() {{
            playing = !playing;
            document.getElementById('playBtn').textContent = playing ? '⏸ Pause' : '▶ Play';
            
            if (playing) {{
                playInterval = setInterval(() => {{
                    if (currentStep < steps.length - 1) {{
                        goTo(currentStep + 1);
                    }} else {{
                        togglePlay();
                    }}
                }}, 1500);
            }} else {{
                clearInterval(playInterval);
            }}
        }}
        
        document.getElementById('firstBtn').onclick = () => goTo(0);
        document.getElementById('prevBtn').onclick = () => goTo(currentStep - 1);
        document.getElementById('nextBtn').onclick = () => goTo(currentStep + 1);
        document.getElementById('lastBtn').onclick = () => goTo(steps.length - 1);
        document.getElementById('playBtn').onclick = togglePlay;
        
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowLeft') goTo(currentStep - 1);
            if (e.key === 'ArrowRight') goTo(currentStep + 1);
            if (e.key === ' ') {{ e.preventDefault(); togglePlay(); }}
        }});
        
        // Initial display
        document.getElementById('totalSteps').textContent = steps.length;
        updateDisplay();
    </script>
</body>
</html>
"""
    
    output_path = Path(filename)
    output_path.write_text(html_content)
    
    return output_path
