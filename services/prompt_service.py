# services/prompt_service.py
"""
prompt_service.py
=================

Service for managing prompts stored in the file system.
Handles CRUD operations for prompt files.
"""

from typing import List
from models.prompt_model import PromptGroup
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

##################################################################

