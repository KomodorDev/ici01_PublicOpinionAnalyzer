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

from enums.platform_enum import PlatformEnum
from models.classification_models import ClassificationGroup
from models.content_models import ContentAnalysis, ContentItem
from models.label_model import Label
from services.classification_service import ClassificationService
from services.prompt_runtime_service import PromptRuntimeService


def create_comment_classification_node(
    client: Any,
    platform: PlatformEnum,
    prompt_template_name: str,
    classification_group_name: str,
    classification_group: ClassificationGroup,
    content_item: ContentItem,
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
        model_name = getattr(client, "model", "UnknownModel")
        print(f"\n🤖 [{model_name}] Starting processing of {len(comments)} comments...")
        start_time = time.time()

        for comment in comments:
            question_start = time.time()
            attempts = 0
            success = False
            label_map = {}

            # Retry logic for each comment/classification set
            while attempts < max_retries and not success:
                try:
                    # (1) Throttle model calls if needed
                    if rate_limiter:
                        rate_limiter.acquire()

                    # (2) Prepare LLM/system/user prompt for this comment
                    sys_prompt, usr_prompt = prompt_service.create_prompt(comment)

                    # (3) Call LLM/model API with the prompts and get a result
                    api_result = client.invoke(sys_prompt, usr_prompt)

                    # (4) Release throttle/resource if used
                    if rate_limiter:
                        rate_limiter.release()

                    # (5) Parse and check validity of JSON result
                    if check_json(api_result):
                        parsed = json.loads(api_result) if isinstance(api_result, str) else api_result
                        missing = [] # To collect any classifications absent from the model output
                        label_map = {}

                        # (6) For every classification this comment needs
                        for classification in classification_group:
                            label_data = parsed.get(classification.name)

                            if label_data is None:
                                # If label is missing, remember to retry
                                missing.append(classification.name)
                                continue

                            # (7) Build Label instance from the API result dict or raw value
                            label = Label(
                                value=label_data.get("value") if isinstance(label_data, dict) else label_data,
                                explanation=label_data.get("explanation") if isinstance(label_data, dict) else None
                            )

                            # (8) Validate label (type/range/category); if invalid, store a default error Label
                            is_valid = classification_service.validate_label_for_classification(classification, label)
                            label_map[classification.name] = label if is_valid else Label(
                                value=None, explanation="Invalid label value."
                            )

                        if missing:
                            # (9) If any label is missing, retry the whole model call for this comment
                            attempts += 1
                            if attempts < max_retries:
                                print(
                                    f"  ⚠️  [{model_name}] Missing labels {missing} for comment ID {comment.comment_id}, retry {attempts}/{max_retries}"
                                )
                            continue  # Retry
                        else:
                            # (10) If all labels present, check if all are valid (success for this comment)
                            success = all(l.value is not None for l in label_map.values())
                            print(
                                f"  [{model_name}] Processed comment ID {comment.comment_id}: "
                                f"{'Success' if success else 'Some labels invalid'}"
                            )
                    else:
                        # (11) If model response isn't JSON, count as failed attempt, possibly retry
                        attempts += 1
                        if attempts < max_retries:
                            print(
                                f"  ⚠️  [{model_name}] Comment ID {comment.comment_id} returned non-JSON, retry {attempts}/{max_retries}"
                            )
                except Exception as e:
                    # (12) Any exception releases rate limiter and counts as a failed attempt
                    if rate_limiter:
                        rate_limiter.release()
                    attempts += 1
                    print(
                        f"  ✗ [{model_name}] Error processing comment ID {comment.comment_id}: {str(e)}"
                    )

            # (13) Ensure the comment.labels field exists and is ready for model/classification results
            if not hasattr(comment, 'labels') or comment.labels is None:
                comment.labels = {}
            comment.labels.setdefault(model_name, {})

            # (14) Store results for every classification: actual Label if valid, or error Label if not
            for classification in classification_group:
                if classification.name in label_map and label_map[classification.name].value is not None:
                    comment.labels[model_name][classification.name] = label_map[classification.name]
                else:
                    # Store a default error Label for missing, invalid, or never-computed outputs
                    comment.labels[model_name][classification.name] = Label(
                        value=None,
                        explanation="Label result missing, invalid, or retries exceeded."
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
