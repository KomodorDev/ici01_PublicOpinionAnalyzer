
# controllers/general_controller.py
"""
general_controller.py
================

Handles logic for the "General" tab.
"""
from typing import Dict, List

from views.general_view import GeneralView
from services.general_service import GeneralService
from services.model_service import ModelService
from services.classification_service import ClassificationService
from services.prompt_service import PromptService
from services.analysis_service import run_analysis
from services.content_fetchers.youtube_fetcher import YouTubeFetcher
from models.content_models import ContentAnalysis


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
        
        # Service layer - 職責分離 (Separation of Concerns)
        self.general_service = GeneralService()  # General operations
        self.model_service = ModelService()  # LLM model management
        self.classification_service = ClassificationService()  # Classification groups
        self.prompt_service = PromptService()  # Prompt template management
        
        # Import and initialize OutputFormatService
        from services.output_format_service import OutputFormatService
        self.output_format_service = OutputFormatService()  # Output formatting

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
            prompt_styles_data = self.prompt_service.list_all_prompt_template_names(
                platform="youtube"
            )
            # Extract template names from the data
            prompt_style_names = [ps["name"] for ps in prompt_styles_data if "name" in ps]
        except (FileNotFoundError, RuntimeError, OSError):
            prompt_style_names = ["default"]

        self.general_view.render_general_view(
            controller=self,
            models=models,
            groups=group_names,
            prompt_styles=prompt_style_names
        )

    # ----------------------------------------------------------------
    def run_analysis( 
        self,
        summaries: Dict[str, str],
        model_selections: List[tuple[str, str]],
        prompt_style_name: str,
        classification_group_name: str,
        progress_callback=None
    ) -> List[ContentAnalysis]:
        """
        Run complete analysis pipeline (MVC Controller 職責).
        
        This method orchestrates the entire analysis workflow:
        1. Content fetching (via ContentFetchers)
        2. Model client setup (via ModelService)
        3. Prompt and classification preparation (via PromptService & ClassificationService)
        4. Analysis execution (via AnalysisService with LangGraph)
        
        Args:
            summaries: Dict mapping URL to user-approved summary
            model_selections: List of (provider, model_id) tuples
            prompt_style_name: Name of prompt style (e.g., "default")
            classification_group_name: Name of classification group (e.g., "Default")
            progress_callback: Optional callback(current, total, msg)
            
        Returns:
            List of processed ContentAnalysis objects with labeled comments
        """
        # Step 1: Fetch content iteratively
        analyses = []
        total = len(summaries)
        
        for i, (url, summary) in enumerate(summaries.items(), 1):
            try:
                if progress_callback:
                    progress_callback(i, total, f"Fetching content from {url}")
                
                # Fetch content for this URL
                fetcher = YouTubeFetcher()
                analysis = fetcher.fetch_content(url)
                analysis.content.summary = summary
                
                analyses.append(analysis)
                
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                if progress_callback:
                    progress_callback(i, total, f"❌ Error fetching {url}: {str(e)}")
        
        if not analyses:
            raise ValueError("No content could be fetched")
        
        # Step 2: Get model clients from selections
        model_clients = []
        model_names = []
        for provider, model_id in model_selections:
            client = self.model_service.get_model_client(provider, model_id)
            model_clients.append(client)
            # Create a readable name for this model
            model_names.append(f"{provider}:{model_id}")
        
        # Step 3: Get prompt style object from PromptService
        prompt_style = self.prompt_service.get_prompt_style(prompt_style_name)
        
        # Step 4: Get classification group object from ClassificationService
        classification_group = self.classification_service.get_classification_group(
            classification_group_name
        )
        
        # Step 5: Delegate to AnalysisService for LangGraph-based parallel processing
        # 職責分離：Controller 只負責協調，不負責具體實現
        return run_analysis(
            analyses=analyses,
            model_clients=model_clients,
            model_names=model_names,
            prompt_style=prompt_style,
            classification_group=classification_group,
            prompt_service=self.prompt_service,  # For prompt building
            classification_service=self.classification_service,  # For classification formatting
            output_format_service=self.output_format_service,  # For output formatting
            progress_callback=progress_callback
        )
    

##################################################################
