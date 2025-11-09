# controllers/prompt_controller.py
"""
prompt_controller.py
====================

Controller for managing prompts.

Provides interface for:
- Getting list of available prompts (for frontend selection)
- Getting prompt content (for other functions to use)
- Creating/updating prompts
- Deleting prompts
"""

from typing import List, Optional, Tuple
from services.prompt_service import PromptService
from models.prompt_template_model import PromptTemplate


##################################################################
class PromptController:
    """Handles prompt management operations."""
    
    # ----------------------------------------------------------------
    def __init__(self):
        """Initialize the prompt controller with service."""
        self.prompt_service = PromptService()
    
    # ----------------------------------------------------------------
    def get_all_prompts(self) -> List[PromptTemplate]:
        """
        Get all available prompts.
        
        Returns:
            List of Prompt objects
        """

    
    # ----------------------------------------------------------------
    def get_prompt_names(self) -> List[str]:
        """
        Get list of prompt names for dropdown/selection.
        
        Returns:
            List of prompt names
        """

    
    # ----------------------------------------------------------------
    def get_prompt_content(self, name: str) -> Optional[str]:
        """
        Get prompt content string (for use by other functions).
        
        Args:
            name: Prompt name
            
        Returns:
            Prompt content string, or None if not found
        """
    
    # ----------------------------------------------------------------
    def create_or_update_prompt(self, name: str, content: str) -> Tuple[bool, str]:
        """
        Create or update a prompt.
        
        Args:
            name: Prompt name (without .json extension)
            content: Prompt content
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        return self.prompt_service.save_prompt_template(name, content)
    
    # ----------------------------------------------------------------
    def delete_prompt(self, name: str) -> Tuple[bool, str]:
        """
        Delete a prompt.
        
        Args:
            name: Prompt name (without .json extension)
            
        Returns:
            Tuple of (success: bool, message: str)
        """


##################################################################
