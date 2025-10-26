# services/llm_providers/google_provider.py
"""
google_provider.py
==================

Google AI (Gemini) provider implementation.
"""

from typing import List
from google import genai
from services.model_providers.base_provider import LLMProvider, ModelInfo


##################################################################
class GoogleAIProvider(LLMProvider):
    """Manages Google AI (Gemini) models."""

    # ----------------------------------------------------------------
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.provider_name = "google"

    # ----------------------------------------------------------------
    def list_models(self) -> List[ModelInfo]:
        """
        List all available Gemini models.
        
        Returns:
            List of ModelInfo objects for available models.
        """
        models = []
        
        # Fetch models from Google AI API
        for model in genai.list_models():
            # Filter to generative models only
            if "generateContent" in model.supported_generation_methods:
                model_info = ModelInfo(
                    id=model.name.split("/")[-1],  # Extract model ID
                    name=model.display_name or model.name,
                    provider=self.provider_name,
                    context_window=getattr(model, "input_token_limit", 32000),
                    supports_function_calling=True,
                    supports_vision="vision" in model.name.lower()
                )
                models.append(model_info)
        
        return sorted(models, key=lambda x: x.id)

    # ----------------------------------------------------------------
    def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed info about a specific Gemini model."""
        model = genai.get_model(f"models/{model_id}")
        
        return ModelInfo(
            id=model_id,
            name=model.display_name or model_id,
            provider=self.provider_name,
            context_window=getattr(model, "input_token_limit", 32000),
            supports_function_calling=True,
            supports_vision="vision" in model.name.lower()
        )
    
    # ----------------------------------------------------------------
    # SAH: Likely not needed, LangGraph will handle client creation
    def create_client(self, model_id: str, **kwargs):
        """Return configured Google AI client for LangChain."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model_id, **kwargs)

    # ----------------------------------------------------------------

##################################################################
