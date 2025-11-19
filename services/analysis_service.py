# services/analysis_service.py
"""
analysis_service.py
===================

Orchestrates multi-model parallel analysis using LangGraph.
Adapted from tmp.py's validated workflow.
"""

from typing import List, Dict, Tuple, Optional
from langgraph.graph import StateGraph, START, END

from enums.task_status_enum import TaskStatusEnum
from models.domain import ContentAnalysis
from models.domain.model_run_progress_model import ModelRunProgress
from nodes.comment_classification_node import create_comment_classification_node
from services.model_service import ModelService
from services.classification_service import ClassificationService
from services.export_service import ExportService
from services.ratelimiter import RateLimiter



class AnalysisService:
    """
    Orchestrates multi-model parallel analysis using LangGraph.
    """

    def __init__(
        self,
        model_service: Optional[ModelService] = None,
        export_service: Optional[ExportService] = None,
        classification_service: Optional[ClassificationService] = None,
    ):
        self.model_service = model_service or ModelService()
        self.export_service = export_service or ExportService()
        self.classification_service = classification_service or ClassificationService()

    ##################################################################
    # Graph Creation
    ##################################################################
    def create_analysis_graph(
        self,
        rate_limiters: dict,
        content_analysis: ContentAnalysis,
        max_retries: int = 3,
        qps: int = 4
    ):
        """
        Build a LangGraph workflow for multi-model parallel analysis.
        """
        graph_builder = StateGraph(ContentAnalysis)

        for client in content_analysis.models:
            model_name = client.name
            rate_limiter = rate_limiters.get(model_name)
            if not rate_limiter:
                rate_limiter = RateLimiter(max_concurrent=5)
                rate_limiters[model_name] = rate_limiter

            graph_builder.add_node(
                model_name,
                create_comment_classification_node(
                    client=client,
                    rate_limiter=rate_limiter,
                    max_retries=max_retries,
                    qps=qps,
                    classification_service=self.classification_service
                )
            )
        for client in content_analysis.models:
            graph_builder.add_edge(START, client.name)
            graph_builder.add_edge(client.name, END)
        return graph_builder.compile()



    ##################################################################
    # Main Analysis Function
    ##################################################################
    def run_analysis(
        self,
        analyses: List[ContentAnalysis],
        selected_models: List[Tuple[str, str]],
        rate_limiters: Dict[str, 'RateLimiter'] = None,
        max_retries: int = 3,
        qps: int = 4,
    ):
        """
        Prepares each ContentAnalysis by attaching actual LLM model clients, runs
        analysis, and exports an .xlsx per video.

        Args:
            analyses: List of ContentAnalysis to analyze.
            selected_models: List of (provider, model_name) chosen in the UI.
            rate_limiters: Dict of {model_name: RateLimiter}, or constructed as needed.
            max_retries: Retries per request.
            qps: Queries per second per model.

        Returns:
            List of file paths (or objects) for generated .xlsx files, one per ContentAnalysis.
        """
        output_paths = []
        results_per_video = []

        if rate_limiters is None:
            rate_limiters = {}

        # Build clients once per selected model (you can reuse across contents)
        client_list = [
            self.model_service.get_llm_model_client(provider, model_name)
            for (provider, model_name) in selected_models
    ]

        for content_analysis in analyses:
            # Attach the clients to this ContentAnalysis so the graph can use them
            content_analysis.models = client_list

            content_analysis.model_run_progress = [
                ModelRunProgress(
                    provider=provider,
                    model_name=model_name,
                    status=TaskStatusEnum.PENDING,
                    progress=0,
                    current_comment=0,
                    total_comments=len(content_analysis.comments),
                    error=None,
                )
                for (provider, model_name) in selected_models
            ]

            graph = self.create_analysis_graph(
                rate_limiters=rate_limiters,
                content_analysis=content_analysis,
                max_retries=max_retries,
                qps=qps,
            )

            # The graph expects content_analysis.models already loaded as clients
            final_state = graph.invoke(content_analysis)
            results_per_video.append(final_state)

            # Export individual results to .xlsx for each final_state/content
            filepath = self.export_service.export_to_xlsx(final_state)
            output_paths.append(filepath)

        return output_paths
