"""
platform_enum.py
===========

Defines the enumeration of supported platforms for prompt templates
and LLM-driven workflows in the application.

Usage:
    from enums.platform_enum import Platform

    platform = PlatformEnum.YOUTUBE
"""

from enum import Enum

class PlatformEnum(Enum):
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

    def __str__(self) -> str:
        """
        Return the string representation of the enum member.

        Returns:
            str: The value for this platform (e.g., 'youtube').
        """
        return self.value
