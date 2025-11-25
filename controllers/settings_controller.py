# controllers/settings_controller.py
"""
settings_controller.py
======================

Controller for managing the Advanced Settings interface.

Coordinates between SettingsView and SettingsService to handle:
- API key display and updates (with masking for security)
- Local provider URL configuration
- Settings validation and persistence

Follows the same pattern as AnalysisController:
- Builds ViewModel from service data
- Defines on_xxx_clicked callbacks that return ViewModels
- Passes ViewModel and callbacks to view
"""

from views.settings_view import SettingsView
from services.settings_service import SettingsService
from models.view_models.settings import SettingsViewModel


##################################################################
class SettingsController:
    """Handles logic and coordination for the Advanced Settings tab."""

    # ----------------------------------------------------------------
    def __init__(self):
        """Initialize the settings controller with service and view."""
        self.settings_service = SettingsService()
        self.settings_view = SettingsView()

    # ================================================================
    # Initial / full view render
    # ================================================================
    def render_settings_view(self):
        """
        Build initial SettingsViewModel for the current controller state
        and render the view with wireback callbacks.
        """
        # Build ViewModel from service data
        vm = self._build_settings_view_model()

        # Delegate to view with ViewModel and wireback callbacks
        self.settings_view.render_settings_view(
            view_model=vm,
            on_api_key_saved=self.on_api_key_saved,
            on_provider_url_saved=self.on_provider_url_saved,
        )

    # ================================================================
    # Callbacks wired by the view
    # ================================================================
    # ----------------------------------------------------------------
    def on_api_key_saved(self, provider_name: str, api_key: str) -> SettingsViewModel:
        """
        Save an API key and return updated SettingsViewModel.
        
        Args:
            provider_name: Provider identifier (e.g., "openai", "anthropic")
            api_key: New API key value
            
        Returns:
            Updated SettingsViewModel with new masked keys and statuses
        """
        # Validate format first
        is_valid, error_msg = self.settings_service.validate_api_key_format(
            provider_name, api_key
        )

        if not is_valid:
            # Return ViewModel with error message
            vm = self._build_settings_view_model()
            vm.error_message = f"❌ {error_msg}"
            return vm

        # Save the key
        success = self.settings_service.set_api_key(provider_name, api_key)

        if not success:
            vm = self._build_settings_view_model()
            vm.error_message = f"❌ Failed to save {provider_name} API key."
            return vm

        # Success - rebuild ViewModel with updated statuses
        vm = self._build_settings_view_model()
        vm.info_message = f"✅ {provider_name.title()} API key saved successfully!"
        return vm

    # ----------------------------------------------------------------
    def on_provider_url_saved(self, provider_name: str, url: str) -> SettingsViewModel:
        """
        Save a provider URL and return updated SettingsViewModel.
        
        Args:
            provider_name: Provider identifier (e.g., "lmstudio", "ollama")
            url: New base URL
            
        Returns:
            Updated SettingsViewModel with new URL and statuses
        """
        success = self.settings_service.set_provider_url(provider_name, url)

        if not success:
            vm = self._build_settings_view_model()
            vm.error_message = (
                f"❌ Failed to update {provider_name} URL. "
                f"Check format (must start with http:// or https://)."
            )
            return vm

        # Success - rebuild ViewModel with updated statuses
        vm = self._build_settings_view_model()
        vm.info_message = f"✅ {provider_name.title()} URL updated successfully!"
        return vm

    # ================================================================
    # Helper methods
    # ================================================================
    # ----------------------------------------------------------------
    def _build_settings_view_model(self) -> SettingsViewModel:
        """
        Build SettingsViewModel from current service state.
        
        Returns:
            SettingsViewModel with current masked keys, URLs, and statuses
        """
        # Get masked API keys for display
        masked_keys = self.settings_service.get_all_masked_api_keys()

        # Get provider URLs
        lmstudio_url = self.settings_service.get_provider_url("lmstudio")
        ollama_url = self.settings_service.get_provider_url("ollama")

        # Get provider statuses
        provider_statuses = self.settings_service.get_all_provider_statuses()

        return SettingsViewModel(
            masked_api_keys=masked_keys,
            lmstudio_url=lmstudio_url,
            ollama_url=ollama_url,
            provider_statuses=provider_statuses,
            info_message=None,
            error_message=None,
        )


##################################################################
