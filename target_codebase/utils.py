# target_codebase/utils.py

# This module has no docstring.

class Helper:
    def __init__(self, value):
        self.value = value

    def add_one(self):
        # Another missing docstring for this method
        return self.value + 1

def calculate_average(list_of_numbers):
    total = 0
    for num in list_of_numbers:
        total += num
    # This function is missing a docstring
    # It's also missing a return statement, which is a logic bug
    # For demonstration, we'll focus on static analysis flags first.
    # return total / len(list_of_numbers)