# models/domain/content_analysis_model.py
"""
content_analysis_model.py
=========================

Container that aggregates a ContentItem with its comments and
per-content analysis configuration.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


from enums import SortDirEnum, SortByEnum, TaskStatusEnum

from models.domain.content_item_model import ContentItem
from models.domain.comment_model import Comment
from models.domain.classification_models_OLD import ClassificationGroup
from models.domain.prompt_template_model import PromptTemplate
from models.domain.model_run_progress_model import ModelRunProgress



@dataclass
class ContentAnalysis:
    """
    Aggregates content with all its comments for analysis.

    Platform-agnostic container for content and comment analysis.

    Attributes:
        content: The content item (video, post, etc.).
        comments: All comments associated with this content.
        prompt_template: Selected prompt template for this content.
        classification_group: Selected classification group.
        models: List of model client objects (type depends on your infra).
        sort_by: Sorting key for fetching comments (e.g. RELEVANCE).
        sort_dir: Sorting direction (ASC/DSC).
        limit: Max number of comments to fetch/analyze.
    """

    # Core
    content: ContentItem

    # Per-content analysis config (non-defaults first)
    sort_by: SortByEnum = SortByEnum.DEFAULT
    sort_dir: SortDirEnum = SortDirEnum.DSC
    limit: int  = None  # e.g. 20 / 50 / 100 / 1000

    # Optional configuration / runtime data
    prompt_template: Optional[PromptTemplate] = None
    classification_group: Optional[ClassificationGroup] = None
    models: Optional[List[Any]] = None  # adapt type as you define your model clients

    # Comments (filled after fetching)
    comments: List[Comment] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Convenience properties for identification
    # ------------------------------------------------------------------
    @property
    def platform(self):
        """Unique ID part 1 — platform namespace (e.g., youtube, tiktok)."""
        return self.content.platform

    @property
    def content_id(self) -> str:
        """Unique ID part 2 — platform-specific unique content identifier."""
        return self.content.content_id

    @property
    def url(self) -> str:
        """Convenience: direct access to the canonical URL."""
        return self.content.url

    # --------------------------------------------------
    # Progress: step 1 – fetching comments (yt-dlp)
    # --------------------------------------------------
    fetch_status: TaskStatusEnum = TaskStatusEnum.PENDING
    fetch_progress: float = 0.0     # 0.0–1.0
    fetch_error: Optional[str] = None
    fetch_status_text: str = ""                             # last line from yt-dlp / human status

    # --------------------------------------------------
    # Progress: step 2 – analyzing comments (per model)
    # --------------------------------------------------
    # One ModelRunProgress per (provider, model_name) on this content
    model_run_progress: List[ModelRunProgress] = field(default_factory=list)

    # --------------------------------------------------
    # Progress: step 3 – exporting results
    # --------------------------------------------------
    export_status: TaskStatusEnum = TaskStatusEnum.PENDING
