"""
main.py

Description:
    * AI Sous Chef - Recipe search and generation

Instructions:
    * Run via CLI:
        python main.py # Start recipe search
        python main.py search # Start recipe search (same, but explicit)

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import sys
from recipe_search import recipe_search

def search():
    """Interactive recipe search"""
    recipe_search()

if __name__ == "__main__":
    commands = {
        "search": search,
    }

    command = sys.argv[1] if len(sys.argv) > 1 else "search"

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands.keys())}")