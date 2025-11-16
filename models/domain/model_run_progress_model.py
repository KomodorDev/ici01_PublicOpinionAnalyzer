# models/domain/model_run_progress_model.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from enums import TaskStatusEnum


@dataclass
class ModelRunProgress:
    """
    Per-model analysis progress for a single content item.

    One instance = one (provider, model_name) run on this video.
    """

    provider: str              # "openai", "google", ...
    model_name: str            # "gpt-4o-mini", "gemini-1.5-flash", ...

    status: TaskStatusEnum = TaskStatusEnum.PENDING   # PENDING | RUNNING | DONE | ERROR
    progress: float = 0.0                              # 0.0–1.0

    current_comment: int = 0                           # how many comments processed
    total_comments: int = 0                            # how many to process in total

    error: Optional[str] = None                        # error message for this model
