# models/view_models/analysis/content_analysis_run_view_model.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from enums.platform_enum import PlatformEnum
from models.view_models.analysis.model_run_progress_view_model import ModelRunProgressViewModel


@dataclass
class ContentAnalysisRunViewModel:
    """
    Represents one 'status box' for a single content item during analysis.
    """

    # Identity / display
    platform: PlatformEnum
    content_id: str
    url: str
    title: str

    # Fetch status text EXACTLY as returned by the backend (string only)
    fetch_status: str

    # Total number of comments for this content
    total_comments: int

    # Progress for each selected model
    model_runs: List[ModelRunProgressViewModel]
