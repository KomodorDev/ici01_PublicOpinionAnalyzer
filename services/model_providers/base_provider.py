"""
base_provider.py
================

Abstract base class for LLM provider integrations.

Defines the contract for provider implementations, requiring model listing,
metadata, client creation, and connection testing.

All model info uses the LLMModelInfo structure from your shared models.
"""

from abc import ABC, abstractmethod
from typing import List, Any
from models.llm_model_info_model import LLMModelInfo



##################################################################
class ModelProvider(ABC):
    """
    Abstract base class for model provider integrations.

    All provider-specific implementations must implement these methods.
    """

    # ----------------------------------------------------------------
    @abstractmethod
    def test_connection(self, api_key: str = None) -> tuple[bool, str]:
        """
        Test if provider connection works (makes real API call).
        
        Args:
            api_key: Optional API key to test. If None, uses stored configuration.
        
        Returns:
            Tuple of (success: bool, message: str)
        """

    # ----------------------------------------------------------------
    @abstractmethod
    def list_llm_models(self) -> List[LLMModelInfo]:
        """
        Get list of available LLM (chat/completion-capable) models from this provider.

        Returns:
            List of LLMModelInfo objects describing available LLM models.
        """
        pass

    # ----------------------------------------------------------------
    @abstractmethod
    def get_llm_model_info(self, model_name: str) -> LLMModelInfo:
        """
        Get detailed information about a specific model.

        Args:
            model_name: The model name (as in LLMModelInfo.name).

        Returns:
            LLMModelInfo object with model details.
        """

    # ----------------------------------------------------------------
    @abstractmethod
    def create_llm_client(self, model_name: str, **kwargs) -> Any:
        """
        Create an LLM client for the specified model.

        Args:
            model_name: The model name (as in LLMModelInfo.name).
            **kwargs: Additional configuration options.

        Returns:
            Configured LLM client, ready for use.
        """

    # ----------------------------------------------------------------

##################################################################
