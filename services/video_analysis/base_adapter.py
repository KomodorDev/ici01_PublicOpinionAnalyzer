# services/video_analysis/base_adapter.py
"""
base_adapter.py
===============

Abstract base class for video analysis adapters.
"""
from abc import ABC, abstractmethod
from typing import Optional


##################################################################
class VideoAnalysisAdapter(ABC):
    """Base class for video analysis provider adapters."""

    # ----------------------------------------------------------------
    @abstractmethod
    def summarize(
        self,
        video_url: str,
        model_id: str,
        custom_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Summarize a YouTube video.
        
        Args:
            video_url: YouTube video URL
            model_id: Model identifier to use for analysis
            custom_prompt: Optional custom prompt for summarization
            max_tokens: Maximum tokens in response (None = provider default)
            
        Returns:
            Video summary as text
        """

    # ----------------------------------------------------------------
    @abstractmethod
    def analyze(
        self,
        video_url: str,
        model_id: str,
        custom_prompt: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Analyze video with custom prompt.
        
        Args:
            video_url: YouTube video URL
            model_id: Model identifier to use for analysis
            custom_prompt: Custom analysis prompt
            max_tokens: Maximum tokens in response (None = provider default)
            
        Returns:
            Analysis result as text
        """

    # ----------------------------------------------------------------
    @abstractmethod
    def supports_native_video(self) -> bool:
        """
        Check if this adapter supports native video analysis.

        Returns:
            True if native video support, False if requires preprocessing
        """

    # ----------------------------------------------------------------

##################################################################
