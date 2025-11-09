"""
label_model.py
==============

Data structure for storing the result of applying a classification question
(e.g., sentiment, stance, toxicity) to a single piece of content—typically
a comment, post, or similar text entry.

Each Label represents a single answer, including the predicted value,
confidence score, and (optionally) a human-readable rationale/explanation
(often provided by an LLM).

Labels are intended to be organized in a nested dictionary on the comment
object:
    labels[model_name][question_id] = Label(...)

- model_name:    Which model provided the label (e.g., "gpt-4", "llama-7b").
- question_id:   The classification or task (e.g., "pro_taiwan", "toxicity").

This design is robust for ensemble/multi-model, multi-question, and
explainable AI workflows.

Example usage:
    label = Label(
        value=True,
        confidence=0.93,
        explanation="Comment supports Taiwan based on explicit statement."
    )
    comment.labels["gpt-4"]["pro_taiwan"] = label
"""

from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any

##################################################################
@dataclass
class Label:
    """
    Represents the answer (and supporting explanation) to a classification
    question for a particular comment and model.

    Attributes:
        value: The answer or prediction.
            - Boolean: True/False/None
            - Numeric: int or float
            - Probability: float (0.0 - 1.0)
            - Categorical: str (single label) or List[str] (multi-label)
            - Text: str
            - Pairwise/Mapping: Dict[str, Any] (e.g., entity→value or category→value)
        explanation: Optional model rationale, supporting text, or reasoning (e.g., LLM output).
    """
    value: Optional[
        Union[
            bool,
            float,
            int,
            str,
            List[str],         # for multi-label categorical
            Dict[str, Any]     # for pairwise/mapping
        ]
    ] = None
    explanation: Optional[str] = None  # LLM rationale, supporting text, etc.

##################################################################