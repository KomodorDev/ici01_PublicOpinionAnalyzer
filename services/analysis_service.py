# services/analysis_service.py
"""
analysis_service.py
===================

Orchestrates multi-model parallel analysis using LangGraph.
Adapted from tmp.py's validated workflow.
"""

import json
import time
from typing import List, Dict, Annotated, Any
from typing_extensions import TypedDict
from threading import Semaphore
from langgraph.graph import StateGraph, START, END

from models.content_models import ContentAnalysis, Comment
from models.classification_models import ClassificationGroup


##################################################################
# State Definition
##################################################################

def merge_model_results(left: Dict[str, List[Dict]], right: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    Custom reducer for merging model results from parallel nodes.
    
    Each node returns a dict with one model's results: {model_name: [...]}
    This function merges them into a single dict with all models.
    """
    if not left:
        return right
    if not right:
        return left
    # Merge dictionaries
    merged = {**left, **right}
    return merged


class AnalysisState(TypedDict):
    """LangGraph state for multi-model parallel comment analysis."""
    # Input data
    comments: List[Comment]  # All comments to analyze
    system_prompt: str  # System prompt from prompt_style
    user_prompt_template: str  # User prompt template with placeholders
    content_item: Any  # ContentItem with video/content metadata
    classifications_string: str  # Formatted classification questions
    output_format_string: str  # Formatted output format specification
    prompt_service: Any  # PromptService instance for building prompts
    
    # Results from each model (parallel updates)
    # model_results: Annotated[Dict[str, List[Dict]], operator.add]
    model_results: Annotated[Dict[str, List[Dict]], merge_model_results]


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


def call_model_api(client: Any, system_prompt: str, user_prompt: str) -> str:
    """
    Call model API with prompts using LangChain ChatOpenAI interface.
    
    Args:
        client: LangChain ChatOpenAI client from ModelService
        system_prompt: System prompt
        user_prompt: User prompt
        
    Returns:
        JSON string with analysis results
    """
    try:
        # LangChain ChatOpenAI uses .invoke() with message list
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = client.invoke(messages)
        
        # Extract content from AIMessage response
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


##################################################################
# Model Node Processing
##################################################################
def create_model_node(client: Any, model_name: str, rate_limiter: RateLimiter, 
                     max_retries: int = 3, qps: int = 4):
    """
    Create a processing node for one model.
    
    Args:
        client: Model client instance
        model_name: Identifier for this model
        rate_limiter: Rate limiter for this model
        max_retries: Maximum retry attempts per comment
        qps: Queries per second limit
        
    Returns:
        Processing function for LangGraph node
    """
    def process(state: AnalysisState) -> Dict:
        comments = state["comments"]
        system_prompt = state["system_prompt"]
        user_prompt_template = state["user_prompt_template"]
        content_item = state["content_item"]
        classifications_string = state["classifications_string"]
        output_format_string = state["output_format_string"]
        prompt_service = state["prompt_service"]
        
        results = []
        
        print(f"\n🤖 [{model_name}] 開始處理 {len(comments)} 條評論...")
        start_time = time.time()
        
        for idx, comment in enumerate(comments, 1):
            question_start = time.time()
            attempts = 0
            success = False
            result_data = None
            
            # Retry logic
            while attempts < max_retries and not success:
                try:
                    rate_limiter.acquire()
                    
                    # Build prompts for this comment using PromptService
                    sys_prompt, usr_prompt = prompt_service.build_analysis_prompt(
                        comment=comment,
                        content_item=content_item,
                        system_prompt=system_prompt,
                        user_prompt_template=user_prompt_template,
                        classifications_string=classifications_string,
                        output_format_string=output_format_string
                    )
                    
                    # Call model API
                    api_result = call_model_api(client, sys_prompt, usr_prompt)
                    
                    rate_limiter.release()
                    
                    # Validate JSON response
                    if check_json(api_result):
                        success = True
                        result_data = {
                            "comment_id": comment.comment_id,
                            "comment_text": comment.text,
                            "result": api_result,
                            "status": "Success",
                            "attempts": attempts + 1
                        }
                        if idx % 10 == 0 or idx == len(comments):
                            print(f"  [{model_name}] 進度: {idx}/{len(comments)} 條評論")
                    else:
                        attempts += 1
                        if attempts < max_retries:
                            print(f"  ⚠️  [{model_name}] 評論 {idx} 返回非 JSON，重試 {attempts}/{max_retries}")
                        
                except Exception as e:
                    rate_limiter.release()
                    attempts += 1
                    print(f"  ✗ [{model_name}] 評論 {idx} 錯誤: {str(e)}")
            
            # If all retries failed
            if not success:
                result_data = {
                    "comment_id": comment.comment_id,
                    "comment_text": comment.text,
                    "result": json.dumps({"error": "達到最大重試次數"}),
                    "status": "Fail",
                    "attempts": attempts
                }
            
            results.append(result_data)
            
            # QPS control
            elapsed = time.time() - question_start
            sleep_time = (1.0 / qps) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r["status"] == "Success")
        fail_count = len(results) - success_count
        
        print(f"  ✅ [{model_name}] 完成！成功: {success_count}/{len(results)}, "
              f"失敗: {fail_count}, 耗時: {total_time:.2f}秒")
        
        # Return results for this model
        return {"model_results": {model_name: results}}
    
    return process


##################################################################
# Graph Creation
##################################################################
def create_analysis_graph(
    model_clients: List[Any],
    model_names: List[str],
    rate_limiters: Dict[str, RateLimiter],
    max_retries: int = 3,
    qps: int = 4
):
    """
    Create LangGraph workflow for multi-model parallel analysis.
    
    Args:
        model_clients: List of model client instances
        model_names: List of model identifiers
        rate_limiters: Dict mapping model names to rate limiters
        max_retries: Maximum retries per comment
        qps: Queries per second per model
        
    Returns:
        Compiled LangGraph
    """
    graph_builder = StateGraph(AnalysisState)
    
    # Add node for each model
    for client, model_name in zip(model_clients, model_names):
        rate_limiter = rate_limiters.get(model_name)
        if not rate_limiter:
            # Create default rate limiter if not specified
            rate_limiter = RateLimiter(max_concurrent=5)
            rate_limiters[model_name] = rate_limiter
        
        graph_builder.add_node(
            model_name,
            create_model_node(client, model_name, rate_limiter, max_retries, qps)
        )
    
    # START -> All models (parallel execution)
    for model_name in model_names:
        graph_builder.add_edge(START, model_name)
    
    # All models -> END
    for model_name in model_names:
        graph_builder.add_edge(model_name, END)
    
    return graph_builder.compile()


##################################################################
# Main Analysis Function
##################################################################
def run_analysis(
    analyses: List[ContentAnalysis],
    model_clients: List[Any],
    model_names: List[str],
    prompt_style: Prompt,
    classification_group: ClassificationGroup,
    prompt_service: Any,
    classification_service: Any,
    output_format_service: Any,
    progress_callback=None,
    qps: int = 4,
    max_retries: int = 3,
    rate_limiters: Dict[str, RateLimiter] = None
) -> List[ContentAnalysis]:
    """
    Run multi-model parallel analysis on all comments using LangGraph.
    
    This function orchestrates the entire analysis pipeline:
    1. Prepares prompts and formatting strings
    2. Creates LangGraph workflow with parallel model nodes
    3. Executes the workflow
    4. Attaches results to comments
    
    Args:
        analyses: List of ContentAnalysis objects with comments
        model_clients: List of model client instances
        model_names: List of model identifiers (same order as clients)
        prompt_style: PromptGroup with system/user prompts
        classification_group: ClassificationGroup with classification questions
        prompt_service: PromptService for building prompts (職責分離：prompt 構建)
        classification_service: ClassificationService for formatting classifications
        output_format_service: OutputFormatService for formatting output specs
        progress_callback: Optional callback(current, total, message)
        qps: Queries per second limit per model
        max_retries: Maximum retry attempts per comment
        rate_limiters: Optional dict of rate limiters per model
        
    Returns:
        List of ContentAnalysis with populated labels
    """
    # Collect all comments from all analyses
    all_comments = []
    for analysis in analyses:
        all_comments.extend(analysis.comments)
    
    if not all_comments:
        print("⚠️  沒有評論需要分析")
        return analyses
    
    print(f"\n📊 分析總覽")
    print(f"   內容數量: {len(analyses)}")
    print(f"   評論總數: {len(all_comments)}")
    print(f"   模型數量: {len(model_clients)}")
    print("=" * 70)
    
    # Extract prompts from prompt_style
    # Assuming prompt_style has prompts[0] = system, prompts[1] = user
    system_prompt = prompt_style.prompts[0].content if prompt_style.prompts else ""
    user_prompt_template = prompt_style.prompts[1].content if len(prompt_style.prompts) > 1 else ""
    
    # Get content_item from first analysis (assuming all from same video/content)
    content_item = analyses[0].content if analyses else None
    
    # Format classifications using classification_service
    classifications_string = classification_service.get_classification_group_to_string(
        classification_group.name, "CLASSIFICATIONS"
    )
    
    # Format output format using output_format_service
    output_format_string = output_format_service.get_output_format_string(
        classification_group.name
    )
    
    # Setup rate limiters
    if rate_limiters is None:
        rate_limiters = {}
        for model_name in model_names:
            # Default: different limits for different providers
            if "gpt" in model_name.lower():
                rate_limiters[model_name] = RateLimiter(max_concurrent=10)
            elif "gemini" in model_name.lower():
                rate_limiters[model_name] = RateLimiter(max_concurrent=15)
            elif "claude" in model_name.lower():
                rate_limiters[model_name] = RateLimiter(max_concurrent=8)
            elif "local" in model_name.lower() or "lmstudio" in model_name.lower():
                rate_limiters[model_name] = RateLimiter(max_concurrent=1)
            else:
                rate_limiters[model_name] = RateLimiter(max_concurrent=5)
    
    # Create LangGraph
    print("🔧 建立 LangGraph 工作流...")
    graph = create_analysis_graph(
        model_clients=model_clients,
        model_names=model_names,
        rate_limiters=rate_limiters,
        max_retries=max_retries,
        qps=qps
    )
    print("✓ 工作流建立完成")
    
    # Create initial state
    initial_state = AnalysisState(
        comments=all_comments,
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        content_item=content_item,
        classifications_string=classifications_string,
        output_format_string=output_format_string,
        prompt_service=prompt_service,  # Pass prompt_service for prompt building
        model_results={}
    )
    
    # Execute graph
    print("\n🚀 開始並行處理（所有模型同時運行）...")
    start_time = time.time()
    
    final_state = graph.invoke(initial_state)
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print(f"✅ 處理完成！")
    print(f"   總耗時: {total_time:.2f} 秒")
    print(f"   評論數: {len(all_comments)}")
    
    # Process results and attach labels to comments
    model_results = final_state.get("model_results", {})
    
    # Create a mapping from comment_id to comment object
    comment_map = {comment.comment_id: comment for comment in all_comments}
    
    # Aggregate results from all models
    print("\n📈 結果統計")
    print("=" * 70)
    for model_name, results in model_results.items():
        success_count = sum(1 for r in results if r["status"] == "Success")
        fail_count = len(results) - success_count
        success_rate = (success_count / len(results) * 100) if results else 0
        
        print(f"{model_name:20s}: 成功 {success_count:3d}/{len(results)} "
              f"({success_rate:5.1f}%), 失敗 {fail_count:3d}")
        
        # Attach labels to comments
        for result in results:
            comment_id = result["comment_id"]
            if comment_id in comment_map and result["status"] == "Success":
                try:
                    labels_data = json.loads(result["result"])
                    # Add model name to labels data
                    labels_data["model"] = model_name
                    comment_map[comment_id].labels.append(labels_data)
                except json.JSONDecodeError:
                    print(f"  ⚠️  無法解析評論 {comment_id} 的 JSON 結果")
    
    print("=" * 70)
    
    print(analyses)
    return analyses