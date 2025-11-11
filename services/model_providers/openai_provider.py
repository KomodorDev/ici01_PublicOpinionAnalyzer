# services/model_providers/openai_provider.py
"""
openai_provider.py
==================

OpenAI provider implementation.
"""
from typing import List, Optional
from openai import OpenAI
from langchain_openai import ChatOpenAI

from services.model_providers.base_provider import ModelProvider
from models.llm_model_info_model import LLMModelInfo
from enums.provider_enum import ProviderEnum

OPENAI_LLM_KEYWORDS = ["gpt-", "gpt", "chatgpt", "turbo", "o1-"]
OPENAI_EXCLUDE_KEYWORDS = ["embedding", "moderation", "whisper", "audio", "dall-e", "vision"]


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
    def list_llm_models(self) -> List[LLMModelInfo]:
        """
        List all available LLM (chat/completion-capable) models from OpenAI.

        Returns:
            List[LLMModelInfo]: List of available LLM models.

        Note:
            Filtering uses keywords that match known OpenAI LLMs and excludes 
            likely non-LLMs (embeddings, audio, vision, moderation, etc.).
            This should be updated as OpenAI introduces new models.
        """
        success, _ = self.test_connection()
        if not success:
            return []

        try:
            client = OpenAI(api_key=self.api_key)  # Uses fresh key
            models = []
            response = client.models.list()

            for model in response.data:
                model_id = model.id.lower()

                # Only include models with LLM keywords and exclude certain types
                if (any(kw in model_id for kw in OPENAI_LLM_KEYWORDS) and
                    not any(kw in model_id for kw in OPENAI_EXCLUDE_KEYWORDS)):
                    
                    models.append(
                        LLMModelInfo(
                            name=model.id,  # Use canonical model id (e.g., "gpt-4")
                            provider=ProviderEnum.OPENAI,
                            display_name=model.id,
                            description="OpenAI chat/completion model",
                            context_window=None,  # If available, add with model.get("context_length")
                            supports_function_calling=None,  # Set True if known for model
                            supports_vision=None,  # Set True for gpt-4-vision if desired
                            favorite=False,
                            is_local=False
                        )
                    )

            return sorted(models, key=lambda x: x.name)
        except Exception as e:
            print(f"Error fetching OpenAI LLM models: {e}")
            return []

    # ----------------------------------------------------------------
    def get_llm_model_info(self, model_name: str) -> Optional[LLMModelInfo]:
        """
        Get detailed info about a specific OpenAI model.
        
        Note: OpenAI API doesn't provide model capabilities metadata.
        This returns basic info only. To be implemented with static mappings later.
        """
        models = self.list_llm_models()

        for model in models:
            if model.name == model_name:
                return model

        return None

    # ----------------------------------------------------------------
    def create_llm_client(self, model_name: str, **kwargs) -> ChatOpenAI:
        """Create a LangChain ChatOpenAI client."""
        success, message = self.test_connection()

        if not success:
            raise ValueError(
                f"{self.provider_name.title()} not available: {message}"
            )

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
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
    models = provider.list_llm_models()
    print(f"Found {len(models)} models.")
    for i, model in enumerate(models, 1):
        print(f"\n  {i}. {model.name}")
        print(f"     ID: {model.id}")
        print(f"     Provider: {model.provider}")
        print(f"     Context Window: {model.context_window}")
        print(f"     Function Calling: {model.supports_function_calling}")
        print(f"     Vision: {model.supports_vision}")

    # Test actual model inference
    print("\n" + "="*60)
    print("Testing Model Inference")
    print("="*60)

    # Use a simple, reliable model (gpt-3.5-turbo or gpt-4o-mini)
    test_model = "gpt-4o-mini"  # Fast and cheap for testing

    print(f"\nTesting model: {test_model}")
    print("Sending test query: 'What is 2+2? Answer with just the number.'")

    try:
        # Create client
        client = provider.create_client(
            model_id=test_model,
            temperature=0.0,  # Deterministic for testing
            max_tokens=10
        )

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
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

if __name__ == "__main__":
    main()

# python -m services.model_providers.openai_provider
