# controllers/settings_controller.py
"""
settings_controller.py
======================

Controller for managing the Advanced Settings interface.

Coordinates between SettingsView and SettingsService to handle:
- API key display and updates (with masking for security)
- Local provider URL configuration
- Settings validation and persistence
"""

from views.settings_view import SettingsView
from services.settings_service import SettingsService


##################################################################
class SettingsController:
    """Handles logic and coordination for the Advanced Settings tab."""

    # ----------------------------------------------------------------
    def __init__(self):
        """Initialize the settings controller with service and view."""
        self.settings_service = SettingsService()
        self.settings_view = SettingsView(self)

    # ----------------------------------------------------------------
    def render_settings_view(self):
        """
        Render the settings view with current configuration.

        Fetches current settings from the service and delegates
        rendering to the view component.
        """
        # Get masked API keys for display
        masked_keys = self.settings_service.get_all_masked_api_keys()

        # Get provider URLs
        lmstudio_url = self.settings_service.get_provider_url("lmstudio")
        ollama_url = self.settings_service.get_provider_url("ollama")

        # Get provider statuses
        provider_statuses = self.settings_service.get_all_provider_statuses()

        # Delegate to view with data
        self.settings_view.render_settings_view(
            masked_keys=masked_keys,
            lmstudio_url=lmstudio_url,
            ollama_url=ollama_url,
            provider_statuses=provider_statuses,
        )

    # ----------------------------------------------------------------
    def update_api_key(self, provider_name: str, api_key: str) -> tuple[bool, str]:
        """
        Update API key for a provider with validation.

        Args:
            provider_name: Provider identifier (e.g., "openai", "anthropic")
            api_key: New API key value

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Validate format first
        is_valid, error_msg = self.settings_service.validate_api_key_format(
            provider_name, api_key
        )

        if not is_valid:
            return False, error_msg

        # Save the key
        success = self.settings_service.set_api_key(provider_name, api_key)

        if success:
            return True, f"{provider_name.title()} API key saved successfully!"
        else:
            return False, f"Failed to save {provider_name} API key."

    # ----------------------------------------------------------------
    def update_provider_url(self, provider_name: str, url: str) -> tuple[bool, str]:
        """
        Update base URL for a local provider with validation.

        Args:
            provider_name: Provider identifier (e.g., "lmstudio", "ollama")
            url: New base URL

        Returns:
            Tuple of (success: bool, message: str)
        """
        success = self.settings_service.set_provider_url(provider_name, url)

        if success:
            return True, f"{provider_name.title()} URL updated successfully!"
        else:
            return (
                False,
                f"Failed to update {provider_name} URL. Check format (must start with http:// or https://).",
            )


##################################################################
