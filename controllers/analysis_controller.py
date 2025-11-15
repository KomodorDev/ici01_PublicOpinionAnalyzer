from typing import List, Optional, Tuple

from services import (
    ContentService,
    PromptTemplateService,
    ClassificationService,
    VideoAnalysisService,
    ModelService,
    ContentAnalysisManager,
)

from enums import SortByEnum, SortDirEnum, PlatformEnum

from models.domain import LLMModelInfo, ContentAnalysis, VideoModelInfo
from models.view_models.analysis import (
    AnalysisViewModel,
    LLMModelInfoViewModel,
    ContentItemDetailViewModel,
    ContentItemListViewModel,
    VideoModelInfoViewModel,
)

from views import AnalysisView


class AnalysisController:
    """
    All per-content operations identify a ContentAnalysis by (platform, content_id).
    """

# ---------------------------------------------------------
def __init__(
    self,
    content_service: Optional[ContentService] = None,
    content_analysis_manager: Optional[ContentAnalysisManager] = None,
    prompt_template_service: Optional[PromptTemplateService] = None,
    classification_service: Optional[ClassificationService] = None,
    video_analysis_service: Optional[VideoAnalysisService] = None,
    model_service: Optional[ModelService] = None,
):
    # Core dependencies
    self.content_service = content_service or ContentService()

    self.content_analysis_manager = content_analysis_manager or ContentAnalysisManager()

    # Prompt templates (dropdowns, etc.)
    self.prompt_template_service = prompt_template_service or PromptTemplateService()

    # Classification groups (dropdowns, etc.)
    self.classification_service = classification_service or ClassificationService()

    # Video-capable model registry / analysis support
    self.video_analysis_service = video_analysis_service or VideoAnalysisService()

    self.model_service = model_service or ModelService()

    self.analysis_view = AnalysisView(self)

    # ================================================================
    # Initial / full view render
    # ================================================================
    def render_analysis_view(self) -> AnalysisViewModel:
        """
        Build initial nalysisViewModel for the current controller state.
        """

        # 5) Build available LLM model viewmodels for dropdown
        llm_models: List[LLMModelInfo] = self.model_service.list_all_llm_models()
        available_llm_models: List[LLMModelInfoViewModel] = [
            self._llm_model_info_to_llm_model_info_view_model(m) for m in llm_models
        ]

        vm =AnalysisViewModel(
            contents=None,
            selected=None,
            available_llm_models=available_llm_models,
            analysis_runs=None,
            info_message=None,
            error_message=None,
        )
        self.analysis_view.render_analysis_view(controller=self, view_model=vm)


    # ================================================================
    # Callbacks wired by the view
    # ================================================================
    # ---------------------------------------------------------
    # Parsing
    def on_parse_links_clicked(self, raw_text: str) -> AnalysisViewModel:
        """
        Parse pasted links and create/update ContentAnalysis objects.
        Returns a full AnalysisViewModel for the view to redraw
        left-list, detail panel, and clear analysis_runs.
        """
        # 1) Normalize raw text → list of unique, non-empty URLs
        urls = self._extract_urls(raw_text)
        errors: list[str] = []

        # 2) For each URL, fetch metadata and store via manager
        for url in urls:
            try:
                content_analysis = self.content_service.fetch_metadata(url)
                self.content_analysis_manager.add_or_update(content_analysis)
            except Exception as exc:
                errors.append(f"Failed to fetch metadata for {url}: {exc!r}")

        # 3) Get updated ContentAnalysis objects
        analyses: List[ContentAnalysis] = self.content_analysis_manager.all()

        # 4) Select default ContentAnalysis (first, if any)
        selected_analysis: Optional[ContentAnalysis] = analyses[0] if analyses else None

        # 5) Build left-side list view models
        contents_vm: Optional[List[ContentItemListViewModel]] = (
            [self._content_analysis_to_content_list_view_model(ca) for ca in analyses]
            if analyses
            else None
        )

        # 6) Build right-side detail view model
        selected_vm: Optional[ContentItemDetailViewModel] = (
            self._build_content_detail_view_model(selected_analysis)
            if selected_analysis is not None
            else None
        )

        # 7) Build available LLM model viewmodels for dropdown
        llm_models: List[LLMModelInfo] = self.model_service.list_all_llm_models()
        available_llm_models: List[LLMModelInfoViewModel] = [
            self._llm_model_info_to_llm_info_view_model(m) for m in llm_models
        ]

        # 8) Prepare messages (inline, no extra helper)
        error_message: Optional[str] = "\n".join(errors) if errors else None

        if urls and not errors:
            info_message: Optional[str] = f"Parsed {len(urls)} link(s)."
        elif urls and errors:
            ok_count = len(urls) - len(errors)
            info_message = f"Parsed {ok_count} of {len(urls)} link(s)."
        else:
            info_message = "No links found." if not raw_text.strip() else None

        # 9) Build AnalysisViewModel directly.
        #    analysis_runs is cleared (None = hide panel).
        return AnalysisViewModel(
            contents=contents_vm,
            selected=selected_vm,
            available_llm_models=available_llm_models,
            analysis_runs=None,
            info_message=info_message,
            error_message=error_message,
        )

    # ---------------------------------------------------------
    # Content list / selection
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    def on_content_clicked(
        self,
        platform: PlatformEnum,
        content_id: str,
    ) -> ContentItemDetailViewModel:
        """
        Load the selected ContentAnalysis for the right-side detail view.

        Returns:
            A ContentItemDetailViewModel representing the selected content item.
            The view uses this only to refresh the detail panel. The list selection
            is already tracked by the UI via the user's click.
        """

        # 1) Look up the corresponding ContentAnalysis from the manager.
        #    Adjust this call to your actual manager API.
        try:
            content_analysis: ContentAnalysis = self.content_analysis_manager.get(
                platform=platform,
                content_id=content_id,
            )
        except KeyError as exc:
            # If this ever happens, something is wrong with the UI → controller state sync.
            raise ValueError(
                f"No ContentAnalysis found for {platform=} {content_id=}"
            ) from exc

        # 2) Build and return the detail view model.
        #    This helper is the one that pulls prompt templates, classification groups,
        #    LLM summary models, etc., and maps everything into the VM.
        return self._build_content_detail_view_model(content_analysis)

    # ---------------------------------------------------------
    def on_remove_content_clicked(
        self,
        platform: PlatformEnum,
        content_id: str,
    ) -> AnalysisViewModel:
        """
        Remove a parsed ContentAnalysis from internal state and return
        updated page state (left list + selected item, and cleared analysis_runs).
        """
        error_message: Optional[str] = None
        info_message: Optional[str] = None

        # 1) Remove the corresponding ContentAnalysis
        removed = False
        try:
            self.content_analysis_manager.remove(
                platform=platform,
                content_id=content_id,
            )
            removed = True
        except KeyError:
            # Item wasn't found; we still continue and just rebuild the view.
            error_message = f"Content item not found for platform={platform} content_id={content_id}."

        if removed:
            info_message = "Removed selected content item."

        # 2) Get updated list of analyses
        analyses: List[ContentAnalysis] = self.content_analysis_manager.all()

        # 3) Choose a new selected analysis (first one if any remain)
        selected_analysis: Optional[ContentAnalysis] = analyses[0] if analyses else None

        # 4) Left-side list view models
        contents_vm: Optional[List[ContentItemListViewModel]] = (
            [self._content_analysis_to_content_list_view_model(ca) for ca in analyses]
            if analyses
            else None
        )

        # 5) Right-side detail panel view model
        selected_vm: Optional[ContentItemDetailViewModel] = (
            self._build_content_detail_view_model(selected_analysis)
            if selected_analysis is not None
            else None
        )

        # 6) Available LLM models for dropdown
        llm_models: List[LLMModelInfo] = self.model_service.list_all_llm_models()
        available_llm_models: List[LLMModelInfoViewModel] = [
            self._llm_model_info_to_llm_info_view_model(m) for m in llm_models
        ]

        # 7) Return full updated page state; analysis_runs cleared
        return AnalysisViewModel(
            contents=contents_vm,
            selected=selected_vm,
            available_llm_models=available_llm_models,
            analysis_runs=None,
            info_message=info_message,
            error_message=error_message,
        )

    # ---------------------------------------------------------
    # Summary (AI + manual)
    # ---------------------------------------------------------
    def on_generate_summary_clicked(
        self,
        platform: PlatformEnum,
        content_id: str,
        provider: str,
        model_name: str,
    ) -> str:
        """
        Generate a summary for the given content item using the selected provider/model.

        Side effects:
            - Calls backend synchronously.
            - Saves the AI summary on the ContentAnalysis/ContentItem.
            - Updates internal fields (summary_source='ai').

        Returns:
            The current saved summary text (textbox should display this).
        """
        # 1) Look up the ContentAnalysis for this content
        try:
            ca: ContentAnalysis = self.content_analysis_manager.get(
                platform=platform,
                content_id=content_id,
            )
        except KeyError as exc:
            raise ValueError(
                f"No ContentAnalysis found for platform={platform} content_id={content_id}"
            ) from exc

        video_url = ca.url  # convenience property → ca.content.url

        # 2) Call the video analysis service to generate a summary
        #    We pass model_name as the model_id expected by summarize()
        try:
            summary_text: str = self.video_analysis_service.summarize(
                video_url=video_url,
                provider=provider,
                model_id=model_name,
                # custom_prompt=None,      # hook for later if you add a custom prompt textbox
                # max_tokens=None,         # hook for later if you want to cap length
            )
        except Exception as exc:
            # You can choose to surface the error differently if you want
            raise RuntimeError(
                f"Failed to generate summary for {platform=} {content_id=}: {exc!r}"
            ) from exc

        # 3) Persist summary into the domain model
        ca.content.summary = summary_text
        ca.content.summary_source = "ai"

        # If your manager requires explicit saving, do it here, e.g.:
        # self.content_analysis_manager.update(ca)

        # 4) Return the updated summary text so the UI can show it
        return summary_text

    # ---------------------------------------------------------
    def on_summary_save_clicked(
        self,
        platform: PlatformEnum,
        content_id: str,
        new_text: str,
    ) -> None:
        """
        Save the manually edited summary text for the given content item.

        Side effects:
            - Persists new_text.
            - Updates summary_source='manual'.

        Returns:
            None. The view already holds the current text in the textbox.
        """
        # 1) Look up the ContentAnalysis for this content
        try:
            ca: ContentAnalysis = self.content_analysis_manager.get(
                platform=platform,
                content_id=content_id,
            )
        except KeyError as exc:
            raise ValueError(
                f"No ContentAnalysis found for platform={platform} content_id={content_id}"
            ) from exc

        # 2) Update the summary on the underlying ContentItem
        # You can decide whether to strip; here we store exactly what the user typed.
        ca.content.summary = new_text
        ca.content.summary_source = "manual"

    # --- Per-content settings ---
    # ---------------------------------------------------------
    def on_sort_changed(
        self,
        platform: PlatformEnum,
        content_id: str,
        sort_by: str,
        sort_dir: str,
    ) -> None:
        """Update the comment sorting configuration (e.g., RELEVANCE asc/dsc) for this content."""

        # 1) Get the ContentAnalysis (we assume it exists)
        ca: ContentAnalysis = self.content_analysis_manager.get(
            platform=platform,
            content_id=content_id,
        )

        # 2) Convert input strings → enums
        ca.sort_by = SortByEnum(sort_by)
        ca.sort_dir = SortDirEnum(sort_dir)

        # 3) Done. No return; view updates itself on next render.
        # If your manager has a persistence method, you could call:
        # self.content_analysis_manager.update(ca)

    # ---------------------------------------------------------
    def on_limit_changed(
        self,
        platform: PlatformEnum,
        content_id: str,
        limit: int,
    ) -> None:
        """Update how many comments to fetch/analyze for this content."""

        # 1) Retrieve the ContentAnalysis (guaranteed to exist)
        ca: ContentAnalysis = self.content_analysis_manager.get(
            platform=platform,
            content_id=content_id,
        )

        # 2) Update the limit
        ca.limit = limit

        # 3) Done.
        # If ContentAnalysisManager requires explicit persistence:
        # self.content_analysis_manager.update(ca)

    # ---------------------------------------------------------
    def on_prompt_template_changed(
        self,
        platform: PlatformEnum,
        content_id: str,
        template_name: str,
    ) -> None:
        """Update the selected prompt template for this content."""

        # 1) Retrieve the ContentAnalysis (guaranteed to exist)
        ca = self.content_analysis_manager.get(
            platform=platform,
            content_id=content_id,
        )

        # 2) Load the PromptTemplate using the correct service method
        prompt_template = self.prompt_template_service.load_prompt_template(
            platform=platform,
            name=template_name,
        )

        # 3) Assign to the domain model
        ca.prompt_template = prompt_template

        # 4) Done (no return value needed)

    # ---------------------------------------------------------
    def on_classification_group_changed(
        self,
        platform: PlatformEnum,
        content_id: str,
        group_id: str,
    ) -> None:
        """Update the selected classification group for this content."""

        # 1) Retrieve the ContentAnalysis (guaranteed to exist)
        ca = self.content_analysis_manager.get(
            platform=platform,
            content_id=content_id,
        )

        # 2) Load classification group via the service
        classification_group = self.classification_service.load_classification_group(
            platform=platform,
            name=group_id,
        )

        # 3) Assign to the domain model
        ca.classification_group = classification_group

        # 4) Done
        # If your manager needs explicit persistence:
        # self.content_analysis_manager.update(ca)

    # ================================================================
    # Run Analysis clicked
    # ================================================================
    # ---------------------------------------------------------
    def on_run_analysis_clicked(
        self,
        selected_models: List[Tuple[str, str]],
    ) -> None:
        """
        Attach the selected LLM models to all ContentAnalysis objects
        in preparation for running an analysis.

        Args:
            selected_models: List of (provider, model_name) tuples
                             e.g. [("openai", "gpt-4o-mini"),
                                   ("google", "gemini-1.5-flash")]
        """

        # 1) Resolve LLM clients for all selected models
        #    (Adjust this to your actual ModelService API)
        llm_clients = []
        for provider, model_name in selected_models:
            client = self.model_service.get_llm_client(
                provider=provider,
                model_name=model_name,
            )
            llm_clients.append(client)

        # 2) Attach the list of clients to every ContentAnalysis
        analyses: List[ContentAnalysis] = self.content_analysis_manager.all()
        for ca in analyses:
            ca.models = llm_clients[:]  # shallow copy so later changes don't alias

        # 3) (Later) you will trigger the actual analysis run somewhere else,
        #    using ca.models on each ContentAnalysis.

        # Call the analysis service with the fully prepared ContentAnalysis objects
        self.analysis_service.run_analysis(analyses)

    # ---------------------------------------------------------
    def on_analysis_status_polled(self) -> AnalysisViewModel:
        """
        Called periodically by the view (e.g. via a Gradio Timer).
        1) Ask backend for latest progress.
        2) Update internal run state (ContentAnalysisRunViewModel list).
        3) Return updated AnalysisViewModel (especially .analysis_runs).
        """

    # ================================================================
    # Helpers
    # ================================================================
    # ---------------------------------------------------------
    def _extract_urls(raw_text: str) -> list[str]:
        """
        Turn the pasted text into a cleaned, de-duplicated list of URLs.

        Very simple version:
          - split by line
          - strip whitespace
          - drop empty lines
          - de-duplicate while preserving order
        """
        if not raw_text:
            return []

        seen = set()
        result: list[str] = []

        for line in raw_text.splitlines():
            url = line.strip()
            if not url:
                continue
            if url in seen:
                continue
            seen.add(url)
            result.append(url)

        return result

    # ================================================================
    # Mapping helpers
    # ================================================================
    # ---------------------------------------------------------
    def _content_analysis_to_content_list_view_model(
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
    def _build_content_detail_view_model(
        self, ca: ContentAnalysis
    ) -> ContentItemDetailViewModel:
        """
        Fetch all needed dropdown/choice data from services and
        build a ContentItemDetailViewModel for the given ContentAnalysis.
        """

        # Adjust these service calls to your real APIs.
        available_prompt_templates = (
            self.prompt_template_service.list_all_template_names()
        )
        available_classification_groups = (
            self.classification_service.list_all_group_names()
        )

        # Suppose your registry returns domain model info objects
        # that you then map to LLMModelInfoViewModel.
        summary_model_infos = self.video_analysis_service.list_video_models()
        available_summary_models = [
            self._llm_model_info_to_llm_model_info_view_model(m)
            for m in summary_model_infos
        ]

        return self._content_analysis_to_content_detail_view_model(
            ca,
            available_prompt_templates=available_prompt_templates,
            available_classification_groups=available_classification_groups,
            available_summary_models=available_summary_models,
        )

    # ---------------------------------------------------------
    def _content_analysis_to_content_detail_view_model(
        ca: ContentAnalysis,
        *,
        available_prompt_templates: list[str],
        available_classification_groups: list[str],
        available_summary_models: list[LLMModelInfoViewModel],
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
    def _video_model_info_to_video_model_info_view_model(
        m: VideoModelInfo,
    ) -> VideoModelInfoViewModel:
        return VideoModelInfoViewModel(
            provider=m.provider,
            model_name=m.name,
            label=m.display_name or m.name,
            is_favorite=m.favorite,
            is_local=m.is_local,
        )

    # ---------------------------------------------------------
    def _llm_model_info_to_llm_model_info_view_model(
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
