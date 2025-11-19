"""
comment_classification_node.py
====================

Factory function for building LangGraph node functions that handle
parallel LLM-based analysis tasks (e.g., multi-comment classification, etc.)

Usage:
    from nodes.llm_analysis_node import create_llm_analysis_node

    node_fn = create_llm_analysis_node(client, model_name, rate_limiter, ...)
"""

import time
import json
from typing import Any
from xmlrpc import client

from enums.platform_enum import PlatformEnum
from models.domain import ClassificationGroup, ContentAnalysis, ContentItem, Label
from services.classification_service import ClassificationService
from services.prompt_runtime_service import PromptRuntimeService


def create_comment_classification_node(
    client: Any,
    prompt_runtime_service: PromptRuntimeService,
    classification_service: ClassificationService,
    rate_limiter=None,
    max_retries: int = 3,
    qps: int = 4,

):
    """
    Creates a node for classifying comments with a specific LLM and config.

    Configures its own PromptService, which is not shared.
    """
    prompt_service = PromptRuntimeService(
        platform=platform,
        prompt_template_name=prompt_template_name,
        classification_group_name=classification_group_name,
        content_item=content_item,
        classification_service=classification_service,
    )

    def process(content_analysis: ContentAnalysis):
        comments = content_analysis.comments
        classification_group = content_analysis.classification_group.classifications 

        model_name = client.model_name
        print(f"\n🤖 [{model_name}] Starting processing of {len(comments)} comments...")
        start_time = time.time()

        for comment in comments:
            question_start = time.time()
            attempts = 0
            success = False
            label_map = {}

            # ============================================================
            # 1) CALL MODEL WITH RETRIES (build prompts + invoke + parse)
            # ============================================================
            while attempts < max_retries and not success:
                try:
                    # 1.1) Throttle if we have a rate limiter
                    if rate_limiter:
                        rate_limiter.acquire()

                    # 1.2) Build system + user prompts for THIS comment
                    sys_prompt, usr_prompt = prompt_runtime_service.create_prompt(
                        content_analysis=content_analysis,
                        comment=comment,
                    )

                    # 1.3) Invoke the model
                    api_result = client.invoke(sys_prompt, usr_prompt)

                    # 1.4)Always release after the call if used
                    if rate_limiter:
                        rate_limiter.release()

                    # 1.5) Ensure the reply is JSON-ish
                    if not check_json(api_result):
                        attempts += 1
                        if attempts < max_retries:
                            print(
                                f"  ⚠️ [{model_name}] Comment ID {comment.comment_id} "
                                f"returned non-JSON, retry {attempts}/{max_retries}"
                            )
                        continue

                    # 1.6) Parse JSON into a Python dict
                    parsed = (
                        json.loads(api_result)
                        if isinstance(api_result, str)
                        else api_result
                    )

                    missing: list[str] = []
                    label_map = {}

                    # ==========================================
                    # 2) BUILD LABELS FOR EACH CLASSIFICATION
                    # ==========================================
                    for classification in classification_group:
                        label_data = parsed.get(classification.name)

                        if label_data is None:
                            # Missing label -> mark for retry
                            missing.append(classification.name)
                            continue

                        # Build Label from either dict or raw scalar
                        if isinstance(label_data, dict):
                            label = Label(
                                value=label_data.get("value"),
                                explanation=label_data.get("explanation"),
                            )
                        else:
                            label = Label(value=label_data, explanation=None)

                        # Validate label, or mark as invalid
                        is_valid = classification_service.validate_label_for_classification(
                            classification,
                            label,
                        )
                        label_map[classification.name] = (
                            label
                            if is_valid
                            else Label(value=None, explanation="Invalid label value.")
                        )

                    # If any classifications missing, retry the whole call
                    if missing:
                        attempts += 1
                        if attempts < max_retries:
                            print(
                                f"  ⚠️ [{model_name}] Missing labels {missing} "
                                f"for comment ID {comment.comment_id}, "
                                f"retry {attempts}/{max_retries}"
                            )
                        continue

                    # All labels present: consider success if all have non-None value
                    success = all(l.value is not None for l in label_map.values())
                    print(
                        f"  [{model_name}] Processed comment ID {comment.comment_id}: "
                        f"{'Success' if success else 'Some labels invalid'}"
                    )

                except Exception as e:
                    # Any exception: release limiter, count attempt, maybe retry
                    if rate_limiter:
                        rate_limiter.release()
                    attempts += 1
                    print(
                        f"  ✗ [{model_name}] Error processing comment ID "
                        f"{comment.comment_id}: {str(e)}"
                    )

            # =======================================================
            # 3) ATTACH RESULTS TO COMMENT (labels per classification)
            # =======================================================
            if not hasattr(comment, "labels") or comment.labels is None:
                comment.labels = {}
            comment.labels.setdefault(model_name, {})

            for classification in classification_group:
                cls_name = classification.name
                if (
                    cls_name in label_map
                    and label_map[cls_name].value is not None
                ):
                    comment.labels[model_name][cls_name] = label_map[cls_name]
                else:
                    # Default error Label when missing/invalid/exceeded retries
                    comment.labels[model_name][cls_name] = Label(
                        value=None,
                        explanation="Label result missing, invalid, or retries exceeded.",
                    )

            # QPS control
            elapsed = time.time() - question_start
            sleep_time = (1.0 / qps) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        total_time = time.time() - start_time
        print(
            f"  ✅ [{model_name}] Finished! Elapsed time: {total_time:.2f} seconds"
        )

    return process

##################################################################
# Helper Functions
##################################################################
def check_json(result: str) -> bool:
    """Check if result is valid JSON."""
    try:
        json.loads(result)
        return True
    except:
        return False
