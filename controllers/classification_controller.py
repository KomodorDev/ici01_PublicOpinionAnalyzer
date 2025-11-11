# Handles "Label Groups" tab
# Handles logic for "Classification" tab
# controllers/classification_controller.py
from views.classification_view import ClassificationView
from services.classification_service import ClassificationService


##################################################################
class ClassificationController:
    """Handles logic and coordination for the Classification management tab."""

    # ----------------------------------------------------------------
    def __init__(self):
        self.classification_service = ClassificationService()
        self.classification_view = ClassificationView()

    # ----------------------------------------------------------------
    def render_classification_view(self):
        """Load classification groups from service and render the view."""
        # Load all classification groups from disk
        groups = self.classification_service.load_all_classification_groups()

        # Pass data to view for display
        self.classification_view.render_classification_view(groups)

    # ----------------------------------------------------------------

##################################################################
