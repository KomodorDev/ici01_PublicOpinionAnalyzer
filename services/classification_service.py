# CRUD for label groups
# services/classification_service.py
from typing import List
from models.classification_models import Classification, ClassificationGroup
from repositories.classification_repository import ClassificationRepository


##################################################################
class ClassificationService:
    """Handles business logic for classification management."""

    # ----------------------------------------------------------------
    def __init__(self):
        self.repository = ClassificationRepository()


    # ================================================================
    # CRUD Operations
    # ================================================================

    # ----------------------------------------------------------------
    def load_all_classification_groups(self) -> List[ClassificationGroup]:
        """Load all classification groups from the repository."""
        return self.repository.load_all_classification_groups()

    # ----------------------------------------------------------------
    def load_classification_group(self, group_name: str) -> ClassificationGroup:
        """
        Load a specific classification group by name.
        
        Args:
            group_name: Name of the classification group folder
            
        Returns:
            ClassificationGroup object
            
        Raises:
            FileNotFoundError: If group doesn't exist
        """
        return self.repository.load_classification_group(group_name)

    # ----------------------------------------------------------------
    def list_classification_group_names(self) -> List[str]:
        """
        Get a list of all available classification group names.
        
        Returns:
            List of group names (folder names)
        """
        return self.repository.list_classification_group_names()

    # ----------------------------------------------------------------
    def save_classification_group(self, group: ClassificationGroup) -> None:
        """Save a classification group."""
        self.repository.save_classification_group(group)

    # ----------------------------------------------------------------
    def delete_classification_group(self, group_name: str) -> None:
        """Delete a classification group."""
        self.repository.delete_classification_group(group_name)

    # ================================================================
    # Prompt Helpers
    # ================================================================

    # ----------------------------------------------------------------
    def get_classification_variants(self) -> List[str]:
        """
        Get list of available classification placeholder variants.
        
        Returns:
            List of placeholder names that can be used in prompt templates
            
        Example:
            ['CLASSIFICATIONS', 'CLASSIFICATIONS_FULL', 'CLASSIFICATIONS_INDICATORS', 'CLASSIFICATIONS_EXPLANATIONS']
        """
        return [
            "CLASSIFICATIONS",
            "CLASSIFICATIONS_FULL",
            "CLASSIFICATIONS_INDICATORS",
            "CLASSIFICATIONS_EXPLANATION"
        ]

    # ----------------------------------------------------------------
    def get_classification_group_to_string(self, group_name: str, variant: str) -> str:
        """
        Returns the formatted string for a given classification group/variant.
        """
        variant_map = {
            "CLASSIFICATIONS": self._format_indicators,
            "CLASSIFICATIONS_FULL": self._format_full,
            "CLASSIFICATIONS_INDICATORS": self._format_indicators,
            "CLASSIFICATIONS_EXPLANATION": self._format_explanation,
        }
        group = self.load_classification_group(group_name)
        formatter = variant_map.get(variant)
        if not formatter:
            raise ValueError(f"Unknown classification variant: {variant}")
        return formatter(group.classifications)

    # ----------------------------------------------------------------
    def _format_full(self, classifications: List[Classification]) -> str:
        """Mock: Format with full details."""
        return "test_full - Implementation currently missing"

    # ----------------------------------------------------------------
    def _format_indicators(self, classifications: List[Classification]) -> str:
        """Mock: Format with indicators."""
        return "test_indicators - Implementation currently missing"

    # ----------------------------------------------------------------
    def _format_explanation(self, classifications: List[Classification]) -> str:
        """Mock: Format with explanations."""
        return "test_explanation - Implementation currently missing"
##################################################################
