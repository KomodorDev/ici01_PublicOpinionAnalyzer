# services/llm_providers/openai_provider.py
"""
openai_provider.py
==================

OpenAI provider implementation.
"""

from typing import List
from openai import OpenAI
from services.model_providers.base_provider import ModelProvider, ModelInfo


##################################################################
class OpenAIProvider(ModelProvider):
    """Manages OpenAI models and API integration."""

    # ----------------------------------------------------------------
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.provider_name = "openai"

    # ----------------------------------------------------------------
    def list_models(self) -> List[ModelInfo]:
        """
        List all available OpenAI models.
        
        Returns:
            List of ModelInfo objects for available models.
        """
        models = []
        
        # Fetch models from OpenAI API
        response = self.client.models.list()
        
        for model in response.data:
            # Filter to chat/completion models only
            if any(keyword in model.id for keyword in ["gpt-", "o1-", "chatgpt"]):
                model_info = ModelInfo(
                    id=model.id,
                    name=model.id,
                    provider=self.provider_name,
                    context_window=self._get_context_window(model.id),
                    supports_function_calling=self._supports_functions(model.id),
                    supports_vision="vision" in model.id or "4o" in model.id
                )
                models.append(model_info)
        
        return sorted(models, key=lambda x: x.id)

    # ----------------------------------------------------------------
    def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed info about a specific OpenAI model."""
        model = self.client.models.retrieve(model_id)
        
        return ModelInfo(
            id=model.id,
            name=model.id,
            provider=self.provider_name,
            context_window=self._get_context_window(model.id),
            supports_function_calling=self._supports_functions(model.id),
            supports_vision="vision" in model.id or "4o" in model.id
        )

    # ----------------------------------------------------------------
    # SAH: Likely not needed, LangGraph will handle client creation
    def create_client(self, model_id: str, **kwargs):
        """Return configured OpenAI client for LangChain."""
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_id, **kwargs)

    # ----------------------------------------------------------------
    def _get_context_window(self, model_id: str) -> int:
        """Map model IDs to context window sizes."""
        context_windows = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16385,
            "o1": 200000,
            "o1-mini": 128000,
        }
        for key, size in context_windows.items():
            if key in model_id:
                return size
        return 4096  # default

    # ----------------------------------------------------------------
    def _supports_functions(self, model_id: str) -> bool:
        """Check if model supports function calling."""
        return any(x in model_id for x in ["gpt-4", "gpt-3.5-turbo", "gpt-4o"])

    # ----------------------------------------------------------------

##################################################################
