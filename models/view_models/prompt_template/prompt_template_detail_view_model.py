from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PromptTemplateDetailViewModel:
    """
    View model representing the full details of a prompt template
    for display in the UI editor.
    """
    name: str = ""
    platform: str = ""
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    placeholders_required: List[str] = field(default_factory=list)
    placeholders_optional: List[str] = field(default_factory=list)
    placeholders_found: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None  # ISO 8601 format
