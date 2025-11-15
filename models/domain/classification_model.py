# models/domain/classification_model.py
"""
classification_model.py
=======================

Data model for a single classification task.

Represents one labeling question with its metadata:
- question text
- expected output type
- optional categories and indicators
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

from enums.classification_output_enum import ClassificationOutputEnum


@dataclass
class Classification:
    """
    Represents a classification task with structured label output.

    Attributes:
        name: Unique identifier for the classification task.
        question: The prompt or query for annotation/model.
        explanation: Human-readable explanation/instructions.
        output_type: Output type for the label.
        categories: Allowed values for categorical output (if any).
        allow_multiple: True if multiple categories can be selected.
        indicators: Maps each category label to example indicator phrases.
        require_llm_explanation: If True, LLM must provide an explanation.
    """

    name: str
    question: str
    output_type: ClassificationOutputEnum = ClassificationOutputEnum.CATEGORICAL
    explanation: Optional[str] = None
    categories: Optional[List[str]] = None
    allow_multiple: Optional[bool] = None
    indicators: Optional[Dict[str, List[str]]] = None
    require_llm_explanation: bool = False
