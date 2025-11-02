"""
config.py
=========

Module-level configuration helpers and constants used by the
PublicOpinionAnalyzer application.

This module provides:
- application constants (`APP_NAME`, `API_PROVIDERS`, `LOCAL_PROVIDERS`)
- a small `Config` helper class that encapsulates common lookup
    logic for API keys (keyring -> environment -> .env -> placeholder)
    and local provider URLs (environment -> .env -> default).

The `Config` class methods are synchronous and may read/write the
local `.env` file or the system keyring. Callers should be prepared to
handle placeholder values (the literal string "API_KEY") when secrets
are not configured.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv
import keyring

APP_NAME = "PublicOpinionAnalyzerAI"

# API providers (secrets)
API_PROVIDERS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

# Local providers (configuration, not secrets)
LOCAL_PROVIDERS = {
    "lmstudio": {
        "default_base_url": "http://localhost:1234/v1",
        "env_var": "LMSTUDIO_BASE_URL",
    },
    "ollama": {
        "default_base_url": "http://localhost:11434",
        "env_var": "OLLAMA_BASE_URL",
    },
}


class Config:
    """
    Configuration helper for the application.

    Responsibilities
    - Manage API keys (secrets) for external API providers using a
        layered lookup order: system keyring -> environment variable ->
        .env file -> default placeholder.
    - Manage local provider base URLs (non-secret configuration) using
        environment variables, .env fallbacks, and a per-provider default
        defined in `LOCAL_PROVIDERS`.

    Key behaviors and methods
    - get_api_key(provider_name: str) -> str
        Returns the API key for `provider_name`. Lookup order:
            1. keyring under key "{APP_NAME}:{provider_name}_api_key"
            2. OS environment variable named by `API_PROVIDERS[provider_name]`
            3. Values from a .env file (loaded via python-dotenv)
            4. Fallback string literal "API_KEY"
        If the provider is unknown (not present in `API_PROVIDERS`),
        the method returns "API_KEY".

    - set_api_key(provider_name: str, api_key: str) -> bool
        Stores the API key in the system keyring. Returns True on
        success, False on failure. Exceptions are caught and printed.

    - get_all_api_keys() -> Dict[str, str]
        Returns a dict mapping provider name -> resolved API key using
        `get_api_key` for each provider defined in `API_PROVIDERS`.

    - is_key_configured(provider_name: str) -> bool
        Returns True when the configured key is not the placeholder
        "API_KEY" and not empty.

    - get_local_provider_url(provider_name: str) -> Optional[str]
        Returns the base URL for a local provider. Lookup order:
            1. Environment variable specified by `LOCAL_PROVIDERS[provider_name]["env_var"]`
            2. .env file (via python-dotenv)
            3. The `default_base_url` value from `LOCAL_PROVIDERS`
        Returns None if the provider is unknown.

    - set_local_provider_url(provider_name: str, base_url: str) -> bool
        Persists the given base URL into the project's `.env` file by
        updating or appending the provider's environment variable.
        This is intended for non-secret configuration and does not use
        the keyring.

    Notes
    - This class does not perform network calls; it only reads and
        writes configuration and secret stores. Calling `load_dotenv()`
        may overlay environment variables for the running process.
    - Caller code should treat values returned from this class as
        authoritative for configuration, but be prepared to handle the
        fallback placeholder when keys are not actually configured.
    """

    # ================================================================
    # API KEY MANAGEMENT (Secrets)
    # ================================================================

    # ----------------------------------------------------------------
    @staticmethod
    def get_api_key(provider_name: str) -> str:
        """
        Get API key for a provider from:
        1. System keyring
        2. Environment variable
        3. .env file
        4. Default placeholder "API_KEY"
        """
        env_var_name = API_PROVIDERS.get(provider_name)
        if not env_var_name:
            return "API_KEY"

        # 1. Try keyring first
        keyring_key = f"{provider_name}_api_key"
        api_key = keyring.get_password(APP_NAME, keyring_key)
        if api_key:
            return api_key

        # 2. Try environment variable
        api_key = os.getenv(env_var_name)
        if api_key:
            return api_key

        # 3. Try .env file
        load_dotenv()
        api_key = os.getenv(env_var_name)
        if api_key:
            return api_key

        return "API_KEY"

    # ----------------------------------------------------------------
    @staticmethod
    def set_api_key(provider_name: str, api_key: str) -> bool:
        """Store API key in system keyring."""
        try:
            keyring_key = f"{provider_name}_api_key"
            keyring.set_password(APP_NAME, keyring_key, api_key)
            return True
        except Exception as e:
            print(f"Error storing key: {e}")
            return False

    # ----------------------------------------------------------------
    @staticmethod
    def get_all_api_keys() -> Dict[str, str]:
        """Get all provider API keys."""
        return {
            provider: Config.get_api_key(provider) for provider in API_PROVIDERS.keys()
        }

    # ----------------------------------------------------------------
    @staticmethod
    def is_key_configured(provider_name: str) -> bool:
        """Check if a provider's API key is actually configured."""
        key = Config.get_api_key(provider_name)
        return key != "API_KEY" and key != ""

    # ================================================================
    # LOCAL PROVIDER CONFIGURATION (Not secrets)
    # ================================================================

    # ----------------------------------------------------------------
    @staticmethod
    def get_local_provider_url(provider_name: str) -> Optional[str]:
        """
        Get base URL for local provider from:
        1. Environment variable
        2. .env file
        3. Default value
        """
        provider_config = LOCAL_PROVIDERS.get(provider_name)
        if not provider_config:
            return None

        # Try environment variable
        env_var = provider_config["env_var"]
        url = os.getenv(env_var)
        if url:
            return url

        # Try .env file
        load_dotenv()
        url = os.getenv(env_var)
        if url:
            return url

        # Return default
        return provider_config["default_base_url"]

    # ----------------------------------------------------------------
    @staticmethod
    def set_local_provider_url(provider_name: str, base_url: str) -> bool:
        """
        Save local provider URL to .env file (not keyring - it's not a secret).
        """
        provider_config = LOCAL_PROVIDERS.get(provider_name)
        if not provider_config:
            return False

        env_var = provider_config["env_var"]

        # Read existing .env
        env_path = ".env"
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_lines = f.readlines()

        # Update or add the variable
        found = False
        for i, line in enumerate(env_lines):
            if line.startswith(f"{env_var}="):
                env_lines[i] = f"{env_var}={base_url}\n"
                found = True
                break

        if not found:
            env_lines.append(f"{env_var}={base_url}\n")

        # Write back
        with open(env_path, "w") as f:
            f.writelines(env_lines)

        return True

    # ----------------------------------------------------------------
