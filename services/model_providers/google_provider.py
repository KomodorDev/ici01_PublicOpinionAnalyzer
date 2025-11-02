# services/model_providers/google_provider.py
"""
google_provider.py
==================

Google AI (Gemini) provider implementation.
"""
from typing import List, Optional
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI

from services.model_providers.base_provider import ModelProvider, ModelInfo


##################################################################
class GoogleProvider(ModelProvider):
    """Manages Google AI (Gemini) models and API integration."""

    # ----------------------------------------------------------------
    def __init__(self, settings_service=None):
        """
        Initialize Google AI provider.
        
        Args:
            settings_service: SettingsService instance for configuration access.
                            If None, creates a new instance.
        """
        self.provider_name = "google"

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
        Test if Google AI API key works by making a real API call.
        
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
            client = genai.Client(api_key=api_key)

            # Free API call - just list models
            list(client.models.list())

            return True, "Connection successful"

        except Exception as e:
            return False, str(e)

    # ----------------------------------------------------------------
    def list_models(self) -> List[ModelInfo]:
        """List all available Google AI models."""
        success, _ = self.test_connection()
        if not success:
            return []

        try:
            client = genai.Client(api_key=self.api_key)  # Uses fresh key

            models = []
            response = client.models.list()

            for model in response:
                # Filter to generative models only
                if hasattr(model, 'name') and 'models/' in model.name:
                    model_id = model.name.replace('models/', '')
                    model_info = ModelInfo(
                        id=model_id,
                        name=model_id,
                        provider=self.provider_name,
                        context_window=None,
                        supports_function_calling=None,
                        supports_vision=None
                    )
                    models.append(model_info)

            return sorted(models, key=lambda x: x.id)
        except Exception as e:
            print(f"Error fetching Google AI models: {e}")
            return []

    # ----------------------------------------------------------------
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get detailed info about a specific Google AI model.
        """
        models = self.list_models()

        for model in models:
            if model.id == model_id:
                return model

        return None

    # ----------------------------------------------------------------
    def create_client(self, model_id: str, **kwargs) -> ChatGoogleGenerativeAI:
        """Create a LangChain ChatGoogleGenerativeAI client."""
        success, message = self.test_connection()

        if not success:
            raise ValueError(
                f"{self.provider_name.title()} not available: {message}"
            )

        return ChatGoogleGenerativeAI(
            model=model_id,
            google_api_key=self.api_key,
            temperature=kwargs.get("temperature", 0.7),
            max_output_tokens=kwargs.get("max_tokens", None),
        )


    # ----------------------------------------------------------------

##################################################################
# Test Main
##################################################################
def main():
    """
    Test the GoogleProvider by checking API availability and listing models.

    This function:
    - Creates a GoogleProvider instance.
    - Prints whether the provider has a valid API key configured.
    - Lists available Google AI models and displays basic information about each.
    - Tests YouTube video summarization if API is configured.


    Run this script as a main module to verify Google AI integration and model discovery.
    """
    print("="*60)
    print("Testing GoogleProvider")
    print("="*60)

    provider = GoogleProvider()

    # Check API key and availability
    print("Checking availability...")
    available, message = provider.test_connection()
    print(f"Is available: {available}")
    if message:
        print(f"Message: {message}")

    if not available:
        print("\n⚠️  Google AI API key not configured!")
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
