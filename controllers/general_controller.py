# Handles logic for "General" tab
# controllers/general_controller.py
from views.general_view import GeneralView
from services.general_service import GeneralService

class GeneralController:
    """Handles logic and coordination for the General tab."""

    def __init__(self):
        # Explicit and self-documenting instance names
        self.general_service = GeneralService()
        self.general_view = GeneralView()

    def render_general_view(self):
        """Get data from service, pass it to view for display."""
        # Ask service for data then give it to view:
        # Available Models
        # Available Label Groups

        self.general_view.render_general_view()
