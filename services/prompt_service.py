# services/prompt_service.py
"""
prompt_service.py
=================

Service for managing prompts stored in the file system.
Handles CRUD operations for prompt files.
"""

from typing import List, Optional, Tuple
from models.prompt_model import Prompt, PromptGroup
from repositories.prompt_repository import PromptRepository


##################################################################
class PromptService:
    """Handles business logic for prompt management."""
    
    # ----------------------------------------------------------------
    def __init__(self):
        """Initialize the prompt service."""
        self.repository = PromptRepository()
    
    # ----------------------------------------------------------------
    def load_all_groups(self) -> List[PromptGroup]:
        """Load all prompt groups from the repository."""
        return self.repository.load_all_prompt_groups()
    
    # ----------------------------------------------------------------
    def save_group(self, group: PromptGroup) -> None:
        """Save a prompt group."""
        self.repository.save_prompt_group(group)
        
    # ----------------------------------------------------------------
    def delete_group(self, group_name: str) -> None:
        """Delete a prompt group."""
        self.repository.delete_prompt_group(group_name)

    # ----------------------------------------------------------------
    def get_all_prompts(self) -> List[Prompt]:
        """
        Get all available prompts from all groups.
        
        Returns:
            List of all Prompt objects across all groups
        """
        all_prompts = []
        groups = self.repository.load_all_prompt_groups()
        for group in groups:
            all_prompts.extend(group.prompts)
        return all_prompts
    
    # ----------------------------------------------------------------
    def get_prompt_names(self) -> List[str]:
        """
        Get list of all prompt names for dropdown/selection.
        
        Returns:
            List of prompt names
        """
        prompts = self.get_all_prompts()
        return [prompt.name for prompt in prompts]
    
    # ----------------------------------------------------------------
    def get_prompt_content(self, name: str) -> Optional[str]:
        """
        Get prompt content by name.
        
        Args:
            name: Prompt name to search for
            
        Returns:
            Prompt content string, or None if not found
        """
        prompts = self.get_all_prompts()
        for prompt in prompts:
            if prompt.name == name:
                return prompt.content
        return None
    
    # ----------------------------------------------------------------
    def save_prompt(self, name: str, content: str, group_name: str = "SystemPrompts") -> Tuple[bool, str]:
        """
        Create or update a prompt.
        
        Args:
            name: Prompt name (without .json extension)
            content: Prompt content
            group_name: Name of the group to save to (defaults to "SystemPrompts")
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            prompt_obj = Prompt(name=name, content=content)
            self.repository.save_prompt(group_name, prompt_obj)
            return (True, f"成功保存 prompt: {name}")
        except Exception as e:
            return (False, f"保存 prompt 失敗: {str(e)}")
    
    # ----------------------------------------------------------------
    def delete_prompt(self, name: str, group_name: str = "SystemPrompts") -> Tuple[bool, str]:
        """
        Delete a prompt.
        
        Args:
            name: Prompt name (without .json extension)
            group_name: Name of the group containing the prompt (defaults to "SystemPrompts")
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.repository.delete_prompt(group_name, name)
            return (True, f"成功刪除 prompt: {name}")
        except Exception as e:
            return (False, f"刪除 prompt 失敗: {str(e)}")

    # ----------------------------------------------------------------

##################################################################

