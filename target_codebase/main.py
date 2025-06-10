# target_codebase/main.py

import math

def calculate_area(radius):
    """Calculates the area of a circle. """ # Deliberate extra space after period
    result = math.pi * radius * radius # Deliberate trailing whitespace
    return result

def greet(name):
    # This function has no docstring at all
    print("Hello, " + name + "!")


def unused_function():
    # This function is never called, will be flagged as unused
    pass

if __name__ == "__main__":
    # Deliberate indentation error below
        area = calculate_area(5)
    print(f"Area: {area}")
    greet("Alice")