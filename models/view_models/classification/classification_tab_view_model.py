"""
classification_tab_view_model.py
================================
View-model representing the full page state of the Classification UI.

This module contains a single dataclass that aggregates the collections and
selected items shown on the classification management screen. It is a pure
presentation model used by controllers/views; no domain logic belongs here.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from models.view_models.classification.classification_group_list_view_model import (
    ClassificationGroupListViewModel,
)
from models.view_models.classification.classification_group_detail_view_model import (
    ClassificationGroupDetailViewModel,
)
from models.view_models.classification.classification_view_model import (
    ClassificationViewModel,
)


@dataclass
class ClassificationTabViewModel:
    """
    Full state for the Classification management view.

    Mirrors the UI:
      - group dropdown/list
      - selected group detail
      - selected classification detail
      - page-level messages
    """

    # ------------------------------
    # Group list (for top dropdown)
    # ------------------------------
    group_contents: Optional[List[ClassificationGroupListViewModel]] = None

    # ------------------------------
    # Selected group (detail panel)
    # ------------------------------
    selected_group: Optional[ClassificationGroupDetailViewModel] = None

    # ------------------------------
    # Selected classification (right editor)
    # Optional because group can be empty.
    # ------------------------------
    selected_classification: Optional[ClassificationViewModel] = None

    # ------------------------------
    # Page-level messages
    # ------------------------------
    info_message: Optional[str] = None
    error_message: Optional[str] = None
