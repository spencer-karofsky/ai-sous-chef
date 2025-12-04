"""
ui_new/constants.py

Description:
    * Shared constants for AI Sous Chef UI (Clean minimal design)

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""

# Colors - Clean minimal palette
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

# Screen dimensions for 7" RPi display (rotated)
WIDTH = 1280
HEIGHT = 720

# Navigation bar
NAV_HEIGHT = 85
NAV_ICON_SIZE = 28
NAV_ITEMS = ['Home', 'Search', 'Favorites', 'Create', 'Settings']

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

# Typography sizes
FONT_TITLE = 48
FONT_HEADER = 32
FONT_BODY = 26
FONT_SMALL = 22
FONT_CAPTION = 18

# Font names - will try in order until one works
FONT_SANS = [
    "SF Pro Display",      # macOS
    "Segoe UI",            # Windows
    "Roboto",              # Linux/Android
    "DejaVu Sans",         # Linux fallback
    "FreeSans",            # Linux fallback
    "Arial",               # Universal fallback
    None                   # Pygame default
]