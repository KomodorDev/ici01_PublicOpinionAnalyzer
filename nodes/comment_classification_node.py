"""
comment_classification_node.py
====================

Factory function for building LangGraph node functions that handle
parallel LLM-based analysis tasks (e.g., multi-comment classification, etc.)

Usage:
    from nodes.llm_analysis_node import create_llm_analysis_node

    node_fn = create_llm_analysis_node(client, model_name, rate_limiter, ...)
"""

import traceback

import time
import json
from typing import Any

from enums import TaskStatusEnum
from models.domain import  ContentAnalysis, Label, ModelRunProgress
from services.classification_service import ClassificationService
from services.prompt_runtime_service import PromptRuntimeService

MISSING_LABEL_SENTINEL = "__MISSING_OR_ERROR__"

def create_comment_classification_node(
    client: Any,
    prompt_runtime_service: PromptRuntimeService,
    classification_service: ClassificationService,
    model_run_progress: ModelRunProgress,
    rate_limiter=None,
    max_retries: int = 3,
    qps: int = 4,

):
    """
    Creates a node for classifying comments with a specific LLM and config.

    Configures its own PromptService, which is not shared.
    """

    def process(content_analysis: ContentAnalysis):
        comments = content_analysis.comments
        classification_group = content_analysis.classification_group.classifications

        model_name = client.name
        total_comments = len(comments)

        # mark as RUNNING
        model_run_progress.status = TaskStatusEnum.RUNNING
        model_run_progress.current_comment = 0
        model_run_progress.total_comments = total_comments
        model_run_progress.progress = 0

        # PRINT
        print(f"\n🤖 [{model_name}] Starting processing of {total_comments} comments...")
        start_time = time.time()

        for idx, comment in enumerate(comments, start=1):
            print(f"\n🟦 Processing comment {idx}/{total_comments} (ID: {comment.comment_id})")

            question_start = time.time()
            attempts = 0
            success = False
            label_map = {}

            # ============================================================
            # 1) CALL MODEL WITH RETRIES (build prompts + invoke + parse)
            # ============================================================
            while attempts < max_retries and not success:
                print(f"\n🟦 Attempts: {attempts}")
                try:
                    # 1.1) Throttle if we have a rate limiter
                    if rate_limiter:
                        rate_limiter.acquire()

                    try:
                        # 1.2) Build system + user prompts for THIS comment
                        sys_prompt, usr_prompt = prompt_runtime_service.create_prompt(
                            content_analysis=content_analysis,
                            comment=comment,
                        )

                        # 1.3) Invoke the model
                        conversation = [
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": usr_prompt},
                        ]

                        # 🔍 DEBUG: print raw conversation
                        print("\n🔵 RAW CONVERSATION:")
                        print(conversation)
                        print("------ END OF CONVERSATION ------\n")

                        api_result = client.invoke(conversation)

                        # 🔍 DEBUG: print raw model response
                        print("\n🔵 RAW MODEL RESPONSE:")
                        print(api_result)
                        print("------ END OF RESPONSE ------\n")

                        # 1.5) Ensure the reply is JSON-ish
                        if not check_json(api_result.content):
                            attempts += 1
                            if attempts < max_retries:
                                print(
                                    f"  ⚠️ [{model_name}] Comment ID {comment.comment_id} "
                                    f"returned non-JSON, retry {attempts}/{max_retries}"
                                )
                            continue

                        # 1.6) Parse JSON into a Python dict
                        # Always get the text content from the AIMessage
                        raw = api_result.content

                        # Parse JSON
                        try:
                            parsed = json.loads(raw) if isinstance(raw, str) else raw
                        except Exception as e:
                            print("\n❌ Failed to parse model output as JSON:")
                            print(raw)
                            raise e
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

                        # If we reach here, all labels are present and valid
                        success = True
                        model_run_progress.current_comment = idx
                        model_run_progress.progress = int(idx * 100 / total_comments)

                    finally:
                        # This *always* runs if we acquired
                        if rate_limiter:
                            rate_limiter.release()

                except Exception as e:
                    # Any exception: release limiter, count attempt, maybe retry
                    if rate_limiter:
                        rate_limiter.release()
                    attempts += 1

                    model_run_progress.status = TaskStatusEnum.ERROR
                    model_run_progress.error = str(e)

                    print(
                        f"  ✗ [{model_name}] Error processing comment ID "
                        f"{comment.comment_id}: {str(e)}"
                    )

                    # Print full traceback to stdout/stderr
                    print("  --- FULL TRACEBACK BELOW ---")
                    traceback.print_exc()

                    # For now: re-raise so we see the error in the main log and stop
                    raise

            # =======================================================
            # 3) ATTACH RESULTS TO COMMENT (labels per classification)
            # =======================================================
            if not hasattr(comment, "labels") or comment.labels is None:
                comment.labels = {}
            comment.labels.setdefault(model_name, {})

            for classification in classification_group:
                cls_name = classification.name
                label = label_map.get(cls_name)

                if label is not None:
                    # Use whatever the validator produced, including value=None
                    # (None is allowed as "no stance / no info")
                    comment.labels[model_name][cls_name] = label
                else:
                    # Classification completely missing (not in model output,
                    # retries exceeded, or we never set it in label_map)
                    comment.labels[model_name][cls_name] = Label(
                        value=MISSING_LABEL_SENTINEL,
                        explanation="Label result missing or retries exceeded.",
                    )

            # QPS control
            elapsed = time.time() - question_start
            sleep_time = (1.0 / qps) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        # After all comments processed:
        model_run_progress.status = TaskStatusEnum.DONE
        model_run_progress.error = None
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
