#!/usr/bin/env python3
"""
Simple test file for testing aider with SnowX provider.

This module provides basic arithmetic operations and greeting functionality:

Functions:
    hello_snowx(): Returns a greeting message from SnowX
    add_numbers(a, b): Returns the sum of two numbers
    multiply_numbers(a, b): Returns the product of two numbers
    divide_numbers(a, b): Returns the division of two numbers, with zero division handling
"""

def hello_snowx():
    """Return a greeting message."""
    return "Hello from SnowX!"

def add_numbers(a, b):
    """Add two numbers and return the result."""
    return a + b

def multiply_numbers(a, b):
    """Multiply two numbers and return the result."""
    return a * b

def divide_numbers(a, b):
    """Divide two numbers, handling division by zero."""
    if b == 0:
        return "Error: Division by zero is not allowed."
    return a / b

if __name__ == "__main__":
    print(hello_snowx())
    result = add_numbers(5, 3)
    print(f"5 + 3 = {result}")
    product = multiply_numbers(5, 3)
    print(f"5 * 3 = {product}")
    division = divide_numbers(5, 3)
    print(f"5 / 3 = {division}")
    zero_division = divide_numbers(5, 0)
    print(f"5 / 0 = {zero_division}")
