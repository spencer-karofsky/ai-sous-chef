"""
run.py

Description:
    * Entry point for AI Sous Chef application

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
from ui.recipe_app import RecipeApp


def main():
    app = RecipeApp()
    app.run()


if __name__ == '__main__':
    main()