# mac-compatible script
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import time
import pyautogui
import subprocess

mcp = FastMCP("Calculator")

# ----------- MATH TOOLS -----------
@mcp.tool()
def add(a: int, b: int) -> int:
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    return sum(l)

@mcp.tool()
def subtract(a: int, b: int) -> int:
    return int(a - b)

@mcp.tool()
def multiply(a: int, b: int) -> int:
    return int(a * b)

@mcp.tool()
def divide(a: int, b: int) -> float:
    return float(a / b)

@mcp.tool()
def power(a: int, b: int) -> int:
    return int(a ** b)

@mcp.tool()
def sqrt(a: int) -> float:
    return float(a ** 0.5)

@mcp.tool()
def cbrt(a: int) -> float:
    return float(a ** (1/3))

@mcp.tool()
def factorial(a: int) -> int:
    return int(math.factorial(a))

@mcp.tool()
def log(a: int) -> float:
    return float(math.log(a))

@mcp.tool()
def remainder(a: int, b: int) -> int:
    return int(a % b)

@mcp.tool()
def sin(a: int) -> float:
    return float(math.sin(a))

@mcp.tool()
def cos(a: int) -> float:
    return float(math.cos(a))

@mcp.tool()
def tan(a: int) -> float:
    return float(math.tan(a))

@mcp.tool()
def mine(a: int, b: int) -> int:
    return int(a - b - b)

# ----------- IMAGE TOOL -----------
@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

# ----------- STRING/INT TOOLS -----------
@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]

# ----------- GUI AUTOMATION TOOLS FOR MAC -----------
@mcp.tool()
def open_freeform():
    subprocess.run(["open", "-a", "Freeform"])
    return {"content": [TextContent(type="text", text="Freeform app launched")]} 

@mcp.tool()
def draw_rectangle_mac(x1: int, y1: int, x2: int, y2: int) -> dict:
    try:
        pyautogui.moveTo(x1, y1)
        pyautogui.mouseDown()
        pyautogui.moveTo(x2, y2)
        pyautogui.mouseUp()
        return {"content": [TextContent(type="text", text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})")]} 
    except Exception as e:
        return {"content": [TextContent(type="text", text=f"Error drawing rectangle: {str(e)}")]} 

@mcp.tool()
def type_text_mac(x: int, y: int, text: str) -> dict:
    try:
        pyautogui.click(x, y)
        time.sleep(0.5)
        pyautogui.write(text, interval=0.05)
        return {"content": [TextContent(type="text", text=f"Typed text '{text}' at ({x},{y})")]} 
    except Exception as e:
        return {"content": [TextContent(type="text", text=f"Error typing text: {str(e)}")]} 

# ----------- RESOURCES & PROMPTS -----------
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    return f"Hello, {name}!"

@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"

@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()
    else:
        mcp.run(transport="stdio")
