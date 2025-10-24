# models/label_model.py
from dataclasses import dataclass
from typing import Optional, Union

@dataclass
class Label:
    """
    Stores the result of applying a classification to a piece of content
    (e.g., a comment, post, or video summary).
    """

    classification_id: str
    comment_id: str
    value: Optional[Union[bool, float, str, dict]] = None
    confidence: Optional[float] = None
    assigned_by: str = "LLM"
