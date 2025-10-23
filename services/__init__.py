"""
controllers package
-------------------
Holds all controller classes responsible for app coordination.
Each controller connects Views (Gradio UI) with backend Services.
"""

from .general_service import GeneralService

# Define what’s publicly importable from this package
__all__ = ["GeneralService"]
