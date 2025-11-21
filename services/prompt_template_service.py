"""
prompt_template_service.py
==========================

Service layer responsible for managing **PromptTemplate** objects and applying
lightweight validation and business rules before delegating file operations to
the repository layer (`PromptTemplateRepository`).

This module forms the middle tier between:
- The **controller layer**, which handles user interactions and UI callbacks.
- The **repository layer**, which performs low-level file I/O and JSON parsing.

Core responsibilities:
----------------------
1. **CRUD orchestration**
   - Loads, saves, lists, and deletes prompt templates via the repository.
   - Enforces overwrite semantics and structured error handling.

2. **Validation**
   - Checks for required and optional placeholders depending on the platform.
   - Ensures mandatory fields (name, system_prompt, user_prompt) are present.
   - Optionally flags unknown placeholders when `strict_unknown=True`.

3. **Placeholder extraction**
   - Uses a simple regex (`[PLACEHOLDER]`) to identify all variable tokens used
     inside the template text.

Design philosophy:
------------------
- Stateless: every operation requires an explicit `PlatformEnum` argument.
- Clean separation of concerns: no UI or I/O logic.
- Extendable: future versions can incorporate richer validation or dynamic
  placeholder schemas loaded from configuration or metadata files.

Typical flow:
-------------
Controller → Service → Repository → File System
"""

import re
from typing import Dict, List, Set

from enums.platform_enum import PlatformEnum
from enums.placeholder_enum import PlaceholderEnum
from repositories.prompt_template_repository import PromptTemplateRepository
from models.domain import PromptTemplate


##################################################################
class PromptTemplateService:
    """
    Service layer encapsulating prompt template management and validation logic.

    This class provides a high-level API for working with `PromptTemplate` objects:
    controllers call into it to perform create, read, update, and delete operations
    without dealing with low-level file handling.

    Responsibilities:
    -----------------
    - **Delegation:** Routes CRUD operations to `PromptTemplateRepository`.
    - **Validation:** Ensures templates contain all required placeholders for their platform.
    - **Extraction:** Finds all placeholders in system/user prompts using a regex.
    - **Abstraction:** Shields controllers from filesystem concerns and error handling.

    Attributes:
    -----------
    prompt_template_repository : PromptTemplateRepository
        Underlying repository that performs JSON file operations.

    _rx : re.Pattern
        Compiled regex used to extract placeholders of the form `[PLACEHOLDER]`.

    _required_placeholders : Dict[PlatformEnum, List[str]]
        Mapping of each platform to its required placeholders.

    _optional_placeholders : Dict[PlatformEnum, List[str]]
        Mapping of each platform to its optional placeholders.

    Notes:
    ------
    - The service is **stateless**: it never caches or stores templates internally.
    - Placeholder validation can be extended to load rules dynamically in the future.
    - Designed for safe composition with higher-level controllers and unit tests.
    """

    # ----------------------------------------------------------------
    def __init__(self):
        """Initialize the service with a reference to the repository."""
        self.prompt_template_repository = PromptTemplateRepository()

        # Platform rules (inline for now)
        self._rx = re.compile(
            r"\[([A-Za-z_][A-Za-z0-9_]*)\]"
        )  # Matches placeholders like [PLACEHOLDER], [SOME_VAR], etc.

        self._required_placeholders: Dict[PlatformEnum, List[PlaceholderEnum]] = {
            PlatformEnum.YOUTUBE: [
                PlaceholderEnum.CLASSIFICATIONS,
                PlaceholderEnum.OUTPUTFORMAT,
                PlaceholderEnum.VIDEOTITLE,
                PlaceholderEnum.VIDEOCONTEXT,
                PlaceholderEnum.TARGETCOMMENT,
            ],
            PlatformEnum.REDDIT: [PlaceholderEnum.OUTPUTFORMAT],
        }

        self._optional_placeholders: Dict[PlatformEnum, List[PlaceholderEnum]] = {
            PlatformEnum.YOUTUBE: [
                PlaceholderEnum.THREADCOMMENTS,
                PlaceholderEnum.TAGGEDCOMMENTS,
            ],
            PlatformEnum.REDDIT: [],
        }

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
        model: PromptTemplate,
        overwrite: bool = False,
    ) -> str:
        """
        Validate and persist a prompt template to disk via the repository.

        Performs a full structural and placeholder validation before delegating
        the actual save operation to the repository layer.

        Args:
            model (PromptTemplate):
                The prompt template instance to persist.
            overwrite (bool, optional):
                Whether to replace an existing file if one already exists.
                Defaults to False.

        Returns:
            str:
                The full path of the saved JSON file.

        Raises:
            ValueError:
                If the template is invalid (e.g., missing required fields or placeholders).
            FileExistsError:
                If a file already exists and `overwrite` is False.
            Exception:
                For unexpected repository-level errors (e.g., I/O issues).
        """
        self.validate_prompt_template(model, strict_unknown=False)
        return self.prompt_template_repository.save_prompt_template(model, overwrite)

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

    # ================================================================
    # Prompt Template Validation (Business Logic)
    # ================================================================
    # ----------------------------------------------------------------
    def get_required_placeholders(self, platform: PlatformEnum) -> List[str]:
        """Return a copy of the platform's required placeholders."""
        return [p.value for p in self._required_placeholders.get(platform, [])]

    # ----------------------------------------------------------------
    def get_optional_placeholders(self, platform: PlatformEnum) -> List[str]:
        """Return a copy of the platform's optional placeholders."""
        return [p.value for p in self._optional_placeholders.get(platform, [])]

    # ----------------------------------------------------------------
    def extract_placeholders(self, tpl: PromptTemplate) -> List[str]:
        """Return sorted unique placeholders found across system/user prompts."""

        # Empty set that only stores strings
        found: Set[str] = set()

        # If system prompts exist, extract placeholders
        if tpl.system_prompt:
            found |= set(self._rx.findall(tpl.system_prompt))

        # If user prompts exist, extract placeholders
        if tpl.user_prompt:
            found |= set(self._rx.findall(tpl.user_prompt))

        # Return sorted list of found placeholders
        return sorted(found)

    # ----------------------------------------------------------------
    def validate_prompt_template(
        self, tpl: PromptTemplate, *, strict_unknown=False
    ) -> None:
        """Validate the prompt template against its platform's requirements."""

        # If mandatory fields are missing, raise error
        if not tpl.name or not tpl.name.strip():
            raise ValueError("Name is required.")
        if not tpl.system_prompt or not tpl.system_prompt.strip():
            raise ValueError("System prompt is required.")
        if not tpl.user_prompt or not tpl.user_prompt.strip():
            raise ValueError("User prompt is required.")

        # Extract placeholders using the helper
        found = set(self.extract_placeholders(tpl))
        req = set(self.get_required_placeholders(tpl.platform))

        # Check for missing placeholders
        missing = [p for p in req if p not in found]
        if missing:
            raise ValueError(
                f"Missing required placeholders for {tpl.platform.value}: {', '.join(missing)}"
            )

        # Optionally disallow unknown placeholders
        if strict_unknown:
            allowed = req | set(self.get_optional_placeholders(tpl.platform))
            unknown = [p for p in sorted(found) if p not in allowed]
            if unknown:
                raise ValueError(
                    f"Unknown placeholders not allowed: {', '.join(unknown)}"
                )

    # ----------------------------------------------------------------


##################################################################

# python -m services.prompt_template_service
