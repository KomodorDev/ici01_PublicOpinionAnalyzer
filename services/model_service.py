# services/model_service.py
"""
model_service.py
================

Central service for managing LLM models across providers.
"""

from typing import List, Dict
from services.model_providers.base_provider import ModelProvider, ModelInfo
from services.model_providers.lmstudio_provider import LMStudioProvider
from services.model_providers.openai_provider import OpenAIProvider
# from services.model_providers.google_provider import GoogleAIProvider


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
            # "google": GoogleAIProvider(),
            "lmstudio": LMStudioProvider(),
            # Add more providers here as you implement them
            # "anthropic": AnthropicProvider(),
            # "deepseek": DeepSeekProvider(),
        }
    # ----------------------------------------------------------------
    def list_all_models(self) -> List[ModelInfo]:
        """
        Get list of all available models from all providers.
        
        Returns:
            Combined list of ModelInfo objects from all providers.
        """
        all_models = []
        for provider in self.providers.values():
            try:
                models = provider.list_models()
                all_models.extend(models)
            except Exception as e:
                print(f"Error fetching models from {provider}: {e}")
        return all_models

    # ----------------------------------------------------------------
    def list_models_by_provider(self, provider_name: str) -> List[ModelInfo]:
        """Get models from a specific provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not configured")
        return self.providers[provider_name].list_models()

    # ----------------------------------------------------------------
    def get_model_client(self, provider_name: str, model_id: str, **kwargs):
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
        return self.providers[provider_name].create_client(model_id, **kwargs)

    # ----------------------------------------------------------------
    def get_providers(self) -> List[str]:
        """Get list of configured provider names."""
        return list(self.providers.keys())

    # ----------------------------------------------------------------
    def is_lmstudio_connected(self) -> bool:
        """Check if LM Studio is running and responding."""
        provider = self.providers.get("lmstudio")
        if not provider:
            return False

        # We call on LM_Studio provider to check availability
        return provider.is_available()

    # ----------------------------------------------------------------

##################################################################
