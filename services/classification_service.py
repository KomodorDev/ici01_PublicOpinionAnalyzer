"""
classification_service.py
=========================

Business logic layer for working with classification groups and labels.

Responsibilities:
- CRUD operations for ClassificationGroup objects (delegating persistence to ClassificationRepository).
- Building human-readable descriptions for classification groups to embed into LLM prompts.
- Building the [OUTPUTFORMAT] JSON hint that shows the exact expected output structure.
- Validating Label objects against their Classification definitions.
"""

from __future__ import annotations

import json
from typing import List, Dict, Any

from enums.classification_output_enum import ClassificationOutputEnum
from models.domain import ClassificationGroup, Classification, Label
from repositories.classification_repository import ClassificationRepository


##################################################################
class ClassificationService:
    """Handles business logic for classification management."""

    # ----------------------------------------------------------------
    def __init__(self):
        self.repository = ClassificationRepository()

        # Cache for human-readable group description used in prompts
        self._classification_group_string_cache: dict[str, str] = {}

        # Cache for the [OUTPUTFORMAT] JSON hint (one per classification_group)
        self._classification_group_schema_cache: dict[str, str] = {}

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
    def get_classification_group_string(
        self, classification_group: ClassificationGroup
    ) -> str:
        """
        Return a cached or freshly built human-readable description of the
        given classification group, suitable for embedding into prompts.
        """
        key = classification_group.name

        # Cached?
        cached = self._classification_group_string_cache.get(key)
        if cached is not None:
            return cached

        # Build and cache
        result = self._format_classification_group_for_prompt(classification_group)
        self._classification_group_string_cache[key] = result

        return result

    # ---------------------------------------------------------
    def _format_classification_group_for_prompt(
        self,
        classification_group: ClassificationGroup,
    ) -> str:
        """
        Build a human-readable description of all classifications in this group
        for inclusion in the LLM prompt.
        """

        lines: list[str] = []
        lines.append(f"Classification group: {classification_group.name}")
        lines.append("")  # blank line

        for c in classification_group.classifications:
            # Header line with name + question
            lines.append(f"- {c.name}: {c.question}")

            # Optional explanation
            if c.explanation:
                lines.append(f"  Explanation: {c.explanation}")

            # Output type (handle Enum or plain str)
            output_type_value = getattr(c.output_type, "value", str(c.output_type))
            lines.append(f"  Output type: {output_type_value}")

            # Optional categories
            if c.categories:
                categories_str = ", ".join(c.categories)
                lines.append(f"  Categories: {categories_str}")

            # Optional multi-select flag
            if c.allow_multiple is not None:
                lines.append(
                    f"  Allow multiple categories: {'yes' if c.allow_multiple else 'no'}"
                )

            # Optional indicators: dict[category -> list[str]]
            if c.indicators:
                lines.append("  Indicators:")
                for category, indicator_list in c.indicators.items():
                    if not indicator_list:
                        continue
                    examples = "; ".join(indicator_list)
                    lines.append(f"    - {category}: {examples}")

            # Optional: require_llm_explanation flag
            if c.require_llm_explanation:
                lines.append("  The model must provide an explanation for this label.")

            # blank line between classifications
            lines.append("")

        return "\n".join(lines)

    # ----------------------------------------------------------------
    def build_outputformat_hint_json(
        self,
        classification_group: ClassificationGroup,
    ) -> str:
        """
        Build (and cache) the JSON 'hint' for the [OUTPUTFORMAT] placeholder.

        This does NOT contain real values, only example/type hints, but it
        shows the exact JSON structure the LLM must return:

        {
          "<ClassificationName>": {
            "value": "<...type hint...>",
            "explanation": "<string: brief explanation>"   // only if require_llm_explanation is True
          },
          ...
        }
        """

        key = classification_group.name

        # 1) Check cache first
        cached = self._classification_group_schema_cache.get(key)
        if cached is not None:
            return cached

        # 2) Build spec fresh
        spec: dict[str, dict[str, Any]] = {}

        for c in classification_group.classifications:
            entry: dict[str, Any] = {}

            # "value" hint depends on output_type / categories / allow_multiple
            entry["value"] = self._build_value_hint_string(c)

            # Only include explanation if required
            if c.require_llm_explanation:
                entry["explanation"] = (
                    "<string: brief explanation for this classification>"
                )

            spec[c.name] = entry

        # 3) Serialize to pretty JSON for prompt
        json_str = json.dumps(spec, indent=2, ensure_ascii=False)

        # 4) Store in cache
        self._classification_group_schema_cache[key] = json_str
        return json_str

    # ---------------------------------------------------------
    def _build_value_hint_string(self, c: Classification) -> str:
        """
        Build a human-readable type hint string for the 'value' field,
        based on output_type, categories, allow_multiple.

        This is what appears in [OUTPUTFORMAT] for each classification's "value".
        """
        t = c.output_type  # this is a ClassificationOutputEnum

        if t is ClassificationOutputEnum.BOOLEAN:
            return "<boolean: true or false, or null if unknown>"

        if t is ClassificationOutputEnum.PROBABILITY:
            return "<float: between 0.0 and 1.0, or null if unknown>"

        if t is ClassificationOutputEnum.NUMERIC:
            return "<number: integer or float, or null if unknown>"

        if t is ClassificationOutputEnum.CATEGORICAL:
            if c.categories:
                cats_str = ", ".join(repr(cat) for cat in c.categories)
                if c.allow_multiple:
                    return (
                        f"<array of strings: zero or more of [{cats_str}], "
                        "or empty array if none apply>"
                    )
                else:
                    return f"<string: one of [{cats_str}], or null if unknown>"
            else:
                # No categories configured, fallback
                if c.allow_multiple:
                    return "<array of strings: zero or more category labels>"
                else:
                    return "<string: single category label, or null>"

        if t is ClassificationOutputEnum.TEXT:
            return "<string: free-form text, or null if no answer>"

        # Fallback for unknown/extended types
        return "<value: type depends on classification definition>"

    # ================================================================
    # Validation
    # ================================================================

    # ----------------------------------------------------------------
    def validate_label_for_classification(
        self, classification: Classification, label: Label
    ) -> bool:
        """
        Validate a Label against a Classification definition.
        Ensures: correct type, allowed values, explanation if required.
        """

        value = label.value
        explanation = label.explanation
        t = classification.output_type

        # ---- BOOLEAN ----
        if t is ClassificationOutputEnum.BOOLEAN:
            if value is None:
                pass  # allowed
            elif isinstance(value, bool):
                pass  # allowed
            else:
                return False

        # ---- PROBABILITY ----
        elif t is ClassificationOutputEnum.PROBABILITY:
            if value is None:
                pass
            elif isinstance(value, (int, float)):
                if not (0.0 <= float(value) <= 1.0):
                    return False
            else:
                return False

        # ---- NUMERIC ----
        elif t is ClassificationOutputEnum.NUMERIC:
            if value is None:
                pass
            elif isinstance(value, (int, float)):
                pass
            else:
                return False

        # ---- CATEGORICAL ----
        elif t is ClassificationOutputEnum.CATEGORICAL:
            categories = classification.categories or []

            if value is None:
                pass

            elif classification.allow_multiple:
                # Must be a list of valid categories
                if not isinstance(value, list):
                    return False
                for v in value:
                    if v not in categories:
                        return False

            else:
                # Must be a single value
                if value not in categories and value is not None:
                    return False

        # ---- TEXT ----
        elif t is ClassificationOutputEnum.TEXT:
            if value is None:
                pass
            elif isinstance(value, str):
                pass
            else:
                return False

        else:
            # Unknown output type
            return False

        # ---- Explanation requirement ----
        if classification.require_llm_explanation:
            if not explanation or not isinstance(explanation, str):
                return False

        # Passed all checks
        return True

    # ----------------------------------------------------------------
    def validate_labels(
        self, classifications: List[Classification], labels: Dict[str, Label]
    ) -> Dict[str, bool]:
        """
        Validates multiple labels against a list of classifications.
        Returns a dict mapping classification name to validation status.
        """
        results = {}
        for classification in classifications:
            label = labels.get(classification.name)
            if label is not None:
                results[classification.name] = self.validate_label_for_classification(
                    classification, label
                )
            else:
                results[classification.name] = False  # or None, if missing label
        return results

    # ----------------------------------------------------------------

