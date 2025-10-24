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
from typing import List, Literal, Optional

ClassificationOutputType = Literal[
    "boolean",        # True / False
    "probability",    # float 0‑1
    "numeric",        # continuous or ordinal number
    "categorical",    # string category
    "text"            # open string
]


@dataclass
class Classification:
    """
    Represents a single classification question and its expected output type.

    Each Classification defines a labeling task such as
    "Is the comment pro‑Taiwan?" and can specify whether the
    answer should be boolean, probabilistic, numeric, categorical,
    or free‑form text.

    Attributes:
        id (str): Unique identifier for this classification.
        question (str): The question or task prompt to guide analysis.
        output_type (ClassificationOutputType): Specifies the kind of expected label.
            - 'boolean' → True / False / None
            - 'probability' → a float from 0.0 to 1.0
            - 'numeric' → an integer or float score
            - 'categorical' → one of multiple category strings
            - 'text' → free‑form textual explanation
        pro_indicators (list[str]): Example phrases suggesting a positive stance.
        con_indicators (list[str]): Example phrases suggesting a negative stance.
        neutral_indicators (list[str]): Sentences indicating neutrality or ambiguity.
        categories (Optional[list[str]]): Allowed category values if output_type=='categorical'.
    """

    id: str
    question: str
    output_type: ClassificationOutputType = "boolean"
    pro_indicators: List[str] = field(default_factory=list)
    con_indicators: List[str] = field(default_factory=list)
    neutral_indicators: List[str] = field(default_factory=list)
    categories: Optional[List[str]] = None  # e.g. ["pro", "neutral", "anti"]


@dataclass
class ClassificationGroup:
    """
    Organizes multiple `Classification` objects into a named thematic group.

    Each `ClassificationGroup` serves as a container for related classification
    questions that share a conceptual purpose — for example, the group
    "Political Alignment" could contain classifications such as
    "Is the comment pro‑Taiwan?" and "Is the comment anti‑China?".

    Attributes:
        id (str):
            Unique identifier for this group.
        name (str):
            Human-readable title of the group.
        classifications (list[Classification]):
            A list of `Classification` instances that belong to this group.
    """

    id: str
    name: str
    classifications: List[Classification] = field(default_factory=list)
