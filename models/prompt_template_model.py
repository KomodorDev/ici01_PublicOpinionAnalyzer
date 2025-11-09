# models/prompt_model.py
"""
prompt_template_model.py
===============

Data models for prompt templates.
"""
from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timezone
from enums.platform_enum import PlatformEnum


@dataclass
class PromptTemplateModel:
    """
    Represents a prompt template used for large language model (LLM) analysis in the MVC architecture.

    This data class stores all metadata and template strings required to generate structured prompts
    for comment classification tasks. It separates the system (instructions/rules) and user (input
    template) aspects of a prompt, as well as required variables for substitution.

    Attributes:
        template_id (str): Unique identifier for the prompt template.
        platform (str): Platform for which the prompt is intended (e.g., 'youtube').
        name (str): Human-readable name of the prompt.
        version (str): Version of the template.
        description (str): Description of the prompt's purpose.
        system_prompt (str): Instructional content for the model, including all context and rules.
        user_prompt_template (str): Template string for runtime variable substitution.
        required_variables (List[str]): List of variable names required for prompt rendering.
    """
    platform: PlatformEnum
    name: str
    version: str
    description: str
    system_prompt: str
    user_prompt_template: str
    required_variables: List[str]
    last_updated: datetime = field(default_factory=datetime.now(timezone.utc))

