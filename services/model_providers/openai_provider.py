# services/model_providers/openai_provider.py
"""
openai_provider.py
==================

OpenAI provider implementation.
"""
from typing import List, Optional
from openai import OpenAI
from langchain_openai import ChatOpenAI

from services.model_providers.base_provider import ModelProvider, ModelInfo


##################################################################
class OpenAIProvider(ModelProvider):
    """Manages OpenAI models and API integration."""

    # ----------------------------------------------------------------
    def __init__(self, settings_service=None):
        """
        Initialize OpenAI provider.
        
        Args:
            settings_service: SettingsService instance for configuration access.
                            If None, creates a new instance.
        """
        self.provider_name = "openai"

        # Use provided settings service or create new one
        if settings_service is None:
            from services.settings_service import SettingsService   # pylint: disable=import-outside-toplevel
            settings_service = SettingsService()

        self.settings_service = settings_service

    # ----------------------------------------------------------------
    @property
    def api_key(self):
        """Always get fresh API key from config."""
        return self.settings_service.get_api_key(self.provider_name)

    # ----------------------------------------------------------------
    def test_connection(self, api_key: str = None) -> tuple[bool, str]:
        """
        Test if OpenAI API key works by making a real API call.
        
        Args:
            api_key: Optional API key to test. If None, uses stored key.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Get key to test
        if api_key is None:
            if not self.settings_service.is_provider_configured(self.provider_name):
                return False, "API key not configured"
            api_key = self.settings_service.get_api_key(self.provider_name)

        # Test the key
        try:
            client = OpenAI(api_key=api_key)

            # Free API call - just list models
            client.models.list()

            return True, "Connection successful"

        except Exception as e:
            return False, str(e)


    # ----------------------------------------------------------------
    def list_models(self) -> List[ModelInfo]:
        """List all available OpenAI models."""
        success, _ = self.test_connection()
        if not success:
            return []

        try:
            client = OpenAI(api_key=self.api_key)  # Uses fresh key

            models = []
            response = client.models.list()

            for model in response.data:
                # Filter to chat/completion models only
                if any(keyword in model.id for keyword in ["gpt-", "o1-", "chatgpt"]):
                    model_info = ModelInfo(
                        id=model.id,
                        name=model.id,
                        provider=self.provider_name,
                        context_window=None,
                        supports_function_calling=None,
                        supports_vision=None,
                    )
                    models.append(model_info)

            return sorted(models, key=lambda x: x.id)
        except Exception as e:
            print(f"Error fetching OpenAI models: {e}")
            return []

    # ----------------------------------------------------------------
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get detailed info about a specific OpenAI model.
        
        Note: OpenAI API doesn't provide model capabilities metadata.
        This returns basic info only. To be implemented with static mappings later.
        """
        models = self.list_models()

        for model in models:
            if model.id == model_id:
                return model

        return None

    # ----------------------------------------------------------------
    def create_client(self, model_id: str, **kwargs) -> ChatOpenAI:
        """Create a LangChain ChatOpenAI client."""
        success, message = self.test_connection()

        if not success:
            raise ValueError(
                f"{self.provider_name.title()} not available: {message}"
            )

        return ChatOpenAI(
            model=model_id,
            api_key=self.api_key,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", None),
        )

    # ----------------------------------------------------------------

##################################################################
# Test Main
##################################################################
def main():
    """
    Test the OpenAIProvider by checking API availability and listing models.

    This function:
    - Creates an OpenAIProvider instance.
    - Prints whether the provider has a valid API key configured.
    - Lists available OpenAI models and displays basic information about each.

    Run this script as a main module to verify OpenAI integration and model discovery.
    """
    print("="*60)
    print("Testing OpenAIProvider")
    print("="*60)

    provider = OpenAIProvider()

    # Check API key and availability
    print("Checking availability...")
    available, message = provider.test_connection()
    print(f"Is available: {available}")
    if message:
        print(f"Message: {message}")

    if not available:
        print("\n⚠️  OpenAI API key not configured!")
        print("Please configure your API key in Settings or .env file.")
        return

    print("\nListing models...")
    models = provider.list_models()
    print(f"Found {len(models)} models.")
    for i, model in enumerate(models, 1):
        print(f"\n  {i}. {model.name}")
        print(f"     ID: {model.id}")
        print(f"     Provider: {model.provider}")
        print(f"     Context Window: {model.context_window}")
        print(f"     Function Calling: {model.supports_function_calling}")
        print(f"     Vision: {model.supports_vision}")

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

if __name__ == "__main__":
    main()
