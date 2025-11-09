# CRUD for label groups
# services/classification_service.py
from typing import List, Dict
from enums.classification_output_enum import ClassificationOutputEnum
from models.classification_models import Classification, ClassificationGroup
from models.label_model import Label
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
    def get_classification_group(self, group_name: str) -> ClassificationGroup:
        """
        Alias for load_classification_group for API consistency.
        
        Args:
            group_name: Name of the classification group folder
            
        Returns:
            ClassificationGroup object
        """
        return self.load_classification_group(group_name)

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
        """
        Format classifications with full details (question + indicators).
        
        Returns formatted string with numbered questions and example indicators.
        """
        lines = []
        for i, cls in enumerate(classifications, 1):
            lines.append(f"{i}. {cls.question}")
            
            if cls.pro_indicators:
                lines.append(f"   Positive indicators: {', '.join(cls.pro_indicators[:3])}")
            if cls.con_indicators:
                lines.append(f"   Negative indicators: {', '.join(cls.con_indicators[:3])}")
            if cls.neutral_indicators:
                lines.append(f"   Neutral indicators: {', '.join(cls.neutral_indicators[:3])}")
            
            lines.append("")  # Empty line between classifications
        
        return "\n".join(lines)

    # ----------------------------------------------------------------
    def _format_indicators(self, classifications: List[Classification]) -> str:
        """
        Format classifications with just questions (numbered list).
        
        Returns simple numbered list of classification questions.
        """
        return "\n".join(
            f"{i}. {cls.question}"
            for i, cls in enumerate(classifications, 1)
        )

    # ----------------------------------------------------------------
    def _format_explanation(self, classifications: List[Classification]) -> str:
        """
        Format classifications with explanations of output types.
        
        Returns detailed format including expected output type for each classification.
        """
        lines = []
        for i, cls in enumerate(classifications, 1):
            lines.append(f"{i}. {cls.question}")
            lines.append(f"   Output type: {cls.output_type}")
            
            if cls.output_type == "categorical" and cls.categories:
                lines.append(f"   Valid categories: {', '.join(cls.categories)}")
            
            lines.append("")
        
        return "\n".join(lines)

    # ================================================================
    # Validation
    # ================================================================
    
    # ----------------------------------------------------------------
    def validate_label_for_classification(self,classification: Classification, label: Label) -> bool:
        """
        Validates that a given label matches the rules set by a classification.
        Returns True if valid, else False.
        If classification.output_type is unknown, returns False.
        """
        # Extract value for convenience
        value = label.value
        ot = classification.output_type

        # 1. Boolean type check
        if ot == ClassificationOutputEnum.BOOLEAN:
            return value in {True, False, None}

        # 2. Probability type check
        elif ot == ClassificationOutputEnum.PROBABILITY:
            try:
                return isinstance(value, (float, int)) and 0.0 <= float(value) <= 1.0
            except Exception:
                return False

        # 3. Numeric type check
        elif ot == ClassificationOutputEnum.NUMERIC:
            return isinstance(value, (float, int)) or value is None

        # 4. Categorical type check (single or multi-label)
        elif ot == ClassificationOutputEnum.CATEGORICAL:
            # Ensure categories are provided
            if not classification.categories:
                return False
            # Multi-label
            if classification.allow_multiple:
                if not (isinstance(value, list) or value is None):
                    return False
                # Accept None/empty (for unclassified)
                if value is None:
                    return True
                # Ensure all provided labels are allowed
                return all(v in classification.categories for v in value)
            # Single-label
            else:
                return (value in classification.categories) or (value is None)

        # 5. Text type check (may also allow None)
        elif ot == ClassificationOutputEnum.TEXT:
            return isinstance(value, str) or value is None

        # 6. Pairwise/mapping type check
        elif ot == ClassificationOutputEnum.PAIRWISE:
            # Accept dicts or None
            if value is None:
                return True
            if not isinstance(value, dict):
                return False
            # Optionally: validate dict keys/values (add more rules as required)
            return True

        # Unknown type
        else:
            return False

    # ----------------------------------------------------------------
    def validate_labels(
        self,
        classifications: List[Classification],
        labels: Dict[str, Label]
    ) -> Dict[str, bool]:
        """
        Validates multiple labels against a list of classifications.
        Returns a dict mapping classification name to validation status.
        """
        results = {}
        for classification in classifications:
            label = labels.get(classification.name)
            if label is not None:
                results[classification.name] = self.validate_label_for_classification(classification, label)
            else:
                results[classification.name] = False  # or None, if missing label
        return results

    # ----------------------------------------------------------------
