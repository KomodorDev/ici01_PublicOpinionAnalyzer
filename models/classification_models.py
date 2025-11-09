"""
classification_models.py
========================

This module defines the data models used to represent classification logic
for analyzing comments or text segments. It includes the `Classification`
and `ClassificationGroup` entities that describe labeling tasks and their
organization within thematic groups.

These models are part of the application's data layer and provide a clean,
structured representation of classification definitions used by the Label
Manager. Each `ClassificationGroup` stores a set of related binary
classifications (e.g., "Is the comment pro‑Taiwan?"), along with
textual indicators that guide interpretation.

Classes:
    Classification:
        Defines a single labeling question and its example indicators.
    ClassificationGroup:
        Groups multiple `Classification` objects under one logical category.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional
from enums.classification_output_enum import ClassificationOutputEnum

##################################################################
@dataclass
class Classification:
    """
    Represents a classification task with structured label output.

    Attributes:
        name (str): Unique identifier for the classification task.
        question (str): The prompt or query for annotation/model.
        explanation (str): Human-readable explanation/instructions.
        output_type (ClassificationOutputType): Output type for the label.
        categories (Optional[List[str]]): Allowed values for categorical output.
        allow_multiple (bool): True if multiple categories can be selected for an answer.
        indicators (Dict[str, List[str]]): Maps each category label to its example indicator phrases.

    Example:
        Classification(
            name="agreement_level",
            question="What level of agreement does the comment express?",
            explanation="Annotate the degree of agreement using the provided categories.",
            output_type=ClassificationOutputType.CATEGORICAL,
            categories=["totally_agree", "partially_agree", "neutral", "disagree", "N/A"],
            allow_multiple=False,
            indicators={
                "totally_agree": ["I fully support", "Absolutely correct"],
                "partially_agree": ["I mostly agree", "Generally valid"],
                "neutral": ["No clear opinion", "Neutral statement"],
                "disagree": ["I don't support", "Completely wrong"]
            }
        )
    """

    name: str
    question: str
    output_type: ClassificationOutputEnum = ClassificationOutputEnum.CATEGORICAL
    explanation: Optional[str] = None
    categories: Optional[List[str]] = None
    allow_multiple: Optional[bool] = None
    indicators: Optional[Dict[str, List[str]]] = None

##################################################################
@dataclass
class ClassificationGroup:
    """
    Organizes multiple `Classification` objects into a named thematic group.

    Each `ClassificationGroup` serves as a container for related classification
    questions that share a conceptual purpose — for example, the group
    "Political Alignment" could contain classifications such as
    "Is the comment pro‑Taiwan?" and "Is the comment anti‑China?".

    Attributes:
        name (str):
            Unique Human-readable title of the group.
        classifications (list[Classification]):
            A list of `Classification` instances that belong to this group.
    """

    name: str
    classifications: List[Classification] = field(default_factory=list)

##################################################################
