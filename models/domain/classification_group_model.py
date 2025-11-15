# models/domain/classification_group_model.py
"""
classification_group_model.py
=============================

Groups multiple `Classification` objects into a named thematic group.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from models.domain.classification_model import Classification


@dataclass
class ClassificationGroup:
    """
    Organizes multiple `Classification` objects into a named thematic group.

    Each `ClassificationGroup` serves as a container for related classification
    questions that share a conceptual purpose — for example, the group
    "Political Alignment" could contain classifications such as
    "Is the comment pro-Taiwan?" and "Is the comment anti-China?".

    Attributes:
        name:
            Human-readable title of the group.
        classifications:
            A list of `Classification` instances that belong to this group.
    """

    name: str
    classifications: List[Classification] = field(default_factory=list)
