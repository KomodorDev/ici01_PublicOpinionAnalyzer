import threading
from typing import List, Optional, Tuple

from services import (
    ContentService,
    PromptTemplateService,
    ClassificationService,
    VideoAnalysisService,
    ModelService,
    ContentAnalysisManager,
    AnalysisService
)

from enums import SortByEnum, SortDirEnum, PlatformEnum, TaskStatusEnum

from mappers import AnalysisMapper

from models.domain import LLMModelInfo, ContentAnalysis, ModelRunProgress
from models.view_models.analysis import (
    AnalysisViewModel,
    LLMModelInfoViewModel,
    ContentItemDetailViewModel,
    ContentItemListViewModel,
    ContentAnalysisRunViewModel,
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
        analysis_service: Optional[AnalysisService] = None,
        analysis_mapper: Optional[AnalysisMapper] = None,
    ):
        # Core dependencies
        self.content_service = content_service or ContentService()

        self.content_analysis_manager = (
            content_analysis_manager or ContentAnalysisManager()
        )

        # Prompt templates (dropdowns, etc.)
        self.prompt_template_service = (
            prompt_template_service or PromptTemplateService()
        )

        # Classification groups (dropdowns, etc.)
        self.classification_service = classification_service or ClassificationService()

        # Video-capable model registry / analysis support
        self.video_analysis_service = video_analysis_service or VideoAnalysisService()

        self.model_service = model_service or ModelService()

        self.analysis_service = analysis_service or AnalysisService()

        # Mapping helpers
        self.analysis_mapper = analysis_mapper or AnalysisMapper()

        self.analysis_view = AnalysisView(self)

        self._analysis_thread = None

    # ================================================================
    # Initial / full view render
    # ================================================================
    def render_analysis_view(self):
        """
        Build initial analysisViewModel for the current controller state.
        """

        # 5) Build available LLM model viewmodels for dropdown
        llm_models: List[LLMModelInfo] = self.model_service.list_all_llm_models()
        available_llm_models: List[LLMModelInfoViewModel] = [
            self.analysis_mapper.llm_model_info_to_llm_model_info_view_model(m)
            for m in llm_models
        ]

        vm = AnalysisViewModel(
            contents=None,
            selected=None,
            available_llm_models=available_llm_models,
            analysis_runs=None,
            info_message=None,
            error_message=None,
        )
        self.analysis_view.render_analysis_view(view_model=vm)

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
            [
                self.analysis_mapper.content_analysis_to_content_list_view_model(ca)
                for ca in analyses
            ]
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
            self.analysis_mapper.llm_model_info_to_llm_model_info_view_model(m)
            for m in llm_models
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
            [
                self.analysis_mapper.content_analysis_to_content_list_view_model(ca)
                for ca in analyses
            ]
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
            self.analysis_mapper.llm_model_info_to_llm_model_info_view_model(m)
            for m in llm_models
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
        llm_clients = []
        for provider, model_name in selected_models:
            client = self.model_service.get_llm_client(
                provider=provider,
                model_name=model_name,
            )
            llm_clients.append(client)

        # 2) For every content item, attach clients and create ModelRunProgress entries
        analyses: List[ContentAnalysis] = self.content_analysis_manager.all()
        if not analyses:
            return


        for ca in analyses:
            # Attach the list of LLM clients (copy so they don't alias)
            ca.models = llm_clients[:]

            # How many comments this content will be analyzed with
            total = len(ca.comments)

            # Fresh per-model progress list for THIS content item
            ca.model_run_progress = []
            for provider, model_name in selected_models:
                ca.model_run_progress.append(
                    ModelRunProgress(
                        provider=provider,
                        model_name=model_name,
                        status=TaskStatusEnum.PENDING,
                        progress=0.0 if total > 0 else 1.0,
                        current_comment=0,
                        total_comments=total,
                    )
                )

        # Optional safety: don't start a second run while one is still running
        if self._analysis_thread is not None and self._analysis_thread.is_alive():
            return

        # 3) Start background thread so we don't block the UI
        thread = threading.Thread(
            target=self._run_analysis_background,
            args=(analyses,),
            daemon=True,
        )
        self._analysis_thread = thread
        thread.start()

    # ---------------------------------------------------------
    def _run_analysis_background(self, analyses: List[ContentAnalysis]) -> None:
        """
        Background worker: run the analysis and update per-model status on error.
        """
        try:
            self.analysis_service.run_analysis(analyses)
        except Exception as exc:
            # If the whole run crashes, mark all model runs as ERROR so UI can show something useful.
            msg = f"Analysis failed: {exc!r}"
            for ca in analyses:
                for mr in ca.model_run_progress:
                    mr.status = TaskStatusEnum.ERROR
                    mr.error = msg

        finally:
            # Allow new runs later
            self._analysis_thread = None

    # ---------------------------------------------------------
    def on_analysis_status_polled(self) -> AnalysisViewModel:
        """
        Called periodically by the view (e.g. via a Gradio Timer).

        1) Read latest progress from ContentAnalysis objects.
        2) Map to ContentAnalysisRunViewModel list.
        3) Return an AnalysisViewModel that has `analysis_runs` populated.
        Other fields can be None so the UI only refreshes the progress panel.
        """
        analyses: List[ContentAnalysis] = self.content_analysis_manager.all()
        if not analyses:
            # Nothing to report; just return an "empty" diff
            return AnalysisViewModel(
                contents=None,
                selected=None,
                available_llm_models=None,
                analysis_runs=None,
                info_message=None,
                error_message=None,
            )

        # Map each ContentAnalysis → ContentAnalysisRunViewModel
        analysis_runs: List[ContentAnalysisRunViewModel] = [
            self.analysis_mapper.content_analysis_to_content_analysis_run_view_model(ca)
            for ca in analyses
        ]

        # Optionally, if you want to hide the panel when no runs exist:
        analysis_runs_or_none: Optional[List[ContentAnalysisRunViewModel]] = (
            analysis_runs if analysis_runs else None
        )

        return AnalysisViewModel(
            contents=None,  # do not touch the left list
            selected=None,  # do not change selection
            available_llm_models=None,  # leave dropdown unchanged
            analysis_runs=analysis_runs_or_none,
            info_message=None,
            error_message=None,
        )

    # ================================================================
    # Helpers
    # ================================================================
    # ---------------------------------------------------------
    def _extract_urls(self, raw_text: str) -> list[str]:
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
            self.prompt_template_service.list_all_prompt_template_names(ContentAnalysis.platform)
        )
        available_classification_groups = (
            self.classification_service.list_classification_group_names()
        )

        # Suppose your registry returns domain model info objects
        # that you then map to LLMModelInfoViewModel.
        summary_model_infos = self.video_analysis_service.list_available_video_models()
        available_summary_models = [
            self.analysis_mapper.llm_model_info_to_llm_model_info_view_model(m)
            for m in summary_model_infos
        ]

        return self.analysis_mapper.content_analysis_to_content_detail_view_model(
            ca,
            available_prompt_templates=available_prompt_templates,
            available_classification_groups=available_classification_groups,
            available_summary_models=available_summary_models,
        )

    # ---------------------------------------------------------
