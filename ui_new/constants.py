"""
ui_new/constants.py

Description:
    * Shared constants for AI Sous Chef UI (Clean minimal design)

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
# Colors
WHITE = (255, 255, 255)
OFF_WHITE = (250, 250, 250)
CREAM = (248, 247, 245)
LIGHT_GRAY = (245, 245, 245)
MID_GRAY = (180, 180, 180)
DARK_GRAY = (120, 120, 120)
CHARCOAL = (60, 60, 60)
SOFT_BLACK = (35, 35, 35)
BLACK = (20, 20, 20)

# Accent colors
ACCENT = (45, 45, 45)
ACCENT_LIGHT = (100, 100, 100)
DIVIDER = (230, 230, 230)

# App color palette
SAGE = (142, 157, 139)
SAGE_LIGHT = (227, 231, 226)
TEAL = (26, 94, 120)

# Navigation bar
NAV_BG = (227, 231, 226) # Light sage

# Keyboard colors
KB_BG = (45, 45, 48)
KB_KEY = (70, 70, 75)
KB_KEY_PRESSED = (100, 100, 105)
KB_KEY_SPECIAL = (55, 55, 60)

# Screen dimensions for 7" RPi display (rotated)
WIDTH = 1280
HEIGHT = 720

# Navigation bar
NAV_HEIGHT = 85
NAV_ICON_SIZE = 28
NAV_ITEMS = ['Home', 'Search', 'My Kitchen', 'Create', 'Settings']

# Keyboard layouts
KEYBOARD_LETTERS = [
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm'],
]

KEYBOARD_NUMBERS = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
    ['-', '/', ':', ';', '(', ')', '$', '&', '@', '"'],
    ['.', ',', '?', '!', "'", '#', '%', '^', '*'],
]

KEYBOARD_SYMBOLS = [
    ['[', ']', '{', '}', '#', '%', '^', '*', '+', '='],
    ['_', '\\', '|', '~', '<', '>', '@', '&', '"'],
    ['.', ',', '?', '!', "'", '-', '/', ':', ';'],
]

# Legacy layout (for backwards compatibility)
KEYBOARD_ROWS = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', "'"],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '?'],
]

KEYBOARD_HEIGHT = 360
KEY_WIDTH = 100
KEY_HEIGHT = 42
KEY_MARGIN = 5

# Typography sizes
FONT_TITLE = 48
FONT_HEADER = 32
FONT_BODY = 26
FONT_SMALL = 22
FONT_CAPTION = 18

# Font names
FONT_SANS = [
    "SF Pro Display",
    "Segoe UI",
    "Roboto",
    "DejaVu Sans",
    "FreeSans",
    "Arial",
    None
]