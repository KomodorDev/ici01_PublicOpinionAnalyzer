# services/content_fetchers/base_fetcher.py
"""
base_fetcher.py
===============

Abstract base class for platform-specific content fetchers.
"""

from abc import ABC, abstractmethod
from models.domain import ContentAnalysis, Comment


##################################################################
class ContentFetcher(ABC):
    """
    Abstract base class for fetching content from social media platforms.
    
    All platform-specific fetchers must implement these methods.
    """

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Determine if this fetcher can handle the given URL.
        
        Args:
            url: The content URL to check.
            
        Returns:
            True if this fetcher supports the platform, False otherwise.
        """

    @abstractmethod
    def fetch_content(self, url: str) -> ContentAnalysis:
        """
        Fetch content metadata and comments from the platform.
        
        Args:
            url: The content URL to fetch.
            
        Returns:
            ContentAnalysis object containing content and comments.
            
        Raises:
            ValueError: If URL is invalid or content not found.
        """

    @abstractmethod
    def fetch_metadata(self, url: str):
        """
        Fetch only metadata (not comments) for the content from the platform.

        Args:
            url: The content URL to fetch.

        Returns:
            ContentItem object containing only basic metadata.

        Raises:
            ValueError: If URL is invalid or content not found.
        """

    @abstractmethod
    def fetch_comments(self, analysis: ContentAnalysis) -> list[Comment]:
        """
        Fetch comments for the given content and update progress fields on the
        provided ContentAnalysis object.

        Args:
            analysis: ContentAnalysis instance whose content.url determines
                    the fetch target, and whose fetch_* fields should be
                    updated during progress.

        Returns:
            List of Comment objects (also assigned to analysis.comments).

        Raises:
            Exception: Fetcher-specific errors (network issues, parsing issues, etc.).
        """

##################################################################
