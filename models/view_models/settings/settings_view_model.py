# models/view_models/settings/settings_view_model.py

from dataclasses import dataclass
from typing import Dict, Optional, Any


@dataclass
class SettingsViewModel:
    """
    Full state for the Settings view.
    Contains all API keys (masked), provider URLs, and provider statuses.
    """

    # Masked API keys for display (provider_name -> masked_key)
    masked_api_keys: Dict[str, str]

    # Local provider URLs
    lmstudio_url: Optional[str]
    ollama_url: Optional[str]

    # Provider statuses (provider_name -> status dict)
    provider_statuses: Dict[str, Dict[str, Any]]

    # Page-level messages
    info_message: Optional[str] = None
    error_message: Optional[str] = None

