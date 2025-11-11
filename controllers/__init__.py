"""
controllers package
-------------------
Holds all controller classes responsible for app coordination.
Each controller connects Views (Gradio UI) with backend Services.
"""

from .app_controller import AppController
from .general_controller import GeneralController
from .classification_controller import ClassificationController
from .settings_controller import SettingsController
from .prompt_template_controller import PromptTemplateController    
# Future controllers can be implemented later:

# Define what’s publicly importable from this package
__all__ = ["AppController", "GeneralController", "ClassificationController", "SettingsController", "PromptTemplateController"]
