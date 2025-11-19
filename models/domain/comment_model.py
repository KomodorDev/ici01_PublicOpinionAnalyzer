# models/domain/comment_model.py
"""
comment_model.py
================

Platform-agnostic comment model usable across YouTube, TikTok, etc.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

from models.domain.label_model import Label


@dataclass
class Comment:
    """
    Represents a comment on any platform content.

    Attributes:
        comment_id: Unique identifier for this comment.
        content_id: ID of the content this comment belongs to.
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

    This allows you to store, for each comment, the label produced for each
    classification task by each model.

    Example:

        comment.labels["gpt-4"]["toxicity"] = Label(
            value=True,
            confidence=0.98,
            explanation="Comment uses harmful language.",
        )
    """
