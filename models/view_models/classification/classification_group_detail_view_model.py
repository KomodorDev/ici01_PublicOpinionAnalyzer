"""
classification_group_detail_view_model
======================================
Editable view-model for a single classification group.

This model is used to render and edit the selected group's details, including
its list of classification view-models and the UI selection index.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from models.view_models.classification.classification_view_model import (
    ClassificationViewModel,
)


@dataclass
class ClassificationGroupDetailViewModel:
    """
    Full editable state for one selected group.

    This is what fills:
      - group name textbox
      - left classification list
      - selection index
    """

    name: str = ""
    classifications: List[ClassificationViewModel] = field(default_factory=list)

    # UI-only selection state inside the group
    selected_index: int = 0
