# models/prompt_model.py
"""
prompt_model.py
===============

Data model for prompt management.
"""

from dataclasses import dataclass, field
from typing import List


##################################################################
@dataclass
class Prompt:
    """Represents a single prompt with its content."""
    
    name: str              # prompt 文件名（不含副檔名）
    content: str           # prompt 內容
    
    def __str__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Prompt(name='{self.name}', preview='{preview}')"


##################################################################
@dataclass
class PromptGroup:
    """
    Organizes multiple `Prompt` objects into a named thematic group.
    
    Each `PromptGroup` serves as a container for related prompts
    that share a conceptual purpose.
    
    Attributes:
        name (str):
            Unique Human-readable title of the group.
        prompts (list[Prompt]):
            A list of `Prompt` instances that belong to this group.
    """
    
    name: str
    prompts: List[Prompt] = field(default_factory=list)


##################################################################

