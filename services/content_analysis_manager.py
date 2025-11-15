from typing import Dict, List, Optional
from enums.platform_enum import PlatformEnum
from models.domain.content_analysis_model import ContentAnalysis
from models.domain.comment_model import Comment


class ContentAnalysisManager:
    """
    Stores and retrieves ContentAnalysis objects by (platform, content_id).

    Acts as a simple in-memory repository.
    """

    def __init__(self):
        # key: (platform, content_id)
        self._items: Dict[tuple[str, str], ContentAnalysis] = {}

    # -----------------------------------------------------
    # Basic CRUD
    # -----------------------------------------------------

    def add_or_update(self, analysis: ContentAnalysis) -> None:
        """
        Insert or overwrite a ContentAnalysis entry.
        Keys identified by (platform, content_id).
        """
        key = (analysis.content.platform.value, analysis.content.content_id)
        self._items[key] = analysis

    def get(self, platform: PlatformEnum, content_id: str) -> Optional[ContentAnalysis]:
        """
        Retrieve a ContentAnalysis by (platform, content_id).
        Returns None if not found.
        """
        key = (platform.value, content_id)
        return self._items.get(key)

    def remove(self, platform: PlatformEnum, content_id: str) -> None:
        """
        Remove the ContentAnalysis entry if it exists.
        """
        key = (platform.value, content_id)
        self._items.pop(key, None)

    def all(self) -> List[ContentAnalysis]:
        """
        Return all stored ContentAnalysis objects as a list.
        """
        return list(self._items.values())

    def clear(self) -> None:
        """
        Remove all entries.
        Useful when parsing new links wipes previous runs.
        """
        self._items.clear()

    # -----------------------------------------------------
    # Comment operations
    # -----------------------------------------------------

    def append_comments(
        self,
        platform: PlatformEnum,
        content_id: str,
        comments: List[Comment],
    ) -> None:
        """
        Append comments to the ContentAnalysis.comments list.
        """
        ca = self.get(platform, content_id)
        if ca:
            ca.comments.extend(comments)

    def set_comments(
        self,
        platform: PlatformEnum,
        content_id: str,
        comments: List[Comment],
    ) -> None:
        """
        Replace the comments list entirely (e.g. after a fresh refetch).
        """
        ca = self.get(platform, content_id)
        if ca:
            ca.comments = comments
