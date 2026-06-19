# ExplainFlow — Demo & Walkthrough 🔍

A hands-on tour of **ExplainFlow**, the code-execution visualizer that traces Python
line-by-line and renders it to your terminal, PNG, GIF, or interactive HTML.

> Every demo below is self-contained — copy a block into a file (or the REPL) and run it.

---

## Table of Contents

1. [Setup](#1-setup)
2. [Demo 1 — Your First Trace](#demo-1--your-first-trace)
3. [Demo 2 — Watching Variables Change in a Loop](#demo-2--watching-variables-change-in-a-loop)
4. [Demo 3 — Conditionals & Branching](#demo-3--conditionals--branching)
5. [Demo 4 — Functions & Recursion](#demo-4--functions--recursion)
6. [Demo 5 — The `@trace` Decorator](#demo-5--the-trace-decorator)
7. [Demo 6 — Exporting (PNG / GIF / HTML)](#demo-6--exporting-png--gif--html)
8. [Demo 7 — Inspecting the Trace Object](#demo-7--inspecting-the-trace-object)
9. [Demo 8 — Themes](#demo-8--themes)
10. [Demo 9 — The CLI](#demo-9--the-cli)
11. [Demo 10 — Handling Errors](#demo-10--handling-errors)
12. [API Cheat-Sheet](#api-cheat-sheet)
13. [Troubleshooting](#troubleshooting)

---

## 1. Setup

```bash
# Core library (terminal + image + HTML export)
pip install explainflow

# Add the command-line tool
pip install explainflow[cli]

# Everything (cli + video + dev tools)
pip install explainflow[all]
```

> **Windows tip:** if `pip` throws a launcher error, use `python -m pip install explainflow`.

Verify it works:

```python
import explainflow
print(explainflow.__version__)   # 0.1.0
```

---

## Demo 1 — Your First Trace

The single most important function is `explain()`. Give it a string of Python; it runs
the code, records every step, and prints a beautiful step-by-step trace.

```python
from explainflow import explain

code = """
x = 5
y = 10
result = x + y
print(f"The sum is: {result}")
"""

explain(code)
```

**What you get in the terminal** (abridged):

```
╭───────────────────────────────────────────╮
│ ExplainFlow - Code Execution Trace        │
╰───────────────────────────────────────────╯

╭─ Source Code ─────────────────────────────╮
│ 1  x = 5                                   │
│ 2  y = 10                                  │
│ 3  result = x + y                          │
│ 4  print(f"The sum is: {result}")          │
╰───────────────────────────────────────────╯

╭─ Step 1  ASSIGNMENT ──────────────────────╮
│ Line 1: x = 5                              │
│ → Set x to 5                               │
│ Variables:                                 │
│   ⟳ x = 5 (int)                            │
╰───────────────────────────────────────────╯

╭─ Step 2  ASSIGNMENT ──────────────────────╮
│ Line 2: y = 10                             │
│ → Set y to 10                              │
│ Variables:                                 │
│     x = 5 (int)                            │
│   ⟳ y = 10 (int)                           │
╰───────────────────────────────────────────╯

... (Step 3 sets result = 15, Step 4 prints) ...

╭─ Program Output ──────────────────────────╮
│ The sum is: 15                            │
╰───────────────────────────────────────────╯

✓ Execution completed successfully
Total steps: 4
```

**Key ideas illustrated here:**
- Each executed line becomes a **step** with a type (`ASSIGNMENT`, `CONDITION`, `CALL`, …).
- The `⟳` marker flags a variable that **changed on that step**.
- Variable **types** are shown (`int`, `str`, …) — toggle with `show_types=False`.

---

## Demo 2 — Watching Variables Change in a Loop

Loops are where ExplainFlow shines: you see the accumulator update on every iteration.

```python
from explainflow import explain

code = """
numbers = [1, 2, 3, 4, 5]
total = 0
for n in numbers:
    total += n
print(f"Sum: {total}")
"""

explain(code)
```

Each pass through the loop produces a step where `n` takes the next list value and
`total` grows — both flagged with `⟳` the moment they change:

```
Step 5  ASSIGNMENT   Line 4: total += n
→ Set total to 1
  numbers = [1, 2, 3, 4, 5] (list)
⟳ n = 1 (int)
⟳ total = 1 (int)
...
→ Set total to 15   (final iteration)
```

---

## Demo 3 — Conditionals & Branching

ExplainFlow labels `if/elif/else` lines as **CONDITION** steps so you can follow which
branch was taken.

```python
from explainflow import explain

code = """
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"

print(f"Grade: {grade}")
"""

explain(code)
```

You'll see the `score >= 90` condition evaluated and skipped, then `score >= 80`
evaluated and taken, then `grade = "B"` assigned — the exact path through the branches.

---

## Demo 4 — Functions & Recursion

Function entry/exit are first-class steps (**CALL** / **RETURN**), and `call_depth`
tracks nesting — perfect for explaining recursion.

```python
from explainflow import explain

code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
print(f"5! = {result}")
"""

explain(code)
```

The trace shows each recursive `CALL` going deeper, then each `RETURN` unwinding back up
(`Returning: 1`, `Returning: 2`, `Returning: 6`, …) until `result = 120`.

---

## Demo 5 — The `@trace` Decorator

Don't want to pass code as a string? Decorate a real function. It runs normally **and**
prints the trace, returning the actual result.

```python
from explainflow import trace

@trace
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Works with or without arguments:
@trace(output="simple", max_steps=50)
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


result = fibonacci(5)               # prints the trace, then...
print(f"fibonacci(5) = {result}")   # fibonacci(5) = 5

idx = binary_search([1, 3, 5, 7, 9, 11], 11)
print(f"found at index {idx}")      # found at index 4
```

- `@trace` — trace with default rich output.
- `@trace(output="simple")` — plain text, no colors.
- `@trace(output="silent", max_steps=50)` — trace silently, cap the steps.

The decorated function still returns its normal value, so it's drop-in.

---

## Demo 6 — Exporting (PNG / GIF / HTML)

Trace once with `output="silent"`, then export the trace object to any format.

```python
from explainflow import explain, export_image, export_gif, export_html

code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

numbers = [64, 34, 25, 12, 22, 11, 90]
print(bubble_sort(numbers.copy()))
"""

trace = explain(code, output="silent")          # trace without printing

export_image(trace, "bubble_sort.png", theme="dark")     # single PNG (final state)
export_html(trace, "bubble_sort.html")                   # interactive step player
export_gif(trace, "bubble_sort.gif", fps=0.5)            # animated, 1 frame / 2s
```

| Export | Function | Notes |
|--------|----------|-------|
| **PNG**  | `export_image(trace, "out.png", theme=, step=, show_all_steps=)` | Pass `step=N` for a specific step, or `show_all_steps=True` for one tall image. |
| **GIF**  | `export_gif(trace, "out.gif", fps=, theme=, loop=)` | One frame per step; lower `fps` = slower playback. |
| **HTML** | `export_html(trace, "out.html", theme=, interactive=)` | Self-contained file with ◀ ▶ Play controls + arrow-key / spacebar navigation. |

> **The HTML export is the best demo** — open it in a browser and step through the whole
> algorithm with the arrow keys, watching variables update live.

> ⚠️ **Windows note:** in v0.1.0 `export_gif` writes temp frames to `/tmp/...`, which does
> not exist on Windows, so GIF export currently fails there. PNG and HTML export work
> fine. (See [Troubleshooting](#troubleshooting).)

---

## Demo 7 — Inspecting the Trace Object

`explain()` returns an `ExecutionTrace` — a rich object you can query programmatically.
It's iterable, indexable, and has helper methods.

```python
from explainflow import explain

trace = explain("a = 1\nb = 2\nc = a + b", output="silent")

len(trace)                        # number of recorded steps
trace[0]                          # first ExecutionStep
for step in trace:                # iterate steps
    print(step.step_number, step.step_type.value, step.explanation)

trace.get_step(3)                 # step by number
trace.get_variable_history("a")   # [(step_no, Variable), ...] for 'a'
trace.get_lines_executed()        # line number for each step, e.g. [0, 1, 2, 3, 3]
print(trace.summary())            # human-readable summary block

trace.success                     # True / False
trace.final_output                # captured stdout
trace.final_variables             # {name: Variable} at the end
```

`trace.summary()` prints something like:

```
Execution Summary
========================================
Total steps: 3
Lines in code: 3
Success: True

Final Variables:
  a = 1 (int)
  b = 2 (int)
  c = 3 (int)
```

---

## Demo 8 — Themes

Three built-in themes work across terminal, image, and HTML output:

```python
explain(code, theme="dark")        # default — dark background
explain(code, theme="light")       # light background, good for print/slides
explain(code, theme="colorblind")  # accessible palette
```

The same `theme=` argument flows into `export_image`, `export_gif`, and `export_html`.

---

## Demo 9 — The CLI

Install with `pip install explainflow[cli]`, then run files directly:

```bash
# Explain a file in the terminal
explainflow run script.py

# Export to image / GIF / HTML by file extension
explainflow run script.py -o trace.png
explainflow run script.py -o trace.gif --fps 2
explainflow run script.py -o trace.html

# Options
explainflow run script.py -t light      # theme
explainflow run script.py -m 200         # max steps
explainflow run script.py -q             # quiet (no terminal trace, just export)
explainflow run script.py -s             # simple (plain, no colors)

# Explain a snippet inline (semicolons become new lines)
explainflow explain-code "x = 5; y = 10; print(x + y)"

# Re-run automatically whenever the file is saved
explainflow watch script.py

# Version
explainflow version
```

| Command | Purpose |
|---------|---------|
| `run FILE` | Trace a file; optionally export with `-o`. |
| `explain-code "..."` | Trace a one-liner snippet. |
| `watch FILE` | Live re-trace on every save (Ctrl+C to stop). |
| `version` | Print the installed version. |

---

## Demo 10 — Handling Errors

ExplainFlow captures problems into the trace instead of crashing your program.

**Syntax error** — reported up front, `success=False`:

```python
trace = explain("x = = 5", output="silent")
print(trace.success)         # False
print(trace.error_message)   # SyntaxError: ... (line 1)
```

**Runtime exception** — traced up to the failing line, then an `EXCEPTION` step is added:

```python
code = """
a = 10
b = 0
c = a / b
print(c)
"""

trace = explain(code, output="silent")
print(trace.success)         # False
print(trace.error_message)   # ZeroDivisionError: division by zero
```

The steps leading up to the error are preserved, so you can see exactly what state the
program was in when it blew up.

> **Runaway protection:** every trace is capped at `max_steps` (default **1000**) so an
> infinite loop won't hang — it stops after the limit and returns what it captured.

---

## API Cheat-Sheet

```python
from explainflow import (
    explain, explain_function, trace,         # tracing
    export_image, export_gif, export_html,    # exporting
    ExecutionTrace, ExecutionStep, Variable, StepType,  # data models
)
```

**`explain(code, output="rich", max_steps=1000, show_types=True, theme="dark") -> ExecutionTrace`**
Run a code string and (optionally) print the trace. `output` ∈ `{"rich", "simple", "silent"}`.

**`explain_function(func, *args, **kwargs) -> ExecutionTrace`**
Trace a function called with the given arguments.

**`@trace` / `@trace(output=, max_steps=)`**
Decorator that traces a function on each call and returns its real result.

**`export_image(trace, filename, theme="dark", step=None, width=1200, show_all_steps=False)`**

**`export_gif(trace, filename, fps=1.0, theme="dark", width=1200, loop=True)`**

**`export_html(trace, filename, theme="dark", interactive=True)`**

**`StepType`** values: `LINE`, `ASSIGNMENT`, `CONDITION`, `LOOP_START`, `CALL`, `RETURN`,
`EXCEPTION` (plus reserved `LOOP_ITERATION`, `LOOP_END`).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `pip` "Fatal error in launcher" on Windows | Use `python -m pip install explainflow`. |
| `ImportError` for Pillow on export | `python -m pip install pillow` (bundled in core, but check your env). |
| Terminal output looks plain, not colored | Install Rich (bundled in core): `python -m pip install rich`. |
| CLI command not found | Install the extra: `python -m pip install explainflow[cli]`. |
| `export_gif` fails on Windows (`/tmp` not found) | Known v0.1.0 issue — temp frames use a hardcoded `/tmp` path. Use PNG/HTML export for now. |
| Trace stops early on a long program | Raise the cap: `explain(code, max_steps=5000)`. |

---

Made with ❤️ for the Python community — inspired by [Python Tutor](http://pythontutor.com/).
