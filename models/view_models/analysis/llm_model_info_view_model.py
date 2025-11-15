"""
llm_model_info_view_model.py
============================

ViewModel projection of LLMModelInfo for the UI layer.

This strips backend-only fields and exposes UI-friendly fields:
- label: what the dropdown shows the user
- value: what the dropdown returns (string, stable identifier)
- provider, model_name: used by the controller to look up the domain model
"""

from dataclasses import dataclass
from enums.provider_enum import ProviderEnum


@dataclass
class LLMModelInfoViewModel:
    """
    UI-friendly representation of an LLM model for dropdown selection.

    Attributes:
        provider:       ProviderEnum (OpenAI, Gemini, DeepSeek,...)
        model_name:     Actual internal name (e.g. "gpt-4o-mini")
        label:          Readable label shown in the dropdown
        is_favorite:    Can be used to prioritize the model in the dropdown
        is_local:       Helps the UI indicate local vs API-based models
    """

    provider: ProviderEnum
    model_name: str
    label: str      # user-facing label in dropdown (e.g. "OpenAI — GPT-4o-mini")
    is_favorite: bool = False
    is_local: bool = False
