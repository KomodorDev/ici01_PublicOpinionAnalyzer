"""
sort_dir_enum.py
================

Enum for sort direction (ascending / descending) used in analysis.
"""

from enum import Enum


class SortDirEnum(str, Enum):
    """
    Sorting direction for ordered comment lists.
    """

    ASC = "asc"
    DSC = "dsc"
