# models/tiktok_models.py
"""
tiktok_models.py
=================

TikTok-specific implementations of content models.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from models.content_models import ContentItem

##################################################################
@dataclass
class TikTokVideo(ContentItem):
    """TikTok-specific video metadata."""
    share_count: Optional[int] = None
    hashtags: List[str] = field(default_factory=list)
    
    # ----------------------------------------------------------------
    def __post_init__(self):
        self.platform = "tiktok"
    # ----------------------------------------------------------------

##################################################################
