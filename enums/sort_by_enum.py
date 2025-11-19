"""
sort_by_enum.py
===============

Enum for comment sorting criteria used in analysis.

Currently minimal, but designed to be extended later
(e.g. TOP, NEWEST, OLDEST, etc.).
"""

from enum import Enum


class SortByEnum(str, Enum):
    """
    Sorting dimension for comments.

    Values are stored as lowercase strings to match backend/API expectations.
    """
    DEFAULT = "default"  # platform default sorting
    # RELEVANCE = "relevance"
    # FUTURE:
    # TOP = "top"
    # NEWEST = "newest"
    # OLDEST = "oldest"
    def __str__(self) -> str:
        return self.value