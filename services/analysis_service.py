# services/analysis_service.py
"""
analysis_service.py
===================

Orchestrates multi-model parallel analysis using LangGraph.
Adapted from tmp.py's validated workflow.
"""

import time
from typing import List, Dict
from langgraph.graph import StateGraph, START, END

from nodes.comment_classification_node import create_comment_classification_node
from services.model_service import ModelService
from services.classification_service import ClassificationService
from services.export_service import ExportService
from services.ratelimiter import RateLimiter
from models.domain import ContentAnalysis


class AnalysisService:
    """
    Orchestrates multi-model parallel analysis using LangGraph.
    """

    def __init__(self):
        self.classification_service = ClassificationService()
        self.export_service = ExportService()
        self.model_service = ModelService()

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

        platform = content_analysis.platform
        prompt_template_name = content_analysis.prompt_template_name
        classification_group_name = content_analysis.classification_group_name
        classification_group = content_analysis.classification_group
        content_item = content_analysis.content_item

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
                    platform=platform,
                    prompt_template_name=prompt_template_name,
                    classification_group_name=classification_group_name,
                    classification_group=classification_group,
                    content_item=content_item,
                    classification_service=self.classification_service,
                    rate_limiter=rate_limiter,
                    max_retries=max_retries,
                    qps=qps
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
    rate_limiters: Dict[str, 'RateLimiter'] = None,
    max_retries: int = 3,
    qps: int = 4
    ):
        """
            Prepares each ContentAnalysis by attaching actual LLM model clients, runs analysis, and exports an .xlsx per video.

            Args:
                analyses: List of ContentAnalysis, each populated with model infos (provider/name).
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

        for content_analysis in analyses:
            # Build model clients for this analysis, based on metadata stored in content_analysis.models
            client_list = [
                self.model_service.get_llm_model_client(model_info.provider, model_info.name)
                for model_info in content_analysis.models    # Here models is model-info, not yet a client
            ]
            # Attach to content_analysis as the actual clients
            content_analysis.models = client_list

            # Build and run the graph using the attached clients
            graph = self.create_analysis_graph(
                rate_limiters=rate_limiters,
                content_analysis=content_analysis,
                max_retries=max_retries,
                qps=qps
            )

            # The graph expects content_analysis.models already loaded as clients
            final_state = graph.invoke(content_analysis)
            results_per_video.append(final_state)

            # Export individual results to .xlsx for each final_state/content
            filepath = self.export_service.export_to_xlsx(final_state)
            output_paths.append(filepath)

        return output_paths
