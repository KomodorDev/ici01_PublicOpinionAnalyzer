
# controllers/general_controller.py
"""
general_controller.py
================

Handles logic for the "General" tab.
"""
from views.general_view import GeneralView
from services.general_service import GeneralService
from services.model_service import ModelService
from services.classification_service import ClassificationService


##################################################################
class GeneralController:
    """Handles logic and coordination for the General tab."""

    # ----------------------------------------------------------------
    def __init__(self):
        # Explicit and self-documenting instance names
        self.general_service = GeneralService()
        self.general_view = GeneralView()
        # model service provides a unified view of available LLM models
        self.model_service = ModelService()
        # classification service provides label groups stored on disk
        self.classification_service = ClassificationService()

    # ----------------------------------------------------------------
    def render_general_view(self):
        """Get data from service, pass it to view for display."""
        # Ask service for data then give it to view:
        # - Available Models (from ModelService)
        # - Available Label Groups (from GeneralService, if implemented)

        # Fetch available models and pass them to the view. ModelService
        # returns a list of ModelInfo objects; the view will extract
        # display names/ids as needed.
        models = self.model_service.list_all_models()

        # Load classification groups and extract names for the view
        try:
            groups = self.classification_service.load_all_groups()
            group_names = [g.name for g in groups]
        except (FileNotFoundError, RuntimeError, OSError):
            group_names = []

        self.general_view.render_general_view(models=models, groups=group_names)

    # ----------------------------------------------------------------


##################################################################
