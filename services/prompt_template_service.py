"""
prompt_template_service.py
=================

Service for managing prompt templates stored in the file system.
Handles CRUD operations for prompt template files.
"""

from typing import List

from enums.platform_enum import PlatformEnum
from repositories.prompt_template_repository import PromptTemplateRepository
from models.prompt_template_model import PromptTemplate


##################################################################
class PromptTemplateService:
    """
    Service layer for managing PromptTemplate objects.
    Provides a clean abstraction between controllers and the file-based repository.

    Responsibilities:
    - Delegates CRUD operations to PromptTemplateRepository
    - Optionally performs lightweight business logic or validation (future extension)
    - Remains stateless: platform must be provided explicitly for each call
    """

    # ----------------------------------------------------------------
    def __init__(self):
        """Initialize the service with a reference to the repository."""
        self.prompt_template_repository = PromptTemplateRepository()


    # ================================================================
    # CRUD Operations (Pass-through to Repository)
    # ================================================================

    # ----------------------------------------------------------------
    # LOAD
    def load_prompt_template(self, platform: PlatformEnum, name: str) -> PromptTemplate:
        """
        Load a single prompt template by name for the given platform.

        Args:
            platform: Platform enum (e.g., PlatformEnum.REDDIT)
            name: Template filename (without .json)

        Returns:
            PromptTemplate: Fully parsed dataclass instance.
        """
        return self.prompt_template_repository.load_prompt_template(platform, name)

    # ----------------------------------------------------------------
    # LOAD ALL
    def load_all_prompt_templates(self, platform: PlatformEnum) -> List[PromptTemplate]:
        """
        Load all templates for a given platform.

        Args:
            platform: Platform enum (e.g., PlatformEnum.YOUTUBE)

        Returns:
            List[PromptTemplate]: All templates found for that platform.
        """
        return self.prompt_template_repository.load_all_prompt_templates(platform)

    # ----------------------------------------------------------------
    # SAVE
    def save_prompt_template(
        self,
        platform: PlatformEnum,
        model: PromptTemplate,
        overwrite: bool = False,
    ) -> str:
        """
        Save a prompt template to disk via repository.

        Args:
            platform: Platform enum
            model: PromptTemplate instance to persist
            overwrite: Whether to replace an existing template if one exists

        Returns:
            str: Path to the saved file.
        """
        return self.prompt_template_repository.save_prompt_template(platform, model, overwrite)

    # ----------------------------------------------------------------
    # DELETE
    def delete_prompt_template(self, platform: PlatformEnum, name: str) -> bool:
        """
        Delete a prompt template from disk.

        Args:
            platform: Platform enum
            name: Template filename (without .json)

        Returns:
            bool: True if deleted successfully, False if file not found.
        """
        return self.prompt_template_repository.delete_prompt_template(platform, name)

    # ----------------------------------------------------------------
    # LIST PROMPT TEMPLATE NAMES
    def list_all_prompt_template_names(self, platform: PlatformEnum) -> List[str]:
        """
        List all prompt template filenames (without .json) for a given platform.

        Args:
            platform: Platform enum (e.g., PlatformEnum.YOUTUBE)

        Returns:
            List[str]: All template names under that platform’s directory.
        """
        return self.prompt_template_repository.list_all_prompt_template_names(platform)


    # ----------------------------------------------------------------

##################################################################


# python -m services.prompt_template_service
