from __future__ import annotations
from typing import Optional
from dataclasses import dataclass
from enums.provider_enum import ProviderEnum
from enums.task_status_enum import TaskStatusEnum


class ModelRunProgressViewModel:
    provider: ProviderEnum
    model_name: str
    label: str # e.g., "OpenAI - GPT-4", "Antrhopic - Claude 2"

    status: TaskStatusEnum        # PENDING | RUNNING | DONE | ERROR
    progress: float               # 0.0–1.0
    current_comment: int
    total_comments: int
    error: Optional[str] = None
