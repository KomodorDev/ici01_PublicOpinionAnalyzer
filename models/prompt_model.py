# models/prompt_model.py
"""
prompt_model.py
===============

Data models for prompt templates.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Prompt:
    """Single prompt component (system or user)."""
    role: str  # "system" or "user"
    content: str


@dataclass
class PromptGroup:
    """Group of prompts forming a complete prompt template."""
    name: str
    platform: str
    prompts: List[Prompt]
    description: str = ""
    
    @classmethod
    def from_template_dict(cls, template_dict: dict) -> 'PromptGroup':
        """
        Create PromptGroup from template dictionary.
        
        Args:
            template_dict: Dictionary loaded from JSON template file
            
        Returns:
            PromptGroup instance
        """
        # For now, treat the entire template as a user prompt
        # System prompt can be empty or a generic instruction
        prompts = [
            Prompt(role="system", content=""),  # Empty system prompt
            Prompt(role="user", content=template_dict.get("template", ""))
        ]
        
        return cls(
            name=template_dict.get("name", ""),
            platform=template_dict.get("platform", ""),
            prompts=prompts,
            description=template_dict.get("description", "")
        )

