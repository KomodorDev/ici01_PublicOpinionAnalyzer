# services/content_service.py
"""
content_service.py
==================

High-level service for fetching content from any supported platform.
"""

from typing import List
from services.content_fetchers.base_fetcher import ContentFetcher
from services.content_fetchers.youtube_fetcher import YouTubeFetcher
from models.domain import Comment, ContentAnalysis


##################################################################
class ContentService:
    """
    Orchestrates content fetching across multiple platforms.
    
    Automatically routes requests to the appropriate platform fetcher.
    """

    # ----------------------------------------------------------------
    def __init__(self):
        # Register all available fetchers
        self.fetchers: List[ContentFetcher] = [
            YouTubeFetcher(),
            # Add more fetchers here as you build them
        ]

    # ----------------------------------------------------------------
    def fetch_content(self, url: str) -> ContentAnalysis:
        """
        Fetch content from any supported platform.
        
        Args:
            url: URL of the content to fetch.
            
        Returns:
            ContentAnalysis object with content and comments.
            
        Raises:
            ValueError: If platform is not supported or URL is invalid.
        """
        # Find the appropriate fetcher
        for fetcher in self.fetchers:
            if fetcher.can_handle(url):
                return fetcher.fetch_content(url)

        # No fetcher found
        raise ValueError(f"Unsupported platform or invalid URL: {url}")

    # ----------------------------------------------------------------
    def fetch_metadata(self, url: str) -> ContentAnalysis:
        """
        Fetch metadata for content from any supported platform.

        Args:
            url: URL of the content whose metadata to fetch.

        Returns:
            ContentAnalysis object with metadata filled and comments list empty.
        """
        # Find the appropriate fetcher
        for fetcher in self.fetchers:
            if fetcher.can_handle(url):
                return fetcher.fetch_metadata(url)

        # No fetcher found
        raise ValueError(f"Unsupported platform or invalid URL: {url}")


    # ----------------------------------------------------------------
    def fetch_comments(self, analysis: ContentAnalysis) -> list[Comment]:
        """
        Fetch comments for the given content and update its progress fields.

        Args:
            analysis: ContentAnalysis object whose content.url will be used
                    and whose fetch_* fields will be updated.

        Returns:
            List of Comment objects associated with the content.
        """
        url = analysis.url  # convenience property on ContentAnalysis

        # Find the appropriate fetcher
        for fetcher in self.fetchers:
            if fetcher.can_handle(url):
                # Let the fetcher mutate analysis directly
                return fetcher.fetch_comments(analysis)

        # No fetcher found
        raise ValueError(f"Unsupported platform or invalid URL: {url}")



    # ----------------------------------------------------------------
    def fetch_multiple(self, urls: List[str]) -> List[ContentAnalysis]:
        """
        Fetch content from multiple URLs.
        
        Args:
            urls: List of content URLs.
            
        Returns:
            List of ContentAnalysis objects.
        """
        results = []
        for url in urls:
            try:
                content = self.fetch_content(url)
                results.append(content)
            except ValueError as e:
                print(f"Error fetching {url}: {e}")
        return results
