# services/llm_providers/base_provider.py
"""
base_provider.py
================

Abstract base class for LLM provider integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass


##################################################################
@dataclass
class ModelInfo:
    """Information about an available LLM model."""
    id: str
    name: str
    provider: str
    context_window: int
    supports_function_calling: bool = False
    supports_vision: bool = False

##################################################################
class ModelProvider(ABC):
    """
    Abstract base class for model provider integrations.

    All provider-specific implementations must implement these methods.
    """

    # ----------------------------------------------------------------
    def is_available(self) -> bool:
        """Return whether the provider service is available.
        Default: returns True (for API-managed models).
        """
        return True

    # ----------------------------------------------------------------
    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """
        Get list of available models from this provider.
        
        Returns:
            List of ModelInfo objects describing available models.
        """
        pass

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
        pass

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
        pass

    # ----------------------------------------------------------------

##################################################################
