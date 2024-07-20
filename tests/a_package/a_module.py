"""
A dummy module for testing purposes.
"""

import random


class AClass:
    """
    A dummy class for testing.
    """

    def __init__(self, a: int):
        self.a = a

    def a_method(self, b):
        return self.a + b

    def __repr__(self):
        return f"AClass(a={self.a})"


def a_function(a, b):
    return a + b


def another_function(a, b):
    return random.randint(a, b)
