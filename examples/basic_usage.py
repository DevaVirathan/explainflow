# Example: Basic Usage of ExplainFlow
# This file demonstrates the core features of ExplainFlow

from explainflow import explain

# Simple variable assignment
print("=" * 50)
print("Example 1: Simple Assignment")
print("=" * 50)

code1 = """
x = 5
y = 10
result = x + y
print(f"The sum is: {result}")
"""

trace1 = explain(code1)

# Loop example
print("\n" + "=" * 50)
print("Example 2: Loop Execution")
print("=" * 50)

code2 = """
numbers = [1, 2, 3, 4, 5]
total = 0
for n in numbers:
    total += n
print(f"Sum: {total}")
"""

trace2 = explain(code2)

# Conditional example
print("\n" + "=" * 50)
print("Example 3: Conditionals")
print("=" * 50)

code3 = """
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

trace3 = explain(code3)

# Function example
print("\n" + "=" * 50)
print("Example 4: Function Calls")
print("=" * 50)

code4 = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
print(f"5! = {result}")
"""

trace4 = explain(code4)

print("\n✅ All examples completed!")
