# services/model_providers/lmstudio_provider.py
"""
lmstudio_provider.py
====================

Local LM Studio provider — OpenAI-compatible API running on localhost.
"""

from typing import List, Optional
from langchain_openai import ChatOpenAI
import requests
from models.domain import LLMModelInfo
from services.model_providers.base_provider import ModelProvider


##################################################################
class LMStudioProvider(ModelProvider):
    """Lists locally served LM Studio models."""

    # ----------------------------------------------------------------
    def __init__(self, settings_service=None):
        """
        Initialize LM Studio provider.
        
        Args:
            settings_service: SettingsService instance for configuration access.
                            If None, creates a new instance.
        """
        self.provider = "lmstudio"

        # Use provided settings service or create new one
        if settings_service is None:
            from services.settings_service import SettingsService     # pylint: disable=import-outside-toplevel
            settings_service = SettingsService()

        self.settings_service = settings_service

    # ----------------------------------------------------------------
    @property
    def base_url(self):
        """Always get fresh URL from config."""
        return self.settings_service.get_provider_url(self.provider)

    # ----------------------------------------------------------------
    def test_connection(self, api_key: str | None = None) -> tuple[bool, str]:
        """Check if LM Studio is running locally (OpenAI-compatible /v1)."""
        url = f"{self.base_url}/models"  # e.g. http://localhost:1234/v1/models
        try:
            resp = requests.get(url, timeout=2)

            if resp.ok:
                # Try to say something useful in the message
                try:
                    data = resp.json()
                    # LM Studio typically returns {"data": [ {...}, ... ]}
                    models = data.get("data", data)
                    count = len(models) if isinstance(models, list) else "unknown"
                    return True, f"OK {resp.status_code} at {url}; models={count}"
                except ValueError:
                    # 200 but not JSON
                    return True, f"OK {resp.status_code} at {url}; non-JSON body"
            else:
                return False, f"HTTP {resp.status_code} at {url}"
        except requests.RequestException as e:
            return False, f"{type(e).__name__} at {url}: {e}"

    # ----------------------------------------------------------------
    def list_llm_models(self) -> List[LLMModelInfo]:
        """
        Fetch the list of LLM (language/chat) models from LM Studio's /v1/models endpoint.

        Returns:
            List[LLMModelInfo]: List of available LLMs from LM Studio.

        TODO:
            Implement proper filtering to exclude embedding, moderation, or other non-LLMs.
        """
        success, _ = self.test_connection()
        if not success:
            return []

        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            resp.raise_for_status()

            data = resp.json()
            models = []

            # LM Studio typically returns OpenAI-compatible format: {"data": [...], "object": "list"}
            model_list = data.get("data", [])

            for model in model_list:
                model_id = model.get("id", "")
                if not model_id:
                    continue
                # TODO: Properly filter out non-LLMs later!
                models.append(
                    LLMModelInfo(
                        name=model_id,
                        provider=self.provider,
                        display_name=f"{model_id} (local)",
                        description=model.get("description", ""),
                        context_window=model.get("context_length"),
                        favorite=False,
                        is_local=True
                    )
                )

            return models

        except requests.RequestException as e:
            print(f"Error fetching models from LM Studio: {e}")
            return []


    # ----------------------------------------------------------------
    def get_llm_model_info(self, model_name: str) -> Optional[LLMModelInfo]:
        """
        Get basic information about a specific model.
        
        Args:
            model_name: The model name (as in LLMModelInfo.name).

        Returns:
            ModelInfo object with model details, or None if not found.
        """
        models = self.list_llm_models()

        for model in models:
            if model.name == model_name:
                return model

        # Model not found
        return None

    # ----------------------------------------------------------------
    def create_llm_client(self, model_name: str, **kwargs):
        """Create a LangChain ChatOpenAI client for LM Studio."""

        return ChatOpenAI(
            base_url=self.base_url,
            api_key="lm-studio",  # Dummy key
            model=model_name,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", None),
        )

    # ----------------------------------------------------------------

##################################################################
# Test Main
##################################################################
def main():
    """Test the LMStudioProvider class."""
    print("=" * 60)
    print("Testing LM Studio Provider")
    print("=" * 60)

    # Test with default URL
    provider = LMStudioProvider()
    print(f"\nProvider: {provider.provider}")
    print(f"Base URL: {provider.base_url}")

    # Test availability
    print("\n" + "-" * 60)
    print("Checking availability...")
    is_available, message = provider.test_connection()
    print(f"LM Studio available: {is_available}")
    if message:
        print(f"Connection message: {message}")

    if not is_available:
        print("\n⚠️  LM Studio is not running on the provided address!")
        print("Please start LM Studio and enable the local server:")
        print("  1. Open LM Studio")
        print("  2. Go to 'Developer' tab")
        print("  3. Click 'Start Server'")
        print("  4. Ensure server is running on port 1234")
        return

    # Test listing models
    print("\n" + "-" * 60)
    print("Fetching models...")
    models = provider.list_llm_models()

    if models:
        print(f"\nFound {len(models)} model(s):")
        for i, model in enumerate(models, 1):
            print(f"\n  {i}. {model.name}")
            print(f"     ID: {model.id}")
            print(f"     Provider: {model.provider}")
            print(f"     Context Window: {model.context_window}")
    else:
        print("\n⚠️  No models found!")
        print("Please load a model in LM Studio:")
        print("  1. Go to 'Local Server' tab in LM Studio")
        print("  2. Select and load a model")


    # Test actual model inference
    print("\n" + "="*60)
    print("Testing Model Inference")
    print("="*60)

    # Use a simple, reliable model
    test_model = "google/gemma-3-12b"  # Fast and cheap for testing

    print(f"\nTesting model: {test_model}")
    print("Sending test query: 'What is 2+2? Answer with just the number.'")

    try:
        # Create client
        client = provider.create_llm_client(
            model_name=test_model,
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

# python -m services.model_providers.lmstudio_provider
