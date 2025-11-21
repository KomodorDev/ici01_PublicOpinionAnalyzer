# services/model_providers/google_provider.py
"""
google_provider.py
==================

Google AI (Gemini) provider implementation.
"""

import traceback

from typing import List, Optional
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI

from enums import ProviderEnum
from services.model_providers.base_provider import ModelProvider
from models.domain import LLMModelInfo


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
        self.provider_name = str(ProviderEnum.GOOGLE)

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
    def list_llm_models(self) -> List[LLMModelInfo]:
        """List all available Google AI models."""
        success, _ = self.test_connection()
        if not success:
            return []

        try:
            client = genai.Client(api_key=self.api_key)  # Uses fresh key

            models = []
            response = client.models.list()

            for model in response:
                print(model)

            for model in response:
                # Filter to generative models only
                if hasattr(model, 'name') and 'models/' in model.name:
                    model_id = model.name.replace('models/', '')
                    model_info = LLMModelInfo(
                        name=model_id,
                        provider=self.provider_name,
                        context_window=None,
                        supports_function_calling=None,
                        supports_vision=None
                    )
                    models.append(model_info)

            return sorted(models, key=lambda x: x.name)
        except Exception as e:
            print(f"Error fetching Google AI models: {e}")
            return []

    # ----------------------------------------------------------------
    def get_llm_model_info(self, model_name: str) -> Optional[LLMModelInfo]:
        """
        Get detailed info about a specific Google AI model.
        """
        models = self.list_llm_models()

        for model in models:
            if model.name == model_name:
                return model

        return None

    # ----------------------------------------------------------------
    def create_llm_client(self, model_name: str, **kwargs) -> ChatGoogleGenerativeAI:
        """Create a LangChain ChatGoogleGenerativeAI client."""
        success, message = self.test_connection()

        if not success:
            raise ValueError(
                f"{self.provider_name.title()} not available: {message}"
            )

        client = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.api_key,
            temperature=kwargs.get("temperature", 0.7),
            max_output_tokens=kwargs.get("max_tokens", None),
        )

        client.name = f"{self.provider_name}_{model_name}"   # "openai:gpt-4o-mini"

        return client

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
    models = provider.list_llm_models()
    print(f"Found {len(models)} models.")
    for i, model in enumerate(models, 1):
        print(f"\n  {i}. {model.name}")
        print(f"     ID: {model.name}")
        print(f"     Provider: {model.provider}")
        print(f"     Context Window: {model.context_window}")
        print(f"     Function Calling: {model.supports_function_calling}")
        print(f"     Vision: {model.supports_vision}")

    # Test actual model inference
    print("\n" + "="*60)
    print("Testing Model Inference")
    print("="*60)

    # Use a simple, reliable model
    test_model = "gemini-2.0-flash"  # Fast and cheap for testing

    print(f"\nTesting model: {test_model}")
    print("Sending test query: 'What is 2+2? Answer with just the number.'")

    try:
        # Create client
        client = provider.create_llm_client(
            model_name=test_model,
            temperature=0.0,  # Deterministic for testing
            max_tokens=10
        )
        # -----------------------------------------
        # DEBUG: Print all attributes of the client
        # -----------------------------------------
        print("\nDEBUG: ChatGoogleGenerativeAI client attributes")
        print("type:", type(client))

        # Print __dict__ if available
        if hasattr(client, "__dict__"):
            print("\nclient.__dict__:")
            for k, v in client.__dict__.items():
                print(f"  {k}: {v}")
        else:
            print("\nclient has no __dict__, printing dir() instead:")
            for attr in dir(client):
                try:
                    val = getattr(client, attr)
                    print(f"  {attr}: {val}")
                except Exception:
                    print(f"  {attr}: <error retrieving value>")
        # -----------------------------------------

        # Make a simple request
        response = client.invoke("What is 2+2? Answer with just the number.")

        print("\n✅ Model Response:")
        print("-" * 60)
        print(response.content)
        print("-" * 60)

        # Verify response is reasonable
        if response.content and len(response.content) > 0:
            print("\n✅ Model inference test PASSED!")
            print(f"   Response length: {len(response.content)} characters")
        else:
            print("\n⚠️  Warning: Model returned empty response")

    except Exception as e:
        print(f"\n❌ Model inference test FAILED!")
        print(f"   Error: {str(e)}")

        traceback.print_exc()

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

if __name__ == "__main__":
    main()

# python -m services.model_providers.google_provider
