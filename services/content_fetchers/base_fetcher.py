# services/content_fetchers/base_fetcher.py
"""
base_fetcher.py
===============

Abstract base class for platform-specific content fetchers.
"""

from abc import ABC, abstractmethod
from models.content_models import ContentAnalysis


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
    def fetch_comments(self, url: str):
        """
        Fetch only the comments for the given content URL from the platform.

        Args:
            url: The content URL whose comments to fetch.

        Returns:
            List of Comment objects associated with the content.

        Raises:
            ValueError: If URL is invalid or comments not found.
        """
##################################################################
