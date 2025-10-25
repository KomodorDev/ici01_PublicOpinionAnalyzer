# services/content_service.py
"""
content_service.py
==================

High-level service for fetching content from any supported platform.
"""

from typing import List
from services.content_fetchers.base_fetcher import ContentFetcher
from services.content_fetchers.youtube_fetcher import YouTubeFetcher
from services.content_fetchers.tiktok_fetcher import TikTokFetcher
from models.content_models import ContentAnalysis


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
            TikTokFetcher(),
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

    # ----------------------------------------------------------------
    
##################################################################
