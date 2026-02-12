# ExplainFlow Roadmap 🗺️

## Future Enhancements & Missing Features Plan

This document outlines the planned improvements, bug fixes, and new features for ExplainFlow.

---

## 🔴 Critical Missing Features (Promised but Not Implemented)

| # | Feature | Status | Priority | Effort |
|---|---------|--------|----------|--------|
| 1 | **Video Export (MP4)** | ❌ Not implemented | 🔴 High | Low |
| 2 | **Memory/Heap Diagrams** | ❌ Not implemented | 🔴 High | High |
| 3 | **Object Reference Visualization** | ❌ Not implemented | 🔴 High | High |

### Details:

#### 1. Video Export
- Dependencies already exist in `pyproject.toml` (`imageio`, `imageio-ffmpeg`)
- Just needs implementation of `export_video()` function
- Estimated time: 1-2 hours

#### 2. Memory/Heap Diagrams
- Visualize heap objects separately from stack
- Show memory addresses
- Display object lifecycle

#### 3. Object Reference Visualization
- Show arrows connecting variables to objects
- Display when multiple variables reference same object
- Track object mutations

---

## 🟠 Major Gaps vs Python Tutor

| # | Feature | Description | Priority |
|---|---------|-------------|----------|
| 4 | **Call Stack Visualization** | Show nested function frames with proper indentation | High |
| 5 | **Data Structure Diagrams** | Visualize lists with indices, dicts with key-value boxes | High |
| 6 | **Object Identity Tracking** | Show object IDs, reference sharing between variables | Medium |
| 7 | **Step Backward** | Allow stepping backwards through execution | Medium |
| 8 | **Breakpoints** | Stop at specific lines | Medium |
| 9 | **Web Interface** | Live interactive web UI (not just static HTML export) | Low |

---

## 🟡 Bugs to Fix

| # | Bug | Location | Fix | Priority |
|---|-----|----------|-----|----------|
| 10 | **@trace decorator executes function twice** | `tracer.py` | Return result from trace, don't call again | 🔴 High |
| 11 | **Windows incompatibility** | `exporter.py` | Use `tempfile.gettempdir()` instead of `/tmp` | 🔴 High |
| 12 | **HTML injection risk** | `exporter.py` | Escape user code in HTML export | 🟠 Medium |
| 13 | **Variable comparison fails for complex objects** | `tracer.py` | Use safer comparison method | 🟡 Low |

### Bug Fix Details:

#### Bug #10: @trace Double Execution
```python
# Current code (WRONG):
def wrapper(*args, **kwargs):
    tracer = Tracer(max_steps=max_steps)
    trace_result = tracer.trace_function(f, *args, **kwargs)
    # ... visualization code ...
    return f(*args, **kwargs)  # <-- Called AGAIN!

# Fixed code:
def wrapper(*args, **kwargs):
    tracer = Tracer(max_steps=max_steps)
    trace_result = tracer.trace_function(f, *args, **kwargs)
    # ... visualization code ...
    return trace_result.return_value  # Don't call f() again!
```

#### Bug #11: Windows Temp Path
```python
# Current code (WRONG):
temp_filename = f"/tmp/explainflow_frame_{i}.png"

# Fixed code:
import tempfile
temp_filename = os.path.join(tempfile.gettempdir(), f"explainflow_frame_{i}.png")
```

---

## 🟢 Feature Enhancements (Nice to Have)

| # | Feature | Description | Priority |
|---|---------|-------------|----------|
| 14 | **Jupyter Notebook Integration** | IPython display, cell magic `%%explain` | Medium |
| 15 | **VSCode Extension** | Inline visualization during debugging | Low |
| 16 | **Async/Generator Support** | Handle `yield`, `async/await` | Medium |
| 17 | **Context Manager Tracing** | Trace `with` statement `__enter__`/`__exit__` | Low |
| 18 | **Multi-file Tracing** | Trace imported modules | Low |
| 19 | **Export to Markdown** | Step-by-step markdown documentation | Low |
| 20 | **Custom Themes** | User-defined color themes via config | Low |
| 21 | **Syntax Highlighting in Images** | Use Pygments for PNG/GIF | Medium |
| 22 | **Performance Profiling** | Show execution time per step | Low |
| 23 | **Special Type Support** | NumPy arrays, Pandas DataFrames, etc. | Medium |
| 24 | **Iframe Embedding** | Embed in websites/blogs | Low |

---

## 📋 Implementation Roadmap

