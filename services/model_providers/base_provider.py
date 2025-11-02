# services/llm_providers/base_provider.py
"""
base_provider.py
================

Abstract base class for LLM provider integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Any, Optional
from dataclasses import dataclass


##################################################################
@dataclass
class ModelInfo:
    """Information about an available LLM model."""
    id: str
    name: str
    provider: str
    context_window: Optional[int] = None
    supports_function_calling: Optional[bool] = None
    supports_vision: Optional[bool] = None

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
        pass

    # ----------------------------------------------------------------
    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """
        Get list of available models from this provider.
        
        Returns:
            List of ModelInfo objects describing available models.
        """

    # ----------------------------------------------------------------
    @abstractmethod
    def get_model_info(self, model_id: str) -> ModelInfo:
        """
        Get detailed information about a specific model.
        
        Args:
            model_id: The model identifier.
            
        Returns:
            ModelInfo object with model details.
        """

    # ----------------------------------------------------------------
    @abstractmethod
    def create_client(self, model_id: str, **kwargs) -> Any:
        """
        Create an LLM client for the specified model.
        
        Args:
            model_id: The model identifier.
            **kwargs: Additional configuration options.
            
        Returns:
            Configured LLM client ready for use.
        """

    # ----------------------------------------------------------------

##################################################################
