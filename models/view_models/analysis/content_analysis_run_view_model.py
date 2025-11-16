from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from enums import PlatformEnum, TaskStatusEnum
from models.view_models.analysis.model_run_progress_view_model import ModelRunProgressViewModel


@dataclass
class ContentAnalysisRunViewModel:
    """
    One 'status box' for a single content item during analysis.

    This is a pure projection of ContentAnalysis + per-model run state,
    used only for the run/progress panel.
    """

    # Identity / display
    platform: PlatformEnum
    content_id: str
    url: str
    title: str
    author: str

    # -----------------------------
    # Step 1: Fetching comments
    # -----------------------------
    fetch_status: TaskStatusEnum              # PENDING | RUNNING | DONE | ERROR
    fetch_progress: float                     # 0.0–1.0
    fetch_status_text: str                    # last status line (yt-dlp, etc.)

    # -----------------------------
    # Per-model progress
    # -----------------------------
    model_runs: List[ModelRunProgressViewModel] = None

    # -----------------------------
    # Exporting results
    # -----------------------------
    export_status: TaskStatusEnum = TaskStatusEnum.PENDING
