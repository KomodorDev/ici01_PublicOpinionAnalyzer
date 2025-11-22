"""
classification_group_list_view_model.py
=======================================
Lightweight view-model for a classification group used in list/dropdown UI.

This module defines a compact dataclass intended for fast rendering in
selection widgets (sidebar, dropdown). It intentionally contains just the
minimal fields needed by the view.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ClassificationGroupListViewModel:
    """Lightweight list item for group dropdown / sidebar.

    This should be cheap to render and stable for identity.
    """

    name: str
    classification_count: int = 0  # optional, but nice for UI labels
