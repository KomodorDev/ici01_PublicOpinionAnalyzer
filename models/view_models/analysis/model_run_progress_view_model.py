from __future__ import annotations
from dataclasses import dataclass
from enums.provider_enum import ProviderEnum
from enums.model_run_status_enum import ModelRunStatusEnum


@dataclass
class ModelRunProgressViewModel:
    """
    Progress info for a single (provider, model) on one content item.
    """

    provider: ProviderEnum
    model_name: str      # internal name, e.g. "gpt-4o-mini"
    label: str           # UI label: e.g. "OpenAI — GPT-4o-mini"

    processed_comments: int
    total_comments: int

    status: ModelRunStatusEnum  # PENDING/RUNNING/DONE/ERROR
