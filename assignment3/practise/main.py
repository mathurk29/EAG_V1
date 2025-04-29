# %%
import ast
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# %%
import os

# Access your API key
api_key = os.getenv("GEMINI_API_KEY")


from google import genai

client = genai.Client(api_key=api_key)

# %%
response = client.models.generate_content(model="gemini-2.0-flash", contents="Hi")
response.text.strip()


# %%
def generate_fibonacci(n: int):
    """
    Generate the first n Fibonacci numbers.
    :param n: Number of Fibonacci numbers to generate.
    :return: List of first n Fibonacci numbers.
    """
    if type(n) != int:
        n = int(n)
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


# %%
import math

def log_base_10(x):
    """
    Compute the logarithm (base 10) of a number.
    :param x: Number to take log of.
    :return: Logarithm (base 10) of x.
    """
    if type(x) != int:
        x = int(x)
    if x <= 0:
        raise ValueError("Logarithm is undefined for non-positive values.")
    return math.log10(x)

# %%
def sum_list(lst):
    """
    Compute the sum of elements in a list.
    :param lst: List of numbers.
    :return: Sum of all numbers in the list.
    """
    lst = [int(x) for x in lst]
    return sum(lst)

# %%
max_iterations = 10
current_iteration = 0
iteration_response = []
last_response = None

# %%
def function_caller(func_name, params):
    """Simple function caller that maps function names to actual functions"""
    function_map = {
        "generate_fibonacci": generate_fibonacci,
        "log_base_10": log_base_10,
        "sum_list": sum_list
    }
    
    if func_name in function_map:
        return function_map[func_name](params)
    else:
        return f"Function {func_name} not found"

# %%
system_prompt = """
You are a math agent solving problems in iterations. Respond with EXACTLY ONE of these formats:

1. FUNCTION_CALL: python_function_name|input
2. FINAL_ANSWER: [number]

where python_function_name is one of the following:

1 sum_list:
     Compute the sum of elements in a list.
     :param lst: List of numbers.
     :return: Sum of all numbers in the list.
2 generate_fibonacci:     
    Generate the first n Fibonacci numbers.
    :param n: Number of Fibonacci numbers to generate.
    :return: List of first n Fibonacci numbers..
3 log_base_10: 
    Compute the logarithm (base 10) of a number.
    :param x: Number to take log of.
    :return: Logarithm (base 10) of x.

DO NOT include multiple responses. Give ONE response at a time.
"""

# %%
query = """
Compute the sum of logarithms (base 10) of the 15 Fibonacci numbers
"""

# %%
while current_iteration < max_iterations:
    print(f"\n--- Iteration {current_iteration + 1} ---")
    if last_response == None:
        current_query = query
    else:
        current_query = current_query + "\n\n" + " ".join(iteration_response)
        current_query = current_query + "  What should I do next?"

    # Get model's response
    prompt = f"{system_prompt}\n\nQuery: {current_query}"
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    response_text = response.text.strip()
    print(f"LLM Response: {response_text}")

    if response_text.startswith("FUNCTION_CALL:"):
        response_text = response.text.strip()
        _, function_info = response_text.split(":", 1)
        func_name, params = [x.strip() for x in function_info.split("|", 1)]
        iteration_result = function_caller(func_name, ast.literal_eval(params))

    # Check if it's the final answer
    elif response_text.startswith("FINAL_ANSWER:"):
        print("\n=== Agent Execution Complete ===")
        break

    print(f"  Result: {iteration_result}")
    last_response = iteration_result
    iteration_response.append(
        f"In the {current_iteration + 1} iteration you called {func_name} with {params} parameters, and the function returned {iteration_result}."
    )

    current_iteration += 1



