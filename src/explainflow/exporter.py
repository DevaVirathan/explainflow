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
            try:
                # Try Windows fonts
                code_font = ImageFont.truetype("consola.ttf", CODE_FONT_SIZE)
                font = ImageFont.truetype("arial.ttf", DEFAULT_FONT_SIZE)
                header_font = ImageFont.truetype("arialbd.ttf", 18)
            except (OSError, IOError):
                try:
                    # Try Windows full path fonts
                    import os
                    windir = os.environ.get("WINDIR", r"C:\Windows")
                    fonts_dir = os.path.join(windir, "Fonts")
                    code_font = ImageFont.truetype(os.path.join(fonts_dir, "consola.ttf"), CODE_FONT_SIZE)
                    font = ImageFont.truetype(os.path.join(fonts_dir, "arial.ttf"), DEFAULT_FONT_SIZE)
                    header_font = ImageFont.truetype(os.path.join(fonts_dir, "arialbd.ttf"), 18)
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
    
    import os
    import tempfile
    
    for i in range(1, len(trace.steps) + 1):
        temp_filename = os.path.join(tempfile.gettempdir(), f"explainflow_frame_{i}.png")
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
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except OSError:
            pass
    
    return output_path


def export_video(
    trace: "ExecutionTrace",
    filename: str,
    fps: float = 1.0,
    theme: str = "dark",
    width: int = 1200,
) -> Path:
    """
    Export execution trace as an MP4 video.
    
    Args:
        trace: ExecutionTrace to export
        filename: Output filename (should end with .mp4)
        fps: Frames per second (lower = slower animation)
        theme: Color theme
        width: Image width in pixels
        
    Returns:
        Path to the created video file
    """
    try:
        import imageio.v3 as iio
    except ImportError:
        raise ImportError(
            "imageio is required for video export. "
            "Install with: pip install explainflow[video]"
        )
    
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow is required for video export. Install with: pip install pillow")
    
    import numpy as np
    import os
    import tempfile
    
    # Generate frames as numpy arrays
    frames = []
    temp_files = []
    
    for i in range(1, len(trace.steps) + 1):
        temp_filename = os.path.join(tempfile.gettempdir(), f"explainflow_video_frame_{i}.png")
        export_image(trace, temp_filename, theme=theme, step=i, width=width)
        img = Image.open(temp_filename).convert("RGB")
        frame_array = np.array(img)
        frames.append(frame_array)
        temp_files.append(temp_filename)
    
    if not frames:
        raise ValueError("No steps to export")
    
    # Ensure all frames have the same shape (pad if necessary)
    max_h = max(f.shape[0] for f in frames)
    max_w = max(f.shape[1] for f in frames)
    
    # Make dimensions even (required by many codecs)
    max_h = max_h + (max_h % 2)
    max_w = max_w + (max_w % 2)
    
    padded_frames = []
    for frame in frames:
        h, w = frame.shape[:2]
        if h != max_h or w != max_w:
            padded = np.zeros((max_h, max_w, 3), dtype=np.uint8)
            padded[:h, :w] = frame
            padded_frames.append(padded)
        else:
            padded_frames.append(frame)
    
    frame_stack = np.stack(padded_frames, axis=0)
    
    # Write video
    output_path = Path(filename)
    iio.imwrite(str(output_path), frame_stack, fps=fps)
    
    # Clean up temp files
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except OSError:
            pass
    
    return output_path


