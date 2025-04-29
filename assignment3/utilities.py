import math
import os

# Access your API key
api_key = os.getenv("GEMINI_API_KEY")


from google import genai

client = genai.Client(api_key=api_key)


def generate_fibonacci(n):
    """
    Generate the first n Fibonacci numbers.
    :param n: Number of Fibonacci numbers to generate.
    :return: List of first n Fibonacci numbers.
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib_sequence = [0, 1]
    for i in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence


def log_base_10(x):
    """
    Compute the logarithm (base 10) of a number.
    :param x: Number to take log of.
    :return: Logarithm (base 10) of x.
    """
    if x <= 0:
        raise ValueError("Logarithm is undefined for non-positive values.")
    return math.log10(x)


def sum_list(lst):
    """
    Compute the sum of elements in a list.
    :param lst: List of numbers.
    :return: Sum of all numbers in the list.
    """
    return sum(lst)
