#!/usr/bin/env python3
"""
run_new.py

Description:
    * Entry point for AI Sous Chef (Clean minimal UI)

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
from ui_new.app import RecipeApp


def main():
    app = RecipeApp()
    app.run()


if __name__ == '__main__':
    main()