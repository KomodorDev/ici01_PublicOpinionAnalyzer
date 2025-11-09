# services/video_analysis/__init__.py
"""Video analysis adapters."""
from .base_adapter import VideoAnalysisAdapter
from .google_adapter import GoogleAdapter

__all__ = [
    "VideoAnalysisAdapter",
    "GoogleAdapter",
]
