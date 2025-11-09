# models/content_models.py
"""
content_models.py
=================

Defines abstract base models for social media content that work across platforms
(YouTube, TikTok, Instagram, etc.).

Classes:
    ContentItem: Abstract base for videos, posts, etc.
    Comment: Abstract base for comments across platforms.
    ContentAnalysis: Aggregates content with analysis metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from abc import ABC

from enums.platform_enum import PlatformEnum
from models.label_model import Label

##################################################################
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

##################################################################
@dataclass
class Comment:
    """
    Represents a comment on any platform content.
    
    Platform-agnostic design for comments across YouTube, TikTok, etc.
    
    Attributes:
        comment_id: Unique identifier for this comment.
        content_id: ID of the content this comment belongs to.
        platform: Platform where comment was posted.
        author: Username of the commenter.
        text: The comment text content.
        published_at: ISO 8601 timestamp when posted.
        like_count: Number of likes on the comment.
        reply_count: Number of replies to this comment.
        parent_comment_id: ID of parent comment (for nested replies).
        
        # Analysis fields (populated during classification)
        labels: Classification labels applied to this comment.
    """
    comment_id: str
    content_id: str
    author: str
    text: str
    published_at: str
    like_count: Optional[int] = 0
    reply_count: Optional[int] = 0
    parent_comment_id: Optional[str] = None  # For threaded replies

    # Analysis fields
    labels: Dict[str, Dict[str, Label]] = field(default_factory=dict)
    """
    Dictionary of all classification results for this comment.

    Structure:
        - Top-level keys: Model names (e.g., "gpt-4", "llama-2")
        - Second-level keys: Classification_name (e.g., "toxicity", "spam")
        - Values: Label instance with classification result, confidence, and explanation

    This allows you to store, for each comment, the label produced for each classification task by each model.
    Usage example:

        comment.labels["gpt-4"]["toxicity"] = Label(value=True, confidence=0.98, explanation="Comment uses harmful language.")

    See also: 
        - Label class for explanation of label fields
        - [Python dataclasses — official documentation][web:5]
        - [Dataclass usage for nested objects on GeeksforGeeks][web:3]
    """

##################################################################
@dataclass
class ContentAnalysis:
    """
    Aggregates content with all its comments for analysis.
    
    Platform-agnostic container for content and comment analysis.
    
    Attributes:
        content: The content item (video, post, etc.).
        comments: All comments associated with this content.
    """
    content: ContentItem
    comments: List[Comment] = field(default_factory=list)
    require_reasoning: bool = False  # If True, include explanations/rationales in the answer

##################################################################
