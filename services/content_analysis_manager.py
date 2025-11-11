# manager.py
from services.content_service import ContentService
class ContentAnalysisManager:

    # ----------------------------------------------------------------
    def __init__(self):
        self.content_service = ContentService()
        self._analyses = []  # storing reference

    # ----------------------------------------------------------------
    def create_content_analyses_with_metadata(self, links: list[str]) -> None:
        """For each link, create a ContentAnalysis and fetch metadata."""
        for link in links:
            if not self._is_supported_link(link):
                continue
            self.create_content_analysis(link=link)
    # ----------------------------------------------------------------
    def create_content_analysis(self, link: str):
        """Create and store a ContentAnalysis object for the given link."""
        try:
            # Fetch metadata and create ContentAnalysis object in one step
            content_analysis = self.content_service.fetch_metadata(link)

            # Store the object
            self._analyses.append(content_analysis)

            return content_analysis
        except Exception as e:
            # Optionally log error or track failed creation
            print(f"Error creating ContentAnalysis for {link}: {e}")
            return None

    # ----------------------------------------------------------------
    def get_all(self):
        """Return all ContentAnalysis objects."""
        return self._analyses

    # ----------------------------------------------------------------
    def update(self, id, **kwargs):
        # Implementation for updating model/data
        ...

    # ----------------------------------------------------------------
    def _is_supported_link(self, link: str) -> bool: # Should be handled by content_service
        supported_domains = ['youtube.com', 'youtu.be']
        return any(domain in link for domain in supported_domains)

    # ----------------------------------------------------------------
