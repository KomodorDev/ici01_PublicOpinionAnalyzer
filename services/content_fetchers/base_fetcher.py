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
        pass

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
        pass

##################################################################
