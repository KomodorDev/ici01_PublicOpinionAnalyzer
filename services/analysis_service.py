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
from services.prompt_runtime_service import PromptRuntimeService
from services.content_service import ContentService


##################################################################
class AnalysisService:
    """
    Orchestrates multi-model parallel analysis using LangGraph.
    """

    def __init__(
        self,
        model_service: Optional[ModelService] = None,
        export_service: Optional[ExportService] = None,
        content_service: Optional["ContentService"] = None,
    ):
        self.model_service = model_service or ModelService()
        self.export_service = export_service or ExportService()
        self.content_service = content_service or ContentService()

    ##################################################################
    # Graph Creation
    ##################################################################
    def create_analysis_graph(
        self,
        rate_limiters: dict,
        content_analysis: ContentAnalysis,
        max_retries: int = 3,
        qps: int = 4,
    ):
        """
        Build a LangGraph workflow for multi-model parallel analysis.
        """

        classification_service = ClassificationService()
        prompt_runtime_service = PromptRuntimeService(classification_service)
        graph_builder = StateGraph(ContentAnalysis)

        for client in content_analysis.models:
            model_name = client.name
            rate_limiter = rate_limiters.get(model_name)
            if not rate_limiter:
                rate_limiter = RateLimiter(max_concurrent=5)
                rate_limiters[model_name] = rate_limiter

            # Find the matching ModelRunProgress for this model
            model_run_progress = None
            for mr in content_analysis.model_run_progress:
                if mr.node_name == model_name:
                    model_run_progress = mr
                    break

            if model_run_progress is None:
                raise RuntimeError(
                    f"No ModelRunProgress found for model '{model_name}'"
                )
            node_fn = create_comment_classification_node(
                client=client,
                prompt_runtime_service=prompt_runtime_service,
                classification_service=classification_service,
                model_run_progress=model_run_progress,
                rate_limiter=rate_limiter,
                max_retries=max_retries,
                qps=qps,
            )

            graph_builder.add_node(model_name, node_fn)

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
        rate_limiters: Dict[str, "RateLimiter"] = None,
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

            # 0) Attach the clients to this ContentAnalysis so the graph can use them
            content_analysis.models = client_list


            # 1) Initialize per-model progress with correct total_comments
            model_runs: list[ModelRunProgress] = []
            for (provider, model_name), client in zip(selected_models, client_list):
                model_runs.append(
                    ModelRunProgress(
                        provider=provider,
                        model_name=model_name,
                        # 🔴 DIRTY HACK: store *client.name* here so it matches LangGraph node name
                        # This is necessary because LangGraph nodes are identified by the string name of the client,
                        # and ModelRunProgress expects a node_name that matches the graph's node naming convention.
                        # Assumes that client.name is unique and stable for each model/provider combination.
                        # TODO: Refactor to decouple ModelRunProgress from client internals.
                        #       Ideally, node_name should be generated explicitly and consistently across the codebase,
                        #       rather than relying on client.name. Consider tracking this in an issue for future cleanup.
                        node_name=client.name,  # e.g. "openai_gpt-4"
                        status=TaskStatusEnum.PENDING,
                        progress=0,
                        current_comment=0,
                        total_comments=0,
                        error=None,
                    )
                )

            content_analysis.model_run_progress = model_runs

            # 2) Ensure we actually have comments
            if not content_analysis.comments:
                # adjust signature to whatever your ContentService expects
                content_analysis.comments = self.content_service.fetch_comments(
                    content_analysis
                )

            # 3) Build and run the graph
            graph = self.create_analysis_graph(
                rate_limiters=rate_limiters,
                content_analysis=content_analysis,
                max_retries=max_retries,
                qps=qps,
            )

            # The graph expects content_analysis.models already loaded as clients
            final_state = graph.invoke(content_analysis)
            self.print_content_analysis_debug(content_analysis)

            results_per_video.append(final_state)

            # Export individual results to .xlsx for each final_state/content
            filepath = self.export_service.export_to_xlsx(content_analysis)
            output_paths.append(filepath)

        return output_paths


##################################################################

    def print_content_analysis_debug(self, ca):
        print("\n=== CONTENT ANALYSIS DEBUG ===")

        # Basic metadata
        print(f"Platform: {getattr(ca, 'platform', None)}")
        print(f"Content ID: {getattr(ca.content, 'content_id', None)}")
        print(f"Title: {getattr(ca.content, 'title', None)}")
        print(f"Total comments: {len(ca.comments)}\n")

        # Loop through comments
        for idx, c in enumerate(ca.comments, start=1):
            print(f"--- Comment {idx} ---")
            print(f"ID: {c.comment_id}")
            print(f"Author: {c.author}")
            print(f"Text: {c.text}")
            print(f"Likes: {c.like_count}, Replies: {c.reply_count}")
            print("Labels:")

            if not c.labels:
                print("    (no labels)")
                continue

            # labels: Dict[model_key, Dict[class_name, Label]]
            for model_key, class_dict in c.labels.items():
                print(f"  Model: {model_key}")

                if not class_dict:
                    print("    (no classifications)")
                    continue

                for class_name, label_obj in class_dict.items():
                    value = getattr(label_obj, "value", None)
                    explanation = getattr(label_obj, "explanation", None)

                    # Unwrap enum.value if necessary
                    if hasattr(value, "value"):
                        value = value.value

                    print(f"    {class_name}: {value}")

                    if explanation:
                        print(f"      explanation: {explanation}")

            print("")  # spacer
