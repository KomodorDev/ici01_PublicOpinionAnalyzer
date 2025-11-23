"""
classification_output_enum.py

This module defines the supported output types for structured content classification tasks.
It standardizes how model, LLM, or human-generated answers to labeling questions are represented and validated.

Output types include:
- BOOLEAN: For binary yes/no analysis.
- PROBABILITY: For model confidence values in the [0.0, 1.0] range.
- NUMERIC: For scores, ratings, or counts.
- CATEGORICAL: For selection among user-defined categories, including sentiment and stance.
- TEXT: For free-form explanations or extractions.
- PAIRWISE: For mappings—such as entity-level results or multi-target annotations.

This schema is designed for extensibility, allowing robust validation and prompt alignment in multi-task, multi-model analysis workflows.
"""

from enum import Enum

class ClassificationOutputEnum(str, Enum):
    """
    Defines the possible output types for classification tasks.

    Types:
        BOOLEAN:
            - Used for binary questions or yes/no decisions.
            - Allowed values: True, False, None (None/"N/A" means insufficient context).

        PROBABILITY:
            - Used when the output is a likelihood or confidence score.
            - Allowed values: float in [0.0, 1.0], or None if not applicable.

        NUMERIC:
            - Used for numerical results such as counts, scores, or ratings.
            - Allowed values: integer or float, or None if not applicable.

        CATEGORICAL:
            - Used when the answer must be one value from a predefined set of categories (e.g., "positive", "neutral", "negative").
            - Allowed values: one of the configured category strings, "N/A", or None.

        TEXT:
            - Used for arbitrary free-form string responses (e.g., explanations, extractions).
            - Allowed values: any string, optionally "N/A" or empty string for non-applicable.

        PAIRWISE:
            - Used for entity-level or mapping outputs, where each item (e.g., country, product, aspect) is assigned a value.
            - Allowed values: dict mapping keys (entities) to values (usually boolean, categorical, numeric, etc.), or list of (key, value) pairs.
            - Example: {"Japan": True, "China": False}, or [("Japan", True), ("China", False)]
    """

    BOOLEAN = "boolean"           # Binary decision/question (True/False/None)
    PROBABILITY = "probability"   # Likelihood/confidence (float 0.0–1.0 or None)
    NUMERIC = "numeric"           # Score/count/rating (int/float or None)
    CATEGORICAL = "categorical"   # One of N configured categories ("positive", "neutral", "negative", "None")
    TEXT = "text"                 # Free-form string or explanation ("None"if uncertain)
    # PAIRWISE = "pairwise"         # Mapping or entity/value pairs—dict or list of (key, value) such as {"country": bool}

    def __str__(self) -> str:
        return self.value
