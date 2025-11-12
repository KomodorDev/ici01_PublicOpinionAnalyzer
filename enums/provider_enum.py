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
from typing import List

class ProviderEnum(str,Enum):
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
    
    @classmethod
    def from_str(cls, value: str) -> "ProviderEnum":
        """Convert a string to a ProviderEnum (case-insensitive)."""
        if not value:
            raise ValueError("Provider cannot be empty")
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f"Unknown provider: {value}")

    @classmethod
    def to_list(cls) -> List[str]:
        """Return all provider string values (for UI dropdowns, etc.)."""
        return [p.value for p in cls]

    def __str__(self) -> str:
        return self.value
