# Example: Using the @trace Decorator

from explainflow import trace

# Decorate any function to automatically trace its execution
@trace
def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@trace(output="simple", max_steps=50)
def binary_search(arr, target):
    """Binary search implementation."""
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


if __name__ == "__main__":
    print("=" * 50)
    print("Example: Fibonacci with @trace decorator")
    print("=" * 50)
    
    # This will automatically trace and display the execution
    result = fibonacci(5)
    print(f"\nFibonacci(5) = {result}")
    
    print("\n" + "=" * 50)
    print("Example: Binary Search with @trace decorator")
    print("=" * 50)
    
    sorted_array = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    target = 11
    
    index = binary_search(sorted_array, target)
    print(f"\nFound {target} at index {index}")
