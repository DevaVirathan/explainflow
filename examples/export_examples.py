# Example: Exporting Traces to Different Formats

from explainflow import explain, export_image, export_gif, export_html

# Code to trace
code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

numbers = [64, 34, 25, 12, 22, 11, 90]
sorted_nums = bubble_sort(numbers.copy())
print(f"Sorted: {sorted_nums}")
"""

# Trace the code silently (no terminal output)
print("Tracing bubble sort algorithm...")
trace = explain(code, output="silent")

# Export as PNG image
print("Exporting to PNG...")
export_image(trace, "bubble_sort_trace.png", theme="dark")
print("✅ Created: bubble_sort_trace.png")

# Export as animated GIF
print("Exporting to GIF (this may take a moment)...")
export_gif(trace, "bubble_sort_animated.gif", fps=0.5, theme="dark")
print("✅ Created: bubble_sort_animated.gif")

# Export as interactive HTML
print("Exporting to HTML...")
export_html(trace, "bubble_sort_interactive.html", theme="dark")
print("✅ Created: bubble_sort_interactive.html")

print("\n🎉 All exports completed!")
print("Open bubble_sort_interactive.html in a browser to step through the execution.")
