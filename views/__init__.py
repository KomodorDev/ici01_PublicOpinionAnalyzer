"""
views package
-------------------
Holds all view classes responsible for app coordination.

"""

from .general_view import GeneralView
from .classification_view import ClassificationView
from .settings_view import SettingsView
from .prompt_template_view import PromptTemplateView

# Define what’s publicly importable from this package
__all__ = ["GeneralView", "ClassificationView", "SettingsView", "PromptTemplateView"]
