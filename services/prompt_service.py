# services/prompt_service.py
"""
prompt_service.py
=================

Service for managing prompts stored in the file system.
Handles CRUD operations for prompt files.
"""

from typing import List, Optional
import re

from repositories.prompt_template_repository import PromptTemplateRepository
from services.classification_service import ClassificationService
from services.output_format_service import OutputFormatService


##################################################################
class PromptService:
    """
    Service for managing and rendering prompt templates.

    Features:
    - CRUD operations (delegates to repository)
    - Template caching for performance
    - Persistent platform and classification configuration
    - Variable substitution and rendering
    """

    # ----------------------------------------------------------------
    def __init__(
        self,
        prompt_template_repository: PromptTemplateRepository,
        classification_service: ClassificationService,
        output_format_service: OutputFormatService,
        platform: Optional[str] = None,
        classification_group_name: Optional[str] = None,
    ):
        """
        Initialize PromptService.

        Args:
            prompt_template_repository: Repository for template storage
            classification_service: Service for classification operations
            output_format_service: Service for output format generation
            platform: Default platform (e.g., 'youtube')
            classification_group_name: Default classification group folder name
        """
        self.prompt_template_repo = prompt_template_repository
        self.classification_service = classification_service
        self.output_format_service = output_format_service

        # Persistent configuration
        self.platform = platform
        self.classification_group_name = classification_group_name

        # Caching
        self._template_cache = {}
        self._classification_cache = {}

        # Regex pattern for placeholder detection
        self.placeholder_pattern = r"\[([A-Z_]+)\]"
        # e.g. Hello [USERNAME], your order [ORDER_ID] is complete.

    # ================================================================
    # Configuration Management
    # ================================================================

    # ----------------------------------------------------------------
    def set_platform(self, platform: str):
        """Set default platform."""
        self.platform = platform

    # ----------------------------------------------------------------
    def set_classification_group(self, classification_group_name: str):
        """
        Set default classification group.

        Args:
            classification_group_name: Folder name for classification group
        """
        self.classification_group_name = classification_group_name
        # Clear classification cache when changing group
        self._classification_cache.clear()

    # ----------------------------------------------------------------
    def get_configuration(self) -> dict:
        """Get current configuration."""
        return {
            "platform": self.platform,
            "classification_group_name": self.classification_group_name,
        }

    # ================================================================
    # CRUD Operations (Pass-through to Repository)
    # ================================================================

    # ----------------------------------------------------------------
    def load_template(
        self, platform: Optional[str] = None, template_name: str = None
    ) -> dict:
        """
        Load a template (with caching).

        Args:
            platform: Platform name (uses default if None)
            template_name: Template filename

        Returns:
            Template dict
        """
        platform = platform or self.platform
        if not platform:
            raise ValueError("Platform must be specified or set as default")

        cache_key = f"{platform}:{template_name}"

        # Check cache first
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        # Load from repository
        template = self.prompt_template_repo.load_template(platform, template_name)

        # Cache it
        self._template_cache[cache_key] = template

        return template

    # ----------------------------------------------------------------
    def save_template(
        self,
        template_name: str,
        template_data: dict,
        platform: Optional[str] = None,
        overwrite: bool = False,
    ) -> str:
        """
        Save a template.

        Args:
            template_name: Template filename
            template_data: Template dict
            platform: Platform name (uses default if None)
            overwrite: Whether to overwrite existing

        Returns:
            Path to saved template
        """
        platform = platform or self.platform
        if not platform:
            raise ValueError("Platform must be specified or set as default")

        # Save via repository
        path = self.prompt_template_repo.save_template(
            platform, template_name, template_data, overwrite
        )

        # Invalidate cache for this template
        cache_key = f"{platform}:{template_name}"
        if cache_key in self._template_cache:
            del self._template_cache[cache_key]

        return path

    # ----------------------------------------------------------------
    def delete_template(
        self, template_name: str, platform: Optional[str] = None
    ) -> bool:
        """
        Delete a template.

        Args:
            template_name: Template filename
            platform: Platform name (uses default if None)

        Returns:
            True if deleted, False if didn't exist
        """
        platform = platform or self.platform
        if not platform:
            raise ValueError("Platform must be specified or set as default")

        # Delete via repository
        deleted = self.prompt_template_repo.delete_template(platform, template_name)

        # Invalidate cache
        cache_key = f"{platform}:{template_name}"
        if cache_key in self._template_cache:
            del self._template_cache[cache_key]

        return deleted

    # ----------------------------------------------------------------
    def list_all_template_names(self, platform: Optional[str] = None) -> List[dict]:
        """
        List template names for a platform.

        Args:
            platform: Platform name (uses default if None)

        Returns:
            List of template metadata
        """
        platform = platform or self.platform
        if not platform:
            raise ValueError("Platform must be specified or set as default")

        return self.prompt_template_repo.list_all_template_names(platform)

    # ----------------------------------------------------------------
    def load_all_templates(self, platform: Optional[str] = None) -> List[dict]:
        """
        Load all templates with full data.

        Args:
            platform: Optional platform filter

        Returns:
            List of all templates
        """
        return self.prompt_template_repo.load_all_templates(platform)

    # ----------------------------------------------------------------
    def template_exists(
        self, template_name: str, platform: Optional[str] = None
    ) -> bool:
        """Check if template exists."""
        platform = platform or self.platform
        if not platform:
            raise ValueError("Platform must be specified or set as default")

        return self.prompt_template_repo.template_exists(platform, template_name)

    # ================================================================
    # Cache Management
    # ================================================================

    # ----------------------------------------------------------------
    def clear_template_cache(self, platform: Optional[str] = None):
        """Clear template cache."""
        if platform:
            # Clear only for specific platform
            keys_to_remove = [
                k for k in self._template_cache if k.startswith(f"{platform}:")
            ]
            for key in keys_to_remove:
                del self._template_cache[key]
        else:
            # Clear all
            self._template_cache.clear()

    # ----------------------------------------------------------------
    def clear_classification_cache(self):
        """Clear classification cache."""
        self._classification_cache.clear()

    # ================================================================
    # Prompt Creation (Core Functionality)
    # ================================================================

    # ----------------------------------------------------------------
    def create_prompt(
        self,
        template_name: str,
        video_data: dict,
        comment_context: dict,
        platform: Optional[str] = None,
        classification_group_name: Optional[str] = None,
        classification_format: str = "indicators",
    ) -> str:
        """
        Create a complete prompt ready for LLM.

        Uses cached template and classification data for performance.

        Args:
            template_name: Template to use
            video_data: Dict with VIDEOTITLE, VIDEOCONTEXT, etc.
            comment_context: Dict with TARGETCOMMENT, THREADCOMMENTS, etc.
            platform: Platform name (uses default if None)
            classification_group_name: Classification group folder name (uses default if None)
            classification_format: "full", "indicators", or "explanations"

        Returns:
            Final rendered prompt string
        """
        # Use defaults if not specified
        platform = platform or self.platform
        classification_group_name = (
            classification_group_name or self.classification_group_name
        )

        if not platform:
            raise ValueError("Platform must be specified or set as default")
        if not classification_group_name:
            raise ValueError("Classification group must be specified or set as default")

        # Load template (cached)
        template_data = self.load_template(platform, template_name)
        template_text = template_data["template"]

        # Load classification data (cached)
        classification_data = self._get_classification_group(classification_group_name)

        # Format classifications based on requested format
        classifications_formatted = self.classification_service.format_classifications(
            classification_data, format_type=classification_format
        )

        # Generate all classification format variants (for flexibility)
        classifications_full = self.classification_service.format_classifications(
            classification_data, "full"
        )
        classifications_indicators = self.classification_service.format_classifications(
            classification_data, "indicators"
        )
        classifications_explanations = (
            self.classification_service.format_classifications(
                classification_data, "explanations"
            )
        )

        # Generate output format
        output_format = self.output_format_service.generate_output_format(
            classification_data
        )

        # Combine all variables
        variables = {
            "CLASSIFICATIONS": classifications_formatted,  # Default to requested format
            "CLASSIFICATIONS_FULL": classifications_full,
            "CLASSIFICATIONS_INDICATORS": classifications_indicators,
            "CLASSIFICATIONS_EXPLANATIONS": classifications_explanations,
            "OUTPUTFORMAT": output_format,
            **video_data,
            **comment_context,
        }

        # Render template
        return self._substitute_variables(template_text, variables)

    # ----------------------------------------------------------------
    def _get_classification_group(self, classification_group_name: str) -> dict:
        """
        Get classification data (with caching).

        Args:
            classification_group_name: Classification group folder name

        Returns:
            Classification data dict
        """
        # Check cache
        if classification_group_name in self._classification_cache:
            return self._classification_cache[classification_group_name]

        # Load from file system by folder name
        classification_data = self.classification_service.load_classification_group(
            classification_group_name
        )

        # Cache it
        self._classification_cache[classification_group_name] = classification_data

        return classification_data

    # ================================================================
    # Variable Substitution
    # ================================================================

    # ----------------------------------------------------------------
    def _substitute_variables(self, template: str, variables: dict) -> str:
        """
        Replace all [PLACEHOLDERS] with values.

        Args:
            template: Template string with placeholders
            variables: Dict mapping placeholder names to values

        Returns:
            Rendered string
        """
        rendered = template

        for key, value in variables.items():
            placeholder = f"[{key}]"
            value_str = str(value) if value is not None else ""
            rendered = rendered.replace(placeholder, value_str)

        return rendered

    # ----------------------------------------------------------------
    def detect_placeholders(self, template_text: str) -> List[str]:
        """
        Detect all placeholders in template.

        Args:
            template_text: Template string

        Returns:
            List of placeholder names (without brackets)
        """
        matches = re.findall(self.placeholder_pattern, template_text)
        return list(set(matches))

    # ----------------------------------------------------------------
    def validate_template(
        self, template_name: str, platform: Optional[str] = None
    ) -> dict:
        """
        Validate a template.

        Returns:
            Validation result dict
        """
        platform = platform or self.platform
        if not platform:
            raise ValueError("Platform must be specified or set as default")

        template_data = self.load_template(platform, template_name)
        template_text = template_data["template"]

        detected = self.detect_placeholders(template_text)
        required = template_data.get("required_variables", [])
        optional = template_data.get("optional_variables", [])

        declared = set(required + optional)
        undeclared = [p for p in detected if p not in declared]

        return {
            "valid": len(undeclared) == 0,
            "detected_placeholders": detected,
            "required_variables": required,
            "optional_variables": optional,
            "undeclared_placeholders": undeclared,
        }

    # ----------------------------------------------------------------

##################################################################
