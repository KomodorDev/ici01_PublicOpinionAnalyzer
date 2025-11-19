"""
video_model_info_view_model.py
==============================

ViewModel projection of VideoModelInfo for the UI layer.

This strips backend-only fields and exposes UI-friendly fields:
- label: what the dropdown shows the user
- value: stable identifier (model name)
- provider: used by the controller to resolve the underlying domain model
"""

from dataclasses import dataclass
from enums.provider_enum import ProviderEnum


@dataclass
class VideoModelInfoViewModel:
    """
    UI-friendly representation of a video-capable model for dropdown selection.

    Attributes:
        provider:       ProviderEnum (OpenAI, Google, etc.)
        model_name:     Internal model identifier (e.g. "gemini-1.5-flash")
        label:          User-facing name for dropdowns
        is_favorite:    Indicate preferred models (optional sorting)
        is_local:       Show whether model is locally hosted
    """

    provider: ProviderEnum
    model_name: str
    label: str
    is_favorite: bool = False
    is_local: bool = False
