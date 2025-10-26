# models/youtube_models.py
"""
youtube_models.py
=================

YouTube-specific implementations of content models.
"""

from dataclasses import dataclass
from typing import Optional
from models.content_models import ContentItem

##################################################################
@dataclass
class YouTubeVideo(ContentItem):
    """
    YouTube-specific video metadata.
    
    Extends ContentItem with YouTube-specific fields.
    
    Attributes:
        channel_id: YouTube channel identifier.
        duration: Video duration in ISO 8601 format (e.g., "PT15M33S").
        category_id: YouTube category ID.
    """
    channel_id: Optional[str] = None
    duration: Optional[str] = None
    category_id: Optional[str] = None

    # ----------------------------------------------------------------
    def __post_init__(self):
        """Ensure platform is set correctly."""
        self.platform = "youtube"

    # ----------------------------------------------------------------

##################################################################
