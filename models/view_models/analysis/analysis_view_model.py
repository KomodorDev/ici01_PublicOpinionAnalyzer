# models/view_models/analysis/analysis_view_model.py

from dataclasses import dataclass
from typing import List, Optional

from models.view_models.analysis.content_item_list_view_model import ContentItemListViewModel
from models.view_models.analysis.content_item_detail_view_model import ContentItemDetailViewModel
from models.view_models.analysis.llm_model_info_view_model import LLMModelInfoViewModel
from models.view_models.analysis.content_analysis_run_view_model import ContentAnalysisRunViewModel


@dataclass
class AnalysisViewModel:
    """
    Full state for the Analysis view.
    """

    # Left-side list
    contents: Optional[List[ContentItemListViewModel]] = None

    # Right-side detail panel
    selected: Optional[ContentItemDetailViewModel] = None

    # ------------------------------
    # Global analysis model selection
    # ------------------------------

    # All selectable LLMs (domain → viewmodel)
    available_llm_models: Optional[List[LLMModelInfoViewModel]] = None

    # NEW: status boxes for the currently running or last run analysis.
    # None = no analysis panel visible.
    analysis_runs: Optional[List[ContentAnalysisRunViewModel]] = None

    # ------------------------------
    # Page-level messages
    # ------------------------------
    info_message: Optional[str] = None
    error_message: Optional[str] = None
