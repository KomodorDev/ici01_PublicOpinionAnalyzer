from views.settings_view import SettingsView
from services.settings_service import SettingsService


##################################################################
class SettingsController:
    """Handles logic and coordination for the Advanced Settings tab."""

    # ----------------------------------------------------------------
    def __init__(self):
        # Consistent, explicit naming pattern for clarity and maintainability
        self.settings_service = SettingsService()
        self.settings_view = SettingsView(self.settings_service)

    # ----------------------------------------------------------------
    def render_settings_view(self):
        """Delegate rendering to the view component."""
        self.settings_view.render_settings_view()

##################################################################
