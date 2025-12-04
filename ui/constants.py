"""
ui/constants.py

Description:
    * Shared constants for AI Sous Chef UI

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""

# Colors - Sleek Blue theme
BLUE_DARK = (13, 27, 42)
BLUE_MID = (27, 38, 59)
BLUE_LIGHT = (41, 51, 82)
CREAM = (255, 253, 240)
GOLD = (212, 175, 55)
GOLD_DARK = (170, 140, 44)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (180, 180, 180)
RED_SOFT = (198, 86, 86)
ACCENT = (100, 149, 237)

# Screen dimensions for 7" RPi display (rotated)
WIDTH = 1280
HEIGHT = 720

# Keyboard layout
KEYBOARD_ROWS = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', "'"],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '?'],
]
KEYBOARD_HEIGHT = 295
KEY_WIDTH = 100
KEY_HEIGHT = 50
KEY_MARGIN = 5