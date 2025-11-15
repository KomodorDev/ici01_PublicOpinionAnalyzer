# models/view/content_item_list_view_model.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from enums.platform_enum import PlatformEnum


@dataclass
class ContentItemListViewModel:
    """
    One row in the left-side 'parsed content' list.
    Projection of a ContentItem domain model only with UI-relevant fields.
    """

    platform: PlatformEnum
    content_id: str
    url: str
    title: str

    # Optional lightweight metadata for display
    author: Optional[str] = None
    comment_count: Optional[int] = None

    # UI-only flag: which item is currently selected in the view
    is_selected: bool = False
