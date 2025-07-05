import pyautogui
import time

print("Move your mouse to desired position. Press Ctrl+C to stop.\n")
try:
    while True:
        x, y = pyautogui.position()
        print(f"X: {x} Y: {y}", end="\r")  # prints in-place
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nStopped.")
