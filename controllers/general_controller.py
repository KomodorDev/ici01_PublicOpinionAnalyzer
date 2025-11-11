# controllers/general_controller.py
"""
general_controller.py
================

Handles logic for the "General" tab.
"""

from typing import List, Tuple

from views.general_view import GeneralView
from services.general_service import GeneralService
from services.model_service import ModelService
from services.classification_service import ClassificationService
from services.prompt_runtime_service import PromptRuntimeService
from services.prompt_template_service import PromptTemplateService
from services.analysis_service import AnalysisService
from services.content_service import ContentService
from services.content_analysis_manager import ContentAnalysisManager


##################################################################
class GeneralController:
    """Handles logic and coordination for the General tab."""

    # ----------------------------------------------------------------
    def __init__(self):
        """
        Initialize GeneralController with all required services.

        Architecture:
        - View: GeneralView (UI rendering)
        - Services: Business logic and data access
        - Controller: Orchestrates interaction between View and Services
        """
        # View layer
        self.general_view = GeneralView()

        # Service layer - (Separation of Concerns)
        self.general_service = GeneralService()  # General operations
        self.model_service = ModelService()  # LLM model management
        self.classification_service = ClassificationService()  # Classification groups
        self.prompt_service = PromptRuntimeService()  # Prompt template management
        self.prompt_template_service = PromptTemplateService()  # Prompt template management
        self.content_service = ContentService()  # Content fetching service
        self.analysis_service = AnalysisService()  # Analysis orchestration

        # Import and initialize OutputFormatService

        # Initialize ContentAnalysisManager
        self.content_analysis_manager = ContentAnalysisManager()

    # ----------------------------------------------------------------
    def render_general_view(self):
        """Get data from service, pass it to view for display."""
        # Ask service for data then give it to view:
        # - Available Models (from ModelService)
        # - Available Label Groups (from GeneralService, if implemented)
        # - Available Prompt Styles (from PromptService)

        # Fetch available models and pass them to the view. ModelService
        # returns a list of ModelInfo objects; the view will extract
        # display names/ids as needed.
        models = self.model_service.list_all_llm_models()

        # Load classification groups and extract names for the view
        try:
            groups = self.classification_service.load_all_classification_groups()
            group_names = [g.name for g in groups]
        except (FileNotFoundError, RuntimeError, OSError):
            group_names = []

        # Load available prompt styles for YouTube platform
        try:
            prompt_styles_data = self.prompt_template_service.list_all_prompt_template_names(
                platform="youtube"
            )
            # Extract template names from the data
            prompt_style_names = [
                ps["name"] for ps in prompt_styles_data if "name" in ps
            ]
        except (FileNotFoundError, RuntimeError, OSError):
            prompt_style_names = ["default"]

        self.general_view.render_general_view(
            controller=self,
            models=models,
            groups=group_names,
            prompt_styles=prompt_style_names,
        )

    # ----------------------------------------------------------------
    def create_content_analyses_from_links(self, links: list[str]) -> None:
        """Given a list of links, creates ContentAnalysis objects and fetches their metadata."""
        for link in links:
            # Validate link (optional, e.g., check for supported domains)
            # if not self._is_supported_link(link):
            #    continue

            # Create a ContentAnalysis entry (could include setting status to 'pending' initially)
            self.content_analysis_manager.create_content_analysis(link=link)


    # ----------------------------------------------------------------
    def run_analysis(
        self,
        selected_video_urls: List[str],
        selected_models: List[Tuple[str, str]],  # (provider, model_name) pairs from UI
    ):
        """
        Prepares and executes analysis on the selected set of videos.

        For each selected video URL:
        - Fetches the associated ContentAnalysis object from the manager.
        - Resolves and attaches the full PromptTemplate and ClassificationGroup objects (using their names/IDs).
        - Fetches and attaches all comments (if not already present).
        - Attaches the selected models list.
        The fully populated ContentAnalysis objects are then passed to AnalysisService.run_analysis().

        Args:
            selected_video_urls: List of video URLs to analyze.
            selected_models: List of model identifiers/settings for analysis.

        Returns:
            Results from analysis_service.run_analysis().
        """
        prepared_analyses = []

        for url in selected_video_urls:
            # Retrieve the ContentAnalysis object for this video
            content_analysis = self.content_analysis_manager.get_content_analysis(url)
            if not content_analysis:
                raise ValueError(f"No ContentAnalysis found for video: {url}")

            # Resolve and attach the PromptTemplate object, if specified by name/ID
            if (
                hasattr(content_analysis, "prompt_template_name")
                and content_analysis.prompt_template_name
            ):
                content_analysis.prompt_template = (
                    self.prompt_template_service.load_prompt_template(
                        content_analysis.platform, content_analysis.prompt_template_name
                    )
                )

            # Resolve and attach the ClassificationGroup object, if specified by name/ID
            if (
                hasattr(content_analysis, "classification_group_name")
                and content_analysis.classification_group_name
            ):
                content_analysis.classification_group = (
                    self.classification_service.load_classification_group(
                        content_analysis.classification_group_name
                    )
                )

            # Fetch and attach comments if not already present
            if not content_analysis.comments or len(content_analysis.comments) == 0:
                content_analysis.comments = self.content_service.fetch_comments(url)

            # Attach the selected models (if per-analysis)
            content_analysis.models = selected_models

            prepared_analyses.append(content_analysis)

        # Call the analysis service with the fully prepared ContentAnalysis objects
        results = self.analysis_service.run_analysis(prepared_analyses)
        return results


##################################################################
