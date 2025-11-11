# llm_model_info_model.py

"""
llm_model_info_model.py
=======================

Data structure for representing metadata about available Large Language Models (LLMs).

See docstring within LLMModelInfo for full details and usage.
"""

from dataclasses import dataclass
from typing import Optional
from enums.provider_enum import ProviderEnum

@dataclass
class LLMModelInfo:
    """
    Metadata/configuration descriptor for a Large Language Model (LLM).

    Attributes:
        name:                        Unique identifier for the model (e.g., "gpt-4", "mixtral").
        provider:                    ProviderEnum specifying hosting/provider platform.
        display_name:                Optional user-friendly name for UI.
        description:                 Optional longer description of model.
        context_window:              Optional max token context window (for model limits).
        supports_function_calling:   Optional bool—whether model supports calling tools/functions.
        supports_vision:             Optional bool—whether model supports vision (image input).
        favorite:                    Boolean flag for preferred/default models.
        is_local:                    Boolean—True for local-hosted, False for API-based models.

    """
    name: str
    provider: ProviderEnum
    display_name: str = ""
    description: str = ""
    context_window: Optional[int] = None
    supports_function_calling: Optional[bool] = None
    supports_vision: Optional[bool] = None
    favorite: bool = False
    is_local: bool = False
