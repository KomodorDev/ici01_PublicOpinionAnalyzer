# services/model_providers/lmstudio_provider.py
"""
lmstudio_provider.py
====================

Local LM Studio provider — OpenAI-compatible API running on localhost.
"""
import requests

from services.model_providers.base_provider import ModelProvider, ModelInfo


##################################################################
class LMStudioProvider(ModelProvider):
    """Lists locally served LM Studio models."""

    # ----------------------------------------------------------------
    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        self.provider = "lmstudio"
        self.base_url = base_url

    # ----------------------------------------------------------------
    def is_available(self) -> bool:
        """Check if LM Studio is running locally."""
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=2)
            return resp.status_code == 200
        except requests.RequestException:
            return False
        
    # ----------------------------------------------------------------
    def list_models(self):
        """
        Since LM Studio doesn’t expose `/models`, 
        return a minimal example list of known models.
        Replace or load dynamically if needed.
        """
        return [
            ModelInfo(
                id="mistral-7b-instruct",
                name="Mistral 7B Instruct (local)",
                provider=self.provider,
                context_window=8192,
            ),
            ModelInfo(
                id="llama-3.2-1b",
                name="LLaMA 3.2 1B (local)",
                provider=self.provider,
                context_window=8192,
            )
        ]

    # ----------------------------------------------------------------
    def create_client(self, model_id: str, **kwargs):
        """
        No-op: LangGraph will manage LLM initialization.
        LM Studio is OpenAI-compatible, so this provider only 
        declares availability and metadata.
        """
        return None

    # ----------------------------------------------------------------

##################################################################
