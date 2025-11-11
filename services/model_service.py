# services/model_service.py
"""
model_service.py
================

Central service for managing LLM models across providers.
"""

from typing import List, Dict
from models.llm_model_info_model import LLMModelInfo
from services.model_providers.base_provider import ModelProvider
from services.model_providers.lmstudio_provider import LMStudioProvider
from services.model_providers.openai_provider import OpenAIProvider
from services.model_providers.google_provider import GoogleProvider


##################################################################
class ModelService:
    """
    Manages LLM models across multiple providers.
    
    Provides unified interface for listing and accessing models.
    """

    # ----------------------------------------------------------------
    def __init__(self):
        """Initialize ModelService with all available providers."""
        # Register all providers - they handle their own configuration
        self.providers: Dict[str, ModelProvider] = {
            "openai": OpenAIProvider(),
            "google": GoogleProvider(),
            "lmstudio": LMStudioProvider(),
            # Add more providers here as you implement them
            # "anthropic": AnthropicProvider(),
            # "deepseek": DeepSeekProvider(),
        }
    # ----------------------------------------------------------------
    def list_all_llm_models(self) -> List[LLMModelInfo]:
        """
        Get list of all available models from all providers.
        
        Returns:
            Combined list of ModelInfo objects from all providers.
        """
        all_models = []
        for provider in self.providers.values():
            try:
                models = provider.list_llm_models()
                all_models.extend(models)
            except Exception as e:
                print(f"Error fetching models from {provider}: {e}")
        return all_models

    # ----------------------------------------------------------------
    def list_llm_models_by_provider(self, provider_name: str) -> List[LLMModelInfo]:
        """Get models from a specific provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not configured")
        return self.providers[provider_name].list_llm_models()

    # ----------------------------------------------------------------
    def get_llm_model_client(self, provider_name: str, model_name: str, **kwargs):
        """
        Create LLM client for specific model.
        
        Args:
            provider_name: Provider name ("openai", "google", etc.)
            model_id: Model identifier
            **kwargs: Additional configuration for the client
            
        Returns:
            Configured LLM client ready for use.
        """
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not configured")
        return self.providers[provider_name].create_llm_client(model_name, **kwargs)

    # ----------------------------------------------------------------
    def get_providers(self) -> List[str]:
        """Get list of configured provider names."""
        return list(self.providers.keys())

    # ----------------------------------------------------------------

##################################################################

def main():
    """List all available LLM models across providers."""
    service = ModelService()
    models = service.list_all_llm_models()

    print("\n=== Available LLM Models ===")
    if not models:
        print("No models found.")
        return

    for m in models:
        # Assuming LLMModelInfo has attributes like: name, provider, and description
        # (adjust field names if they differ)
        provider = getattr(m, "provider", "unknown")
        name = getattr(m, "name", "unnamed")
        desc = getattr(m, "description", "")
        print(f"- Provider: {provider:10s} | Model: {name:25s} | {desc}")

if __name__ == "__main__":
    main()
