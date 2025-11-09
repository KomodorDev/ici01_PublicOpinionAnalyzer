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
from typing import Any, Dict

from enums.platform_enum import PlatformEnum
from models.classification_models import ClassificationGroup
from models.content_models import ContentAnalysis, ContentItem
from models.label_model import Label
from services.classification_service import ClassificationService
from services.output_format_service import OutputFormatService
from services.prompt_service import PromptService


def create_comment_classification_node(
    client: Any,
    platform: PlatformEnum,
    prompt_template_name: str,
    classification_group_name: str,
    classification_group: ClassificationGroup,
    content_item: ContentItem,
    classification_service: ClassificationService,
    output_format_service: OutputFormatService,
    rate_limiter=None,
    max_retries: int = 3,
    qps: int = 4,
):
    """
    Creates a node for classifying comments with a specific LLM and config.

    Configures its own PromptService, which is not shared.
    """
    prompt_service = PromptService(
        platform=platform,
        prompt_template_name=prompt_template_name,
        classification_group_name=classification_group_name,
        content_item=content_item,
        classification_service=classification_service,
        output_format_service=output_format_service,
    )

    def process(content_analysis: ContentAnalysis) -> Dict:
        comments = content_analysis.comments
        model_name = getattr(client, "model", "UnknownModel")
        print(f"\n🤖 [{model_name}] Starting processing of {len(comments)} comments...")
        start_time = time.time()

        for comment in comments:
            question_start = time.time()
            attempts = 0
            success = False
            label_map = {}

            # Retry logic
            while attempts < max_retries and not success:
                try:
                    if rate_limiter:
                        rate_limiter.acquire()

                    sys_prompt, usr_prompt = prompt_service.create_prompt(comment)
                    api_result = client.invoke(sys_prompt, usr_prompt)

                    if rate_limiter:
                        rate_limiter.release()

                    # Validate and parse API response
                    if check_json(api_result):
                        parsed = json.loads(api_result) if isinstance(api_result, str) else api_result
                        missing = []
                        label_map = {}

                        for classification in classification_group:
                            label_data = parsed.get(classification.name)
                            if label_data is None:
                                missing.append(classification.name)
                                continue

                            label = Label(
                                value=label_data.get("value") if isinstance(label_data, dict) else label_data,
                                explanation=label_data.get("explanation") if isinstance(label_data, dict) else None
                            )
                            is_valid = classification_service.validate_label_for_classification(classification, label)
                            label_map[classification.name] = label if is_valid else Label(
                                value=None, explanation="Invalid label value."
                            )

                        if missing:
                            attempts += 1
                            if attempts < max_retries:
                                print(
                                    f"  ⚠️  [{model_name}] Missing labels {missing} for comment ID {comment.comment_id}, retry {attempts}/{max_retries}"
                                )
                            continue  # Retry
                        else:
                            success = all(l.value is not None for l in label_map.values())
                            print(
                                f"  [{model_name}] Processed comment ID {comment.comment_id}: "
                                f"{'Success' if success else 'Some labels invalid'}"
                            )
                    else:
                        attempts += 1
                        if attempts < max_retries:
                            print(
                                f"  ⚠️  [{model_name}] Comment ID {comment.comment_id} returned non-JSON, retry {attempts}/{max_retries}"
                            )
                except Exception as e:
                    if rate_limiter:
                        rate_limiter.release()
                    attempts += 1
                    print(
                        f"  ✗ [{model_name}] Error processing comment ID {comment.comment_id}: {str(e)}"
                    )

            # Save results in comment.labels under model_name
            if not hasattr(comment, 'labels') or comment.labels is None:
                comment.labels = {}
            comment.labels.setdefault(model_name, {})

            # Save all labels, fill in error/default label if any were missing or invalid
            for classification in classification_group:
                if classification.name in label_map and label_map[classification.name].value is not None:
                    comment.labels[model_name][classification.name] = label_map[classification.name]
                else:
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

        # Optionally, return a summary or simply {}
        return {}

    return process


##################################################################
# Rate Limiter
##################################################################
class RateLimiter:
    """Controls concurrent requests to prevent API rate limits."""
    
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = Semaphore(max_concurrent)
    
    def acquire(self):
        self.semaphore.acquire()
    
    def release(self):
        self.semaphore.release()


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