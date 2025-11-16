# mappers/analysis_mapper.py

from __future__ import annotations

from typing import List

from enums import SortByEnum, SortDirEnum

from models.domain import (
    ContentAnalysis,
    LLMModelInfo,
    VideoModelInfo,
    ModelRunProgress,
)
from models.view_models.analysis import (
    ContentItemListViewModel,
    ContentItemDetailViewModel,
    LLMModelInfoViewModel,
    VideoModelInfoViewModel,
    ModelRunProgressViewModel,
    ContentAnalysisRunViewModel,
)


class AnalysisMapper:
    """
    Pure mapping helpers for AnalysisController.

    These methods:
    - take domain objects + already-fetched choice lists
    - output view models
    - do NOT call services themselves
    """

    # ================================================================
    # Mapping helpers
    # ================================================================
    # ---------------------------------------------------------
    def content_analysis_to_content_list_view_model(
        self,
        ca: ContentAnalysis,
    ) -> ContentItemListViewModel:
        """
        Map a ContentAnalysis domain object to the left-list view model.
        """
        content = ca.content

        # Decide which comment_count to show:
        # - Prefer the platform's total comment_count, if present
        # - Otherwise, if we've already loaded comments into this ContentAnalysis,
        #   show the number of loaded comments as a fallback.
        if content.comment_count is not None:
            comment_count = content.comment_count
        elif ca.comments:
            comment_count = len(ca.comments)
        else:
            comment_count = None

        return ContentItemListViewModel(
            platform=content.platform,
            content_id=content.content_id,
            url=content.url,
            title=content.title,
            author=content.author,
            comment_count=comment_count,
        )

    # ---------------------------------------------------------
    def content_analysis_to_content_detail_view_model(
        self,
        ca: ContentAnalysis,
        *,
        available_prompt_templates: List[str],
        available_classification_groups: List[str],
        available_summary_models: List[LLMModelInfoViewModel],
    ) -> ContentItemDetailViewModel:
        """
        Map a ContentAnalysis + ContentItem domain object into the detail view model.
        """
        content = ca.content

        # -----------------------------
        # Summary defaults
        # -----------------------------
        summary_text = content.summary or ""
        summary_status = "idle"  # Hard-coded until you actually wire summary generation
        summary_source = content.summary_source  # "manual" | "ai" | None

        # -----------------------------
        # Selected template/group names
        # -----------------------------
        selected_template_name = ca.prompt_template.name if ca.prompt_template else None
        selected_group_name = (
            ca.classification_group.name if ca.classification_group else None
        )

        # -----------------------------
        # Comment count decision
        # -----------------------------
        if content.comment_count is not None:
            comment_count = content.comment_count
        elif ca.comments:
            comment_count = len(ca.comments)
        else:
            comment_count = None

        # -----------------------------
        # Build the viewmodel
        # -----------------------------
        return ContentItemDetailViewModel(
            # Identity
            platform=content.platform,
            content_id=content.content_id,
            url=content.url,
            # Metadata
            title=content.title,
            author=content.author,
            description=content.description,
            view_count=content.view_count,
            like_count=content.like_count,
            comment_count=comment_count,
            # Summary
            summary_text=summary_text,
            summary_status=summary_status,
            summary_source=summary_source,
            # Analysis config
            sort_by=ca.sort_by,
            sort_dir=ca.sort_dir,
            limit=ca.limit,
            selected_prompt_template_name=selected_template_name,
            selected_classification_group_name=selected_group_name,
            # Dropdown choice data
            available_prompt_templates=available_prompt_templates,
            available_classification_groups=available_classification_groups,
            available_sort_by_options=list(SortByEnum),
            available_sort_dir_options=list(SortDirEnum),
            available_summary_models=available_summary_models,
        )

    # ---------------------------------------------------------
    def video_model_info_to_video_model_info_view_model(
        self,
        m: VideoModelInfo,
    ) -> VideoModelInfoViewModel:
        """
        Convert a domain VideoModelInfo into a UI-friendly VideoModelInfoViewModel.
        """
        return VideoModelInfoViewModel(
            provider=m.provider,
            model_name=m.name,
            label=m.display_name or m.name,
            is_favorite=m.favorite,
            is_local=m.is_local,
        )

    # ---------------------------------------------------------
    def llm_model_info_to_llm_model_info_view_model(
        self,
        model: LLMModelInfo,
    ) -> LLMModelInfoViewModel:
        """
        Convert a domain LLMModelInfo into a UI-friendly LLMModelInfoViewModel.
        """
        return LLMModelInfoViewModel(
            provider=model.provider,
            model_name=model.name,
            label=model.display_name or model.name,
            is_favorite=model.favorite,
            is_local=model.is_local,
        )

    # ---------------------------------------------------------
    def model_run_progress_to_model_run_progress_view_model(
        self,
        p: ModelRunProgress,
    ) -> ModelRunProgressViewModel:
        """
        Map a domain ModelRunProgress object into a UI-friendly ModelRunProgressViewModel.
        """
        # Human-readable label (you can later replace this with a registry lookup)
        label = f"{p.provider.capitalize()} - {p.model_name}"

        vm = ModelRunProgressViewModel()
        vm.provider = p.provider
        vm.model_name = p.model_name
        vm.label = label

        vm.status = p.status
        vm.progress = p.progress
        vm.current_comment = p.current_comment
        vm.total_comments = p.total_comments
        vm.error = p.error

        return vm

    # ---------------------------------------------------------
    def content_analysis_to_content_analysis_run_view_model(
        self,
        ca: ContentAnalysis,
    ) -> ContentAnalysisRunViewModel:
        """
        Map a ContentAnalysis domain object to a ContentAnalysisRunViewModel
        used for the run/progress panel.
        """

        # Map per-model progress entries
        if ca.model_run_progress:
            model_runs: List[ModelRunProgressViewModel] = [
                self.model_run_progress_to_model_run_progress_view_model(p)
                for p in ca.model_run_progress
            ]
        else:
            model_runs = []

        return ContentAnalysisRunViewModel(
            # Identity / display
            platform=ca.content.platform,
            content_id=ca.content.content_id,
            url=ca.content.url,
            title=ca.content.title,
            author=ca.content.author,
            # Step 1: Fetching comments
            fetch_status=ca.fetch_status,
            fetch_progress=ca.fetch_progress,
            fetch_status_text=ca.fetch_status_text or "",
            # Per-model progress
            model_runs=model_runs,
            export_status=ca.export_status,
        )
