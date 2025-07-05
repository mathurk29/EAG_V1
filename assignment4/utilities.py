import pyautogui
import os
import time

def write_to_freeform(text_to_write = "Hello, Freeform!"):

    os.system("open -a Freeform")
    time.sleep(1)

    # Optional: Click to ensure Freeform is focused (adjust coords if needed)
    pyautogui.click(800, 5000)
    time.sleep(1)

    # Open new board
    pyautogui.hotkey('command', 'n')
    time.sleep(1)

    # Insert menu
    pyautogui.click(240, 20)
    time.sleep(1)

    # Text option
    pyautogui.click(240, 100)
    time.sleep(1)

    # Type text
    pyautogui.write(text_to_write)

    # exit the text box
    pyautogui.press('esc')

