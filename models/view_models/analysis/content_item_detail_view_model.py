# models/view/content_item_detail_view_model.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from enums.platform_enum import PlatformEnum
from enums.sort_by_enum import SortByEnum
from enums.sort_dir_enum import SortDirEnum
from .video_model_info_view_model import VideoModelInfoViewModel


@dataclass
class ContentItemDetailViewModel:
    """
    Detail panel ViewModel for the currently selected ContentItem.
    Pure UI projection of the domain models (ContentItem + ContentAnalysis).
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------
    platform: PlatformEnum
    content_id: str

    url: str

    # ---------------------------------------------------------
    # Metadata (lightweight, UI-friendly)
    # ---------------------------------------------------------
    title: str
    author: str
    description: Optional[str]
    view_count: Optional[int]
    like_count: Optional[int]
    comment_count: Optional[int]

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------
    summary_text: str
    summary_status: str              # "idle" | "running" | "done" | "error"
    summary_source: Optional[str]    # "manual" | "ai" | None

    # ---------------------------------------------------------
    # Per-content analysis config
    # ---------------------------------------------------------
    sort_by: SortByEnum
    sort_dir: SortDirEnum
    limit: int                       # e.g. 20 / 50 / 100 / 1000

    selected_prompt_template_name: Optional[str]
    selected_classification_group_name: Optional[str]

    # ---------------------------------------------------------
    # Dropdown (choice) data for the right panel
    # ---------------------------------------------------------
    # Just names/ids for templates and groups.
    available_prompt_templates: List[str]
    available_classification_groups: List[str]

    # Sorting options as enums (Gradio uses .value)
    available_sort_by_options: List[SortByEnum]
    available_sort_dir_options: List[SortDirEnum]

    # Full LLM model choices (viewmodel projection of LLMModelInfo)
    available_summary_models: List[VideoModelInfoViewModel]
