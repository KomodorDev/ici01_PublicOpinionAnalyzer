# models/domain/content_item_model.py
"""
content_item_model.py
=====================

Abstract base class for platform content items (videos, posts, etc.)
that works across platforms (YouTube, TikTok, Instagram, ...).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from abc import ABC

from enums.platform_enum import PlatformEnum


@dataclass
class ContentItem(ABC):
    """
    Abstract base class for platform content (videos, posts, etc.).

    All platform-specific content types inherit from this base.

    Attributes:
        content_id: Unique identifier for this content.
        platform: Platform name (e.g., "youtube", "tiktok").
        url: Full URL to the content.
        title: Content title or caption.
        author: Username or channel name of the creator.
        description: Content description or caption.
        published_at: ISO 8601 timestamp of publication.
        view_count: Number of views.
        like_count: Number of likes.
        comment_count: Total number of comments.

        # Analysis metadata (user/AI-generated)
        summary: Optional content summary.
        summary_source: Origin of summary ("manual" | "ai" | None).
    """
    content_id: str
    platform: PlatformEnum
    url: str
    title: str
    author: str
    description: Optional[str] = None
    published_at: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None

    # Analysis fields (populated later)
    summary: Optional[str] = None
    summary_source: Optional[str] = None  # "manual" | "ai"
