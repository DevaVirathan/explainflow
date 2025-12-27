# ExplainFlow 🔍

**Code Execution Visualizer & Explainer** - Generate step-by-step visual explanations of Python code execution.

[![PyPI version](https://img.shields.io/pypi/v/explainflow.svg)](https://pypi.org/project/explainflow/)
[![PyPI downloads](https://img.shields.io/pypi/dm/explainflow.svg)](https://pypi.org/project/explainflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/DevaVirathan/explainflow?style=social)](https://github.com/DevaVirathan/explainflow)

## ✨ Features

- 🎯 **Step-by-step execution tracing** - See exactly what happens at each line
- 📊 **Variable state visualization** - Track how variables change over time
- 🖼️ **Export to images** - Generate PNG diagrams for documentation
- 🎬 **Export to GIF/video** - Create animated explanations for tutorials
- 🎨 **Beautiful terminal output** - Rich console visualization
- 📝 **Memory diagrams** - Visualize object references and data structures
- 🔄 **Loop unwinding** - See each iteration of loops clearly
- 📚 **Perfect for teaching** - Create educational content effortlessly

## 🚀 Installation

### Standard Installation

```bash
pip install explainflow
```

For video export support:
```bash
pip install explainflow[video]
```

For CLI support:
```bash
pip install explainflow[cli]
```

Install everything:
```bash
pip install explainflow[all]
```

### ⚠️ Windows Installation (Python 3.12+)

If you encounter the error:
```
Fatal error in launcher: Unable to create process using '"C:\...\python.exe" "C:\...\pip.exe"'
```

**Use this command instead:**
```powershell
python -m pip install explainflow
```

<details>
<summary><b>Why does this happen?</b></summary>

This is a known Windows pip launcher issue (not specific to explainflow) that occurs when:
- Python is installed in a path with spaces (e.g., `C:\Program Files`)
- The pip.exe launcher has a stale or corrupted Python path reference
- Multiple Python versions are installed

**Permanent fixes:**
1. **Recommended**: Always use `python -m pip install <package>` on Windows
2. **Repair pip**: `python -m pip install --upgrade --force-reinstall pip`
3. **Use virtual environments**: Create a venv in a path without spaces
4. **Reinstall Python**: Install to a simple path like `C:\Python312`

</details>

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.\venv\Scripts\activate.bat

# Activate (Linux/macOS)
source venv/bin/activate

# Install explainflow
pip install explainflow
```

## 📖 Quick Start

### Basic Usage

```python
from explainflow import explain

# Explain a simple code snippet
code = '''
x = 5
y = 10
result = x + y
print(result)
'''

# Generate step-by-step explanation
explain(code)
```

### Export to Image

```python
from explainflow import explain, export_image

code = '''
numbers = [1, 2, 3, 4, 5]
total = 0
for n in numbers:
    total += n
print(total)
'''

# Generate and export as image
trace = explain(code, output="silent")
export_image(trace, "loop_explanation.png")
```

### Export to GIF

```python
from explainflow import explain, export_gif

code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
'''

trace = explain(code, output="silent")
export_gif(trace, "factorial.gif", fps=1)
```

### Using the Decorator

```python
from explainflow import trace

@trace
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

# This will automatically trace and explain the execution
bubble_sort([64, 34, 25, 12, 22, 11, 90])
```

## 🖥️ CLI Usage

```bash
# Explain a Python file
explainflow run mycode.py

# Export as image
explainflow run mycode.py --output explanation.png

# Export as GIF
explainflow run mycode.py --output explanation.gif --fps 2

# Watch mode - re-run on file changes
explainflow watch mycode.py
```

## 📚 Use Cases

### For Students
- Understand how loops and recursion work
- Debug your code visually
- Study algorithm execution step-by-step

### For Teachers
- Create visual explanations for lectures
- Generate diagrams for assignments
- Build interactive tutorials

### For Documentation
- Add visual code explanations to docs
- Create GIFs for README files
- Generate step-by-step guides

### For Debugging
- Trace variable changes
- Understand control flow
- Find logic errors visually

## 🛠️ API Reference

### Core Functions

#### `explain(code, output="rich", max_steps=1000)`
Execute and explain code step-by-step.

- `code`: Python code string to explain
- `output`: Output mode - "rich" (terminal), "silent", "simple"
- `max_steps`: Maximum execution steps to trace
- Returns: `ExecutionTrace` object

#### `export_image(trace, filename, theme="dark")`
Export execution trace as a PNG image.

#### `export_gif(trace, filename, fps=1, theme="dark")`
Export execution trace as an animated GIF.

#### `@trace` decorator
Decorator to automatically trace function execution.

## 🎨 Themes

ExplainFlow supports multiple themes:
- `dark` (default) - Dark background, easy on eyes
- `light` - Light background for printing
- `colorblind` - Accessible color scheme

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔧 Troubleshooting

### Windows: "Fatal error in launcher" when using pip

If you see this error on Windows:
```
Fatal error in launcher: Unable to create process using '"..."'
```

**Quick Fix** - Use `python -m pip` instead of `pip`:
```powershell
python -m pip install explainflow
```

**Permanent Fix** - Repair your pip installation:
```powershell
python -m pip install --upgrade --force-reinstall pip
```

This is a Windows-specific issue with the pip launcher, not a problem with explainflow. See [pip issue discussion](https://stackoverflow.com/q/24627525) for more details.

### Import errors after installation

Make sure you're using the same Python environment where you installed explainflow:
```bash
python -c "import explainflow; print(explainflow.__version__)"
```

### GIF/Video export not working

Install the video dependencies:
```bash
python -m pip install explainflow[video]
```

## 🙏 Acknowledgments

- Inspired by [Python Tutor](http://pythontutor.com/)
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Uses [Pillow](https://python-pillow.org/) for image generation

## 📬 Contact

- Create an issue for bug reports or feature requests
- Star ⭐ the repo if you find it useful!

---

Made with ❤️ for the Python community
