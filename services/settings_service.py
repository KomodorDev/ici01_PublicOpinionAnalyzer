# services/settings_service.py
"""
settings_service.py
===================

Central service for application settings management.
Provides business logic layer on top of Config module.
"""

from typing import Any, Dict, Optional
import json
from config import Config, API_PROVIDERS, LOCAL_PROVIDERS

from services.model_providers.openai_provider import OpenAIProvider
from services.model_providers.lmstudio_provider import LMStudioProvider


##################################################################
class SettingsService:
    """
    Manages application settings with validation and business logic.
    
    Acts as intermediary between UI/controllers and low-level Config.
    """

    # ----------------------------------------------------------------
    def __init__(self):
        """Initialize the settings service."""

    # ----------------------------------------------------------------
    # API Key Management
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    def get_api_key(self, provider_name: str) -> str:
        """
        Get API key for a provider.
        
        Args:
            provider_name: Provider identifier (e.g., "openai", "anthropic")
            
        Returns:
            API key string (may be placeholder "API_KEY" if not configured)
        """
        return Config.get_api_key(provider_name)

    # ----------------------------------------------------------------
    def get_masked_api_key(self, provider_name: str) -> str:
        """
        Get masked API key for display purposes.
        
        Shows first 4 and last 4 characters with asterisks in between.
        Example: "sk-1234***********7890" or "API_KEY" if not configured.
        
        Args:
            provider_name: Provider identifier
            
        Returns:
            Masked API key string
        """
        key = self.get_api_key(provider_name)

        if key == "API_KEY" or not key:
            return "API_KEY"

        # Mask the middle part
        if len(key) <= 8:
            return "****"

        visible_chars = 4
        prefix = key[:visible_chars]
        suffix = key[-visible_chars:]
        masked_middle = "*" * (len(key) - (2 * visible_chars))

        return f"{prefix}{masked_middle}{suffix}"

    # ----------------------------------------------------------------
    def set_api_key(self, provider_name: str, api_key: str) -> bool:
        """
        Set API key for a provider with validation.
        
        Args:
            provider_name: Provider identifier
            api_key: The API key to store
            
        Returns:
            True if successful, False otherwise
        """
        if provider_name not in API_PROVIDERS:
            print(f"Unknown provider: {provider_name}")
            return False

        if not api_key or api_key.strip() == "":
            print("API key cannot be empty")
            return False

        return Config.set_api_key(provider_name, api_key.strip())

    # ----------------------------------------------------------------
    def is_provider_configured(self, provider_name: str) -> bool:
        """
        Check if a provider has an API key configured (lightweight check).
        
        Args:
            provider_name: Provider identifier
            
        Returns:
            True if provider has API key set, False otherwise
        """
        return Config.is_key_configured(provider_name)

    # ----------------------------------------------------------------
    def is_provider_available(self, provider_name: str) -> tuple[bool, str]:
        """
        Check if a provider is actually available by testing the connection.
        
        This makes an actual API call to verify the key works.
        
        Args:
            provider_name: Provider identifier (e.g., "openai", "anthropic")
            
        Returns:
            Tuple of (is_available: bool, message: str)
        """

        # Get the provider and test connection
        try:
            if provider_name == "openai":

                provider = OpenAIProvider(self)
                return provider.test_connection()

            elif provider_name == "lmstudio":

                provider = LMStudioProvider(self)
                return provider.test_connection()

            else:
                return False, f"Unknown provider: {provider_name}"

        except Exception as e:
            return False, f"Error testing {provider_name}: {str(e)}"

    # ----------------------------------------------------------------
    def get_all_masked_api_keys(self) -> Dict[str, str]:
        """
        Get all API keys with masking for display.
        
        Returns:
            Dictionary mapping provider names to masked API keys
        """
        return {
            provider: self.get_masked_api_key(provider)
            for provider in API_PROVIDERS.keys()
        }

    # ----------------------------------------------------------------
    # Local Provider Configuration
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    def get_provider_url(self, provider_name: str) -> Optional[str]:
        """
        Get base URL for a local provider.
        
        Args:
            provider_name: Provider identifier (e.g., "lmstudio", "ollama")
            
        Returns:
            Base URL string, or None if provider not found
        """
        return Config.get_local_provider_url(provider_name)

    # ----------------------------------------------------------------
    def set_provider_url(self, provider_name: str, url: str) -> bool:
        """
        Set base URL for a local provider with validation.
        
        Args:
            provider_name: Provider identifier
            url: Base URL to set
            
        Returns:
            True if successful, False otherwise
        """
        if provider_name not in LOCAL_PROVIDERS:
            print(f"Unknown local provider: {provider_name}")
            return False

        if not url or not url.strip():
            print("URL cannot be empty")
            return False

        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            print("URL must start with http:// or https://")
            return False

        if url.endswith("/"):
            url = url[:-1]

        return Config.set_local_provider_url(provider_name, url)

    # ----------------------------------------------------------------
    # Provider Status
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    def get_all_provider_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get comprehensive status of all providers.
        
        Returns:
            Dictionary with provider status information
        """
        statuses: Dict[str, Dict[str, Any]] = {}

        # --- API providers ---
        for provider in API_PROVIDERS.keys():
            status, message = self.is_provider_available(provider)
            statuses[provider] = {
                "available": status,                     # bool only
                "message": message,                      # detail string
                "masked_key": self.get_masked_api_key(provider),
                "type": "api",
            }

        # --- Local providers ---
        for provider in LOCAL_PROVIDERS.keys():
            status, message = self.is_provider_available(provider)
            statuses[provider] = {
                "available": status,                     # bool only
                "message": message,
                "url": self.get_provider_url(provider),
                "type": "local",
            }

        # Debug print (optional)
        print(json.dumps(statuses, indent=2))

        return statuses

    # ----------------------------------------------------------------
    def get_available_providers(self) -> list[str]:
        """
        Get list of provider names that are configured and ready to use.
        
        Returns:
            List of provider names
        """
        available = []

        for provider in API_PROVIDERS.keys():
            status, _ = self.is_provider_available(provider)
            if status:
                available.append(provider)

        for provider in LOCAL_PROVIDERS.keys():
            status, _ = self.is_provider_available(provider)
            if status:
                available.append(provider)

        return available

    # ----------------------------------------------------------------
    # Validation Helpers
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    def validate_api_key_format(self, provider_name: str, api_key: str) -> tuple[bool, str]:
        """
        Validate API key format for a specific provider.
        
        Args:
            provider_name: Provider identifier
            api_key: API key to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not api_key or api_key.strip() == "":
            return False, "API key cannot be empty"

        key = api_key.strip()

        if provider_name == "openai":
            if not key.startswith("sk-"):
                return False, "OpenAI API keys should start with 'sk-'"
            if len(key) < 20:
                return False, "OpenAI API key seems too short"

        elif provider_name == "anthropic":
            if not key.startswith("sk-ant-"):
                return False, "Anthropic API keys should start with 'sk-ant-'"

        elif provider_name == "google":
            if len(key) < 30:
                return False, "Google API key seems too short"

        return True, ""


##################################################################
# Test Main
##################################################################
def main():
    """Test the SettingsService functionality."""
    print("="*60)
    print("Testing SettingsService")
    print("="*60)

    # Create service instance
    settings = SettingsService()

    # Test provider statuses
    print("\nProvider Statuses:")
    statuses = settings.get_all_provider_statuses()
    for provider, info in statuses.items():
        status_icon = "✓" if info["available"] else "⚠"
        print(f"\n  {status_icon} {provider.upper()} ({info['type']})")
        if info["type"] == "api":
            print(f"     Key: {info['masked_key']}")
        else:
            print(f"     URL: {info['url']}")

    # Test available providers
    print("\n" + "-"*60)
    print("Available Providers:")
    available = settings.get_available_providers()
    if available:
        for provider in available:
            print(f"  ✓ {provider}")
    else:
        print("  ⚠ No providers available")

    # Test masked keys
    print("\n" + "-"*60)
    print("Masked API Keys:")
    masked_keys = settings.get_all_masked_api_keys()
    for provider, masked_key in masked_keys.items():
        configured = "✓" if masked_key != "API_KEY" else "⚠"
        print(f"  {configured} {provider}: {masked_key}")

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)


if __name__ == "__main__":
    main()
