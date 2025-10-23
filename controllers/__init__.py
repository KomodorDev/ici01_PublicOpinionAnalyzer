"""
controllers package
-------------------
Holds all controller classes responsible for app coordination.
Each controller connects Views (Gradio UI) with backend Services.
"""

from .app_controller import AppController

# Define what’s publicly importable from this package
__all__ = ["AppController"]