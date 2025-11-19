"""
controllers package
-------------------
Holds all controller classes responsible for app coordination.
Each controller connects Views (Gradio UI) with backend Services.
"""

from .app_controller import AppController
from .analysis_controller import AnalysisController
from .classification_controller import ClassificationController
from .settings_controller import SettingsController
from .prompt_template_controller import PromptTemplateController

# Define what’s publicly importable from this package
__all__ = ["AppController", "AnalysisController", "ClassificationController", "SettingsController", "PromptTemplateController"]