def export_markdown(
    trace: "ExecutionTrace",
    filename: str,
    show_types: bool = True,
) -> Path:
    """
    Export execution trace as a Markdown document.
    
    Args:
        trace: ExecutionTrace to export
        filename: Output filename (should end with .md)
        show_types: Whether to show variable types
        
    Returns:
        Path to the created Markdown file
    """
    lines = []
    lines.append("# ExplainFlow - Code Execution Trace\n")
    
    # Source code
    lines.append("## Source Code\n")
    lines.append("```python")
    lines.append(trace.code.strip())
    lines.append("```\n")
    
    # Steps
    lines.append("## Execution Steps\n")
    
    for step in trace.steps:
        lines.append(f"### Step {step.step_number}: {step.step_type.value.upper()}\n")
        lines.append(f"**Line {step.line_number}:** `{step.line_content.strip()}`\n")
        lines.append(f"> {step.explanation}\n")

        if step.loop_iteration is not None:
            lines.append(f"🔄 **Loop iteration:** {step.loop_iteration}\n")
        if step.duration_ms > 0:
            lines.append(f"⏱ **Duration:** {step.duration_ms:.2f}ms\n")

        if step.variables:
            lines.append("**Variables:**\n")
            lines.append("| Name | Value | Type | Changed | Object ID |")
            lines.append("|------|-------|------|---------|-----------|")
            for var in step.variables.values():
                changed = "⟳" if var.changed else ""
                type_info = var.type_name if show_types else ""
                oid = str(var.object_id) if var.object_id else ""
                lines.append(f"| `{var.name}` | `{var.repr_value}` | {type_info} | {changed} | {oid} |")
            lines.append("")

        if step.call_stack:
            lines.append("**Call Stack:**\n")
            for i, frame in enumerate(step.call_stack):
                indent = "&nbsp;&nbsp;" * i
                rv = f" → `{frame.return_value}`" if frame.return_value else ""
                lines.append(f"- {indent}↳ **{frame.function_name}** (line {frame.line_number}){rv}")
            lines.append("")

        if step.heap_objects:
            lines.append("**Heap Objects:**\n")
            lines.append("| Object ID | Type | Value | Refs |")
            lines.append("|-----------|------|-------|------|")
            for oid, obj in step.heap_objects.items():
                refs = len(obj.children) if obj.children else 0
                lines.append(f"| @{oid} | {obj.type_name} | `{obj.repr_value[:60]}` | {refs} |")
            lines.append("")
    
    # Summary
    lines.append("## Summary\n")
    lines.append(f"- **Total steps:** {len(trace.steps)}")
    lines.append(f"- **Success:** {'✅ Yes' if trace.success else '❌ No'}")
    
    if trace.final_output:
        lines.append(f"\n### Program Output\n")
        lines.append("```")
        lines.append(trace.final_output.rstrip())
        lines.append("```\n")
    
    if not trace.success:
        lines.append(f"\n### Error\n")
        lines.append(f"```\n{trace.error_message}\n```\n")
    
    if trace.final_variables:
        lines.append("\n### Final Variables\n")
        lines.append("| Name | Value | Type |")
        lines.append("|------|-------|------|")
        for var in trace.final_variables.values():
            lines.append(f"| `{var.name}` | `{var.repr_value}` | {var.type_name} |")
        lines.append("")
    
    output_path = Path(filename)
    output_path.write_text("\n".join(lines))
    
    return output_path


