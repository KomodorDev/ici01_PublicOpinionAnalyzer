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
from models.content_models import ContentItem, Comment


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
        platform: Optional[str] = None,
        prompt_template_name: Optional[str] = None,
        classification_group_name: Optional[str] = None,
        content_item: Optional[ContentItem] = None,
        classification_service: Optional[ClassificationService] = None,
        output_format_service: Optional[OutputFormatService] = None,
    ):
        """
        Initialize PromptService.

        Args:
            prompt_template_repository: Repository for prompt template storage (required)
            platform: Default platform (e.g., 'youtube')
            prompt_template_name: Default prompt template to use
            classification_group_name: Default classification group folder name
            content_item: Optional ContentItem to extract metadata from
            classification_service: Service for classification operations (optional, needed for create_prompt)
            output_format_service: Service for output format generation (optional, needed for create_prompt)
        """
        self.prompt_template_repository = prompt_template_repository

        # Persistent configuration
        self.platform = platform
        self.prompt_template_name = prompt_template_name
        self.classification_group_name = classification_group_name

        # Store content item reference
        self.content_item = content_item

        # Optional services (only needed for prompt creation)
        self.classification_service = classification_service
        self.output_format_service = output_format_service

        # Simple caching - single values per instance
        self._cached_prompt_template: Optional[dict] = None
        self._cached_classifications_string: Optional[str] = None
        self._cached_output_format: Optional[str] = None

        # Track what format is cached to avoid regeneration
        self._cached_classification_variant: Optional[str] = None

        # Regex pattern for placeholder detection
        self.placeholder_pattern = r"\[([A-Z_]+)\]"

        # Load and cache prompt template if platform and name are provided
        if self.platform and self.prompt_template_name:
            self._cached_prompt_template = (
                self.prompt_template_repository.load_prompt_template(
                    self.platform, self.prompt_template_name
                )
            )

            # Detect which placeholders are used in the template
            prompt_template_text = self._cached_prompt_template["template"]
            used_placeholders = self.detect_placeholders(prompt_template_text)

            # Determine which classification variant is used and cache it
            if self.classification_service and self.classification_group_name:
                classification_variant = self._get_used_classification_variant(
                    used_placeholders
                )

                # Load and cache the appropriate format
                self._cached_classifications_string = (
                    self.classification_service.get_classification_group_to_string(
                        self.classification_group_name, classification_variant or "CLASSIFICATIONS"
                    )
                )

            # Load and cache output format if needed
            if self.output_format_service and self.classification_group_name:
                self._cached_output_format = (
                    self.output_format_service.get_output_format_string(
                        self.classification_group_name
                    )
                )

    # ----------------------------------------------------------------
    def _get_used_classification_variant(
        self, used_placeholders: List[str]
    ) -> Optional[str]:
        """
        Returns the used classification variant placeholder name (e.g. 'CLASSIFICATIONS_FULL') or None.
        """
        if not self.classification_service:
            return None
        available_variants = self.classification_service.get_classification_variants()
        for variant in available_variants:
            if variant in used_placeholders:
                return variant
        return None

    # ================================================================
    # CRUD Operations (Pass-through to Repository)
    # ================================================================

    # ----------------------------------------------------------------
    def load_prompt_template(
        self, template_name: str, platform: Optional[str] = None, ) -> dict:
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

        # Load from repository
        template = self.prompt_template_repository.load_prompt_template(
            platform, template_name
        )

        return template

    # ----------------------------------------------------------------
    def save_prompt_template(
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
        path = self.prompt_template_repository.save_prompt_template(
            platform, template_name, template_data, overwrite
        )

        return path

    # ----------------------------------------------------------------
    def delete_prompt_template(
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
        deleted = self.prompt_template_repository.delete_prompt_template(
            platform, template_name
        )

        return deleted

    # ----------------------------------------------------------------
    def list_all_prompt_template_names(
        self, platform: Optional[str] = None
    ) -> List[dict]:
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

        return self.prompt_template_repository.list_all_prompt_template_names(platform)

    # ----------------------------------------------------------------
    def load_all_prompt_templates(self, platform: Optional[str] = None) -> List[dict]:
        """
        Load all templates with full data.

        Args:
            platform: Optional platform filter

        Returns:
            List of all templates
        """
        return self.prompt_template_repository.load_all_prompt_templates(platform)

    # ================================================================
    # Prompt Creation (Core Functionality)
    # ================================================================

    # ----------------------------------------------------------------
    def create_prompt(self, comment: Comment) -> str:
        """
        Create a complete prompt ready for LLM using cached data.

        Args:
            comment: Comment object to generate prompt for

        Returns:
            Final rendered prompt string
        """
        if not self._cached_prompt_template:
            raise ValueError(
                "Prompt template not cached. Initialize PromptService with "
                "platform and prompt_template_name."
            )

        if not self.content_item:
            raise ValueError(
                "ContentItem not provided. Initialize PromptService with content_item."
            )

        # Build comment context from comment object
        comment_context = {
            "TARGETCOMMENT": comment.text,
            "THREADCOMMENTS": "THREADCOMMENTS_Test - Implementation currently missing",  # TODO
            "TAGGEDCOMMENTS": "TaggedComments_Test - Implementation currently missing",  # TODO
            "COMMENTAUTHOR": comment.author,
            # ... whatever other comment fields you need
        }

        # Build variables from cached/stored data
        variables = {
            # Cached at init
            "CLASSIFICATIONS": self._cached_classifications_string or "",
            "OUTPUTFORMAT": self._cached_output_format or "",
            # From content_item
            "VIDEOTITLE": self.content_item.title,
            "VIDEOCONTEXT": self.content_item.summary,
            # From comment
            **comment_context,
        }
        
        return self._substitute_variables(
            self._cached_prompt_template["template"], variables
        )

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

        template_data = self.load_prompt_template(platform, template_name)
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

def main():
    """Test the PromptService class."""
    # Create a ContentItem
    content_item = ContentItem(
        content_id="vid123",
        platform="youtube",
        url="https://youtube.com/watch?v=abc123",
        title="How to Build Amazing Apps",
        author="TechGuru",
        description="A comprehensive tutorial on app development",
        view_count=50000,
        like_count=3200,
        summary="This video covers the fundamentals of modern app development including architecture, testing, and deployment.",
    )

    # Create a Comment
    comment = Comment(
        comment_id="comment456",
        content_id="vid123",
        platform="youtube",
        author="user789",
        text="This is an incredibly toxic comment that should be flagged!",
        published_at="2025-11-05T18:30:00Z",
        like_count=5,
    )

    # Initialize services
    prompt_template_repo = PromptTemplateRepository()
    classification_service = ClassificationService()
    output_format_service = OutputFormatService()

    # Create PromptService
    prompt_service = PromptService(
        prompt_template_repository=prompt_template_repo,
        platform="youtube",
        prompt_template_name="default",
        classification_group_name="Default",
        content_item=content_item,
        classification_service=classification_service,
        output_format_service=output_format_service,
    )

    # Test create_prompt
    try:
        prompt = prompt_service.create_prompt(comment)

        print("=" * 80)
        print("GENERATED PROMPT:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)

    except Exception as e:
        print(f"Error creating prompt: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

# python -m services.prompt_service
