"""
platform_enum.py
===========

Defines the enumeration of supported platforms for prompt templates
and LLM-driven workflows in the application.

Usage:
    from enums.platform_enum import Platform

    platform = PlatformEnum.YOUTUBE
"""

from typing import List
from enum import Enum

class PlatformEnum(str,Enum):
    """
    Enumeration of supported content platforms for prompt templates and analysis.

    This enum provides a controlled set of string values representing
    platforms such as YouTube, Twitter, Reddit, etc. Using this enum prevents
    typos, enables code completion, and centralizes valid platform names.

    Members:
        YOUTUBE: Represents the YouTube platform.
        TWITTER: Represents the Twitter platform.
        REDDIT:  Represents the Reddit platform.
        # Add additional platforms as needed.

    Example:
        >>> from enums.platform import Platform
        >>> Platform.YOUTUBE
        <Platform.YOUTUBE: 'youtube'>
        >>> str(Platform.YOUTUBE)
        'youtube'
    """

    YOUTUBE = "youtube"
    TWITTER = "twitter"
    REDDIT = "reddit"
    # Add more platforms as needed

    @classmethod
    def from_str(cls, value: str) -> "PlatformEnum":
        """Convert a string to a Platform enum (case-insensitive)."""
        if not value:
            raise ValueError("Platform cannot be empty")
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f"Unknown platform: {value}")


    @classmethod
    def to_list(cls) -> List[str]:
        """Return all platform string values (for UI dropdowns, etc.)."""
        return [p.value for p in cls]

    def __str__(self) -> str:
        return self.value