def main():
    """Main"""
    # Minimal fake data to test formatting and OUTPUTFORMAT generation.
    # Adjust constructor calls if your actual dataclasses differ.

    demo_classifications = [
        Classification(
            name="IsProTaiwan",
            question="Is this comment supportive of Taiwan?",
            explanation="True if the comment clearly supports Taiwan, false otherwise.",
            output_type=ClassificationOutputEnum.BOOLEAN,
            categories=None,
            allow_multiple=None,
            indicators={
                "true": ["praises Taiwan", "supports independence"],
                "false": ["criticizes Taiwan", "supports PRC narrative"],
            },
            require_llm_explanation=True,
        ),
        Classification(
            name="Tone",
            question="What is the tone of this comment?",
            explanation="Choose the main emotional tone.",
            output_type=ClassificationOutputEnum.CATEGORICAL,
            categories=["positive", "neutral", "negative"],
            allow_multiple=False,
            indicators={
                "positive": ["praise", "optimistic wording"],
                "neutral": ["matter-of-fact", "no emotional language"],
                "negative": ["insults", "frustration", "anger"],
            },
            require_llm_explanation=False,
        ),
    ]

    demo_group = ClassificationGroup(
        name="DemoGroup",
        classifications=demo_classifications,
    )

    svc = ClassificationService()

    print("=== Human-readable classification group string ===")
    print(svc.get_classification_group_string(demo_group))
    print()

    print("=== [OUTPUTFORMAT] JSON hint ===")
    print(svc.build_outputformat_hint_json(demo_group))
    print()

if __name__ == "__main__":
    main()

# python -m services.classification_service