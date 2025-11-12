"""
placeholder_enum.py
===================

Enumeration of all supported placeholder tokens used in prompt templates.
Centralizes placeholder definitions for validation, autocomplete, and
cross-platform consistency.
"""

from enum import Enum

class PlaceholderEnum(str, Enum):
    """
    String-based enumeration of placeholder names used in system and user prompts.
    Provides a single source of truth for placeholder validation and reference.
    """
    CLASSIFICATIONS = "CLASSIFICATIONS"
    OUTPUTFORMAT = "OUTPUTFORMAT"
    VIDEOTITLE = "VIDEOTITLE"
    VIDEOCONTEXT = "VIDEOCONTEXT"
    TARGETCOMMENT = "TARGETCOMMENT"
    THREADCOMMENTS = "THREADCOMMENTS"
    TAGGEDCOMMENTS = "TAGGEDCOMMENTS"
    LANG = "LANG"

    def __str__(self) -> str:
        return self.value