def export_html(
    trace: "ExecutionTrace",
    filename: str | None = None,
    theme: str = "dark",
    interactive: bool = True,
    return_string: bool = False,
) -> "Path | str":
    """
    Export execution trace as an interactive HTML file or string.

    Args:
        trace: ExecutionTrace to export
        filename: Output filename (should end with .html). Ignored when *return_string* is True.
        theme: Color theme
        interactive: Whether to include step-through controls
        return_string: If True, return the HTML as a string instead of writing to file.

    Returns:
        Path to the created HTML file, or the HTML string when *return_string* is True.
    """
    from explainflow.visualizer import get_theme

    colors = get_theme(theme)

    # Escape HTML in code
    import html as _html
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
                    "changed": var.changed,
                    "object_id": var.object_id,
                }
                for name, var in step.variables.items()
            },
            "call_stack": [
                {
                    "function": sf.function_name,
                    "line": sf.line_number,
                    "return_value": sf.return_value,
                }
                for sf in step.call_stack
            ],
            "heap_objects": {
                str(oid): {
                    "type": obj.type_name,
                    "repr": obj.repr_value,
                    "children": obj.children,
                }
                for oid, obj in step.heap_objects.items()
            },
            "loop_iteration": step.loop_iteration,
            "duration_ms": step.duration_ms,
        })
    
    import json
    steps_json = json.dumps(steps_data)
    
    # Build code lines HTML
    code_lines_html = []
    for i, line in enumerate(code_lines, 1):
        escaped_line = _html.escape(line) or "&nbsp;"
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
        .call-stack {{ margin-top: 15px; }}
        .call-stack h4 {{ color: {colors["header"]}; margin-bottom: 5px; }}
        .stack-frame {{
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 12px;
            padding: 4px 8px;
            border-left: 3px solid {colors["header"]};
            margin: 3px 0;
            background: rgba(86, 156, 214, 0.08);
        }}
        .heap-panel {{ margin-top: 15px; }}
        .heap-panel h4 {{ color: {colors["changed"]}; margin-bottom: 5px; }}
        .heap-object {{
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 12px;
            padding: 4px 8px;
            border-left: 3px solid {colors["changed"]};
            margin: 3px 0;
        }}
        .timing {{ font-size: 11px; color: {colors["comment"]}; margin-top: 6px; font-style: italic; }}
        .loop-badge {{ display: inline-block; padding: 1px 6px; border-radius: 8px; background: {colors["success"]}20; color: {colors["success"]}; font-size: 11px; margin-left: 5px; }}
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
                        <span class="loop-badge" id="loopBadge" style="display:none;"></span>
                    </div>
                    <div id="lineInfo" style="color: {colors["comment"]}; margin: 5px 0;"></div>
                    <div class="explanation" id="explanation"></div>
                    <div class="timing" id="timing" style="display:none;"></div>
                </div>
                
                <div class="variables">
                    <h4>Variables</h4>
                    <div id="variablesList"></div>
                </div>
                
                <div class="call-stack" id="callStackPanel" style="display:none;">
                    <h4>📚 Call Stack</h4>
                    <div id="callStackList"></div>
                </div>
                
                <div class="heap-panel" id="heapPanel" style="display:none;">
                    <h4>📦 Heap Objects</h4>
                    <div id="heapList"></div>
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
            function escHtml(s) {{ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }}
            for (const [name, info] of Object.entries(step.variables)) {{
                const div = document.createElement('div');
                div.className = 'variable' + (info.changed ? ' changed' : '');
                const oid = info.object_id ? ' <span class="type">@' + escHtml(String(info.object_id)) + '</span>' : '';
                div.innerHTML = (info.changed ? '⟳ ' : '&nbsp;&nbsp;') +
                    '<span class="name">' + escHtml(name) + '</span> = ' +
                    '<span class="value">' + escHtml(info.value) + '</span> ' +
                    '<span class="type">(' + escHtml(info.type) + ')</span>' + oid;
                varsList.appendChild(div);
            }}
            
            // Call stack
            const csPanel = document.getElementById('callStackPanel');
            const csList = document.getElementById('callStackList');
            if (step.call_stack && step.call_stack.length > 0) {{
                csPanel.style.display = 'block';
                csList.innerHTML = '';
                step.call_stack.forEach(frame => {{
                    const d = document.createElement('div');
                    d.className = 'stack-frame';
                    let rv = frame.return_value ? ' → ' + escHtml(String(frame.return_value)) : '';
                    d.innerHTML = '↳ <b>' + escHtml(frame.function) + '</b> (line ' + frame.line + ')' + rv;
                    csList.appendChild(d);
                }});
            }} else {{
                csPanel.style.display = 'none';
            }}
            
            // Heap objects
            const heapPanel = document.getElementById('heapPanel');
            const heapList = document.getElementById('heapList');
            if (step.heap_objects && Object.keys(step.heap_objects).length > 0) {{
                heapPanel.style.display = 'block';
                heapList.innerHTML = '';
                for (const [oid, obj] of Object.entries(step.heap_objects)) {{
                    const d = document.createElement('div');
                    d.className = 'heap-object';
                    const refs = obj.children && Object.keys(obj.children).length ? ' [' + Object.keys(obj.children).length + ' refs]' : '';
                    d.innerHTML = '📦 <b>' + escHtml(obj.type) + '</b> @' + escHtml(oid) + ' = ' + escHtml(obj.repr) + refs;
                    heapList.appendChild(d);
                }}
            }} else {{
                heapPanel.style.display = 'none';
            }}
            
            // Loop iteration badge
            const loopBadge = document.getElementById('loopBadge');
            if (step.loop_iteration !== null && step.loop_iteration !== undefined) {{
                loopBadge.style.display = 'inline-block';
                loopBadge.textContent = 'iter ' + step.loop_iteration;
            }} else {{
                loopBadge.style.display = 'none';
            }}
            
            // Timing
            const timing = document.getElementById('timing');
            if (step.duration_ms > 0) {{
                timing.style.display = 'block';
                timing.textContent = '⏱ ' + step.duration_ms.toFixed(2) + 'ms';
            }} else {{
                timing.style.display = 'none';
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

    if return_string:
        return html_content
    
    output_path = Path(filename)
    output_path.write_text(html_content)
    
    return output_path
