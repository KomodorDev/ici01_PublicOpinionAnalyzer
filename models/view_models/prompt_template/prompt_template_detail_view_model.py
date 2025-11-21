from dataclasses import dataclass, field
from typing import List

@dataclass
class PromptTemplateDetailViewModel:
    """
    View model representing the full details of a prompt template
    for display in the UI editor.
    """
    name: str = ""
    platform: str = ""
    description: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    placeholders_required: List[str] = field(default_factory=list)
    placeholders_optional: List[str] = field(default_factory=list)
    placeholders_found: List[str] = field(default_factory=list)
    last_updated: str = "" # ISO 8601 format