### Phase 1: Bug Fixes & Quick Wins (v0.2.0)
- [x] Fix @trace decorator double execution
- [x] Fix Windows temp file path
- [x] Fix HTML escaping
- [x] Implement video export (MP4)
- [x] Add Windows font fallbacks

**Target Release:** v0.2.0 ✅ COMPLETE

---

### Phase 2: Core Visualization (v0.3.0)
- [x] Memory/Heap diagram visualization
- [x] Object reference arrows
- [x] Data structure diagrams (lists, dicts)
- [x] Object ID tracking
- [x] Improved variable display for complex types

**Target Release:** v0.3.0 ✅ COMPLETE

---

### Phase 3: Enhanced Interactivity (v0.4.0)
- [x] Call stack visualization
- [x] Step backward support
- [x] Breakpoints
- [x] Improved exception flow visualization
- [x] Loop iteration counter

**Target Release:** v0.4.0 ✅ COMPLETE

---

### Phase 4: Integrations (v0.5.0)
- [x] Jupyter Notebook integration
- [x] Live web interface (WebSocket-based)
- [x] Async/generator support
- [x] Context manager tracing

**Target Release:** v0.5.0 ✅ COMPLETE

---

### Phase 5: Polish (v1.0.0)
- [x] VSCode extension
- [x] Multi-file tracing
- [x] Custom themes
- [x] Special type support (NumPy, Pandas)
- [x] Comprehensive documentation site
- [x] Performance optimizations

**Target Release:** v1.0.0 ✅ COMPLETE

---

## 🎯 Priority Matrix

|  | **Low Effort** | **High Effort** |
|--|----------------|-----------------|
| **High Impact** | Video export, Bug fixes, Windows compat | Memory diagrams, Call stack viz |
| **Low Impact** | Markdown export, Custom themes | VSCode extension, Multi-file tracing |

---

## 💡 Quick Implementation Snippets

### Video Export (Add to exporter.py)
```python
def export_video(trace: "ExecutionTrace", filename: str, fps: int = 1, theme: str = "dark") -> None:
    """Export execution trace as MP4 video."""
    try:
        import imageio
    except ImportError:
        raise ImportError("Video export requires imageio. Install with: pip install explainflow[video]")
    
    frames = []
    for i in range(len(trace.steps)):
        frame = _generate_frame(trace, i, theme)
        frames.append(np.array(frame))
    
    imageio.mimwrite(filename, frames, fps=fps)
    print(f"✓ Video saved to {filename}")
```

### Jupyter Integration (Future)
```python
def _repr_html_(self):
    """IPython display integration."""
    return export_html(self, return_string=True)
```

---

## 📊 Current vs Target Feature Comparison

| Feature | Python Tutor | ExplainFlow Now | ExplainFlow Target |
|---------|--------------|-----------------|-------------------|
| Step-by-step tracing | ✅ | ✅ | ✅ |
| Variable tracking | ✅ | ✅ | ✅ |
| Rich terminal output | ❌ | ✅ | ✅ |
| PNG export | ❌ | ✅ | ✅ |
| GIF export | ❌ | ✅ | ✅ |
| HTML export | ✅ | ✅ | ✅ |
| Video export | ❌ | ❌ | ✅ v0.2.0 |
| Heap visualization | ✅ | ❌ | ✅ v0.3.0 |
| Object references | ✅ | ❌ | ✅ v0.3.0 |
| Call stack display | ✅ | ⚠️ Basic | ✅ v0.4.0 |
| Step backward | ✅ | ❌ | ✅ v0.4.0 |
| Breakpoints | ✅ | ❌ | ✅ v0.4.0 |
| Web interface | ✅ | ❌ | ✅ v0.5.0 |
| Jupyter support | ❌ | ❌ | ✅ v0.5.0 |
| CLI tool | ❌ | ✅ | ✅ |
| Decorator API | ❌ | ✅ | ✅ |
| Multiple themes | ❌ | ✅ | ✅ |

---

## 🔗 Related Resources

- **Python Tutor**: http://pythontutor.com/ (Inspiration)
- **Rich Library**: https://github.com/Textualize/rich
- **Pillow**: https://python-pillow.org/

---

## 📝 Contributing

Want to help implement these features? Check out [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Priority areas where contributions are welcome:
1. Bug fixes (especially #10, #11)
2. Video export implementation
3. Data structure visualization
4. Test coverage improvements

---

*Last Updated: December 2024*
