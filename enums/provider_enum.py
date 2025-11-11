"""
provider_enum.py
================

Defines the enumeration for supported model/service providers in the application.

Usage example:
    from enums.provider_enum import ProviderEnum

    if client.provider == ProviderEnum.OPENAI:
        # Handle OpenAI-specific logic
"""

from enum import Enum

class ProviderEnum(Enum):
    """
    Enumeration of supported LLM/model service providers.

    Members:
        OPENAI:      Represents OpenAI models and APIs (e.g., GPT-4, GPT-3.5).
        ANTHROPIC:   Represents Anthropic models and APIs (e.g., Claude).
        GOOGLE:      Represents Google models and APIs (e.g., Gemini, PaLM).
        LMSTUDIO:    Represents LM Studio, a local model serving platform.
        OLLAMA:      Represents Ollama, a local model serving platform.
        # Extend this enum as you support additional providers.

    Example:
        >>> ProviderEnum.OPENAI
        <ProviderEnum.OPENAI: 'openai'>
        >>> str(ProviderEnum.GOOGLE)
        'google'
    """
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LMSTUDIO = "lmstudio"
    OLLAMA = "ollama"

    def __str__(self):
        """
        Returns the string value of the provider for serialization or display.

        Returns:
            str: The provider identifier (e.g., 'openai', 'anthropic').
        """
        return self.value
