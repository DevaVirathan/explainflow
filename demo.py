# from explainflow import explain

# code = """
# x = 5
# y = 10
# result = x + y
# print(f"The sum is: {result}")
# """

# explain(code)

# from explainflow import explain

# code = """
# numbers = [1, 2, 3, 4, 5]
# total = 0
# for n in numbers:
#     total += n
# print(f"Sum: {total}")
# """

# explain(code)

# from explainflow import explain

# code = """
# score = 85

# if score >= 90:
#     grade = "A"
# elif score >= 80:
#     grade = "B"
# elif score >= 70:
#     grade = "C"
# else:
#     grade = "F"

# print(f"Grade: {grade}")
# """

# explain(code)

# from explainflow import explain

# code = """
# def factorial(n):
#     if n <= 1:
#         return 1
#     return n * factorial(n - 1)

# result = factorial(5)
# print(f"5! = {result}")
# """

# explain(code)

# from explainflow import trace

# @trace
# def fibonacci(n):
#     if n <= 1:
#         return n
#     return fibonacci(n - 1) + fibonacci(n - 2)

# # Works with or without arguments:
# @trace(output="simple", max_steps=50)
# def binary_search(arr, target):
#     left, right = 0, len(arr) - 1
#     while left <= right:
#         mid = (left + right) // 2
#         if arr[mid] == target:
#             return mid
#         elif arr[mid] < target:
#             left = mid + 1
#         else:
#             right = mid - 1
#     return -1


# result = fibonacci(5)               # prints the trace, then...
# print(f"fibonacci(5) = {result}")   # fibonacci(5) = 5

# idx = binary_search([1, 3, 5, 7, 9, 11], 11)
# print(f"found at index {idx}")      # found at index 4

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