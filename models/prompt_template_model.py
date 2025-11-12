"""
prompt_model.py
===============

Data model for prompt templates used in LLM-driven classification workflows.

This module defines the `PromptTemplate` dataclass, representing a single
prompt configuration (system + user prompt pair) associated with a specific
content platform such as YouTube, Twitter, or Reddit.

The class provides serialization helpers (`to_dict()` / `from_dict()`)
to facilitate saving/loading templates as JSON files and passing them
through controller/service layers as neutral Python dictionaries.

Typical usage example::

    from models.prompt_model import PromptTemplate
    from enums.platform_enum import PlatformEnum
    from datetime import datetime, timezone

    # Create a new template
    tpl = PromptTemplate(
        platform=PlatformEnum.YOUTUBE,
        name="Sentiment Classification",
        version="1.0",
        description="Classifies comment sentiment into positive/neutral/negative.",
        system_prompt="You are a sentiment analysis assistant...",
        user_prompt="Classify the following comment: {comment}",
    )

    # Serialize to dict for saving
    data = tpl.to_dict()

    # Reconstruct from dict
    tpl2 = PromptTemplate.from_dict(data)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enums.platform_enum import PlatformEnum


@dataclass
class PromptTemplate:
    """
    Represents a single LLM prompt template in the application's domain model.

    Each template defines both the *system prompt* (the persistent instruction set
    describing model behavior) and the *user prompt* (a variable template for runtime
    substitution). Templates are versioned and platform-specific, enabling reuse
    across multiple content platforms.

    Attributes:
        platform (PlatformEnum): Platform for which the template applies
            (e.g., `PlatformEnum.YOUTUBE`).
        name (str): Human-readable name of the template.
        version (str): Version identifier of the template (e.g., "1.0").
        description (str): Short description explaining the template’s purpose.
        system_prompt (str): Instructional system message defining model behavior.
        user_prompt (str): User-facing prompt template
        last_updated (datetime): Timestamp of last modification in UTC.

    Methods:
        to_dict() -> dict:
            Serialize this template into a neutral, JSON-compatible dictionary.
        from_dict(d: dict) -> PromptTemplate:
            Deserialize a dictionary (e.g. loaded from JSON) into a
            `PromptTemplate` instance.
    """
    platform: PlatformEnum
    name: str
    version: str
    description: str
    system_prompt: str
    user_prompt: str
    last_updated: datetime = field(default_factory=datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """
        Serialize the prompt template into a neutral Python dictionary.

        Returns:
            dict: A machine-readable representation of this prompt template,
            ready for JSON serialization or repository persistence. The output

        Example output::
            {
                "name": "Sentiment Classification",
                "platform": "youtube",
                "version": "1.0",
                "description": "Classifies comment sentiment.",
                "system_prompt": "You are a sentiment analysis assistant...",
                "user_prompt": "Classify: {comment}",
                "last_updated": "2025-11-11T07:33:28+00:00",
            }
        """

        return {
            "name": self.name,
            "platform": self.platform.value,  # neutral, not view prettified
            "version": self.version,
            "description": self.description or "",
            "system_prompt": self.system_prompt or "",
            "user_prompt": self.user_prompt or "",
            "last_updated": self.last_updated.astimezone(timezone.utc).isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PromptTemplate":
        """
        Reconstruct a `PromptTemplate` instance from a dictionary.

        Args:
            d (dict): Dictionary representation of a prompt template,
                typically obtained via `json.load()` or `PromptTemplate.to_dict()`.

        Returns:
            PromptTemplate: A fully constructed prompt template instance.

        Notes:
            - Platform strings are case-insensitive and converted to
              `PlatformEnum` values using `PlatformEnum.from_str()`.
            - The `last_updated` field is parsed as UTC and accepts both
              ISO 8601 strings with 'Z' suffix or '+00:00' offset.
            - Missing or malformed timestamps default to the current UTC time.

        Example::
            data = {
                "platform": "youtube",
                "name": "Test",
                "version": "1.0",
                "description": "",
                "system_prompt": "...",
                "user_prompt": "...",
                "last_updated": "2025-11-11T07:33:28Z"
            }
            tpl = PromptTemplate.from_dict(data)
        """

        plat = d.get("platform")
        platform = plat if isinstance(plat, PlatformEnum) else PlatformEnum.from_str(plat)

        lu = d.get("last_updated")
        if isinstance(lu, str) and lu.endswith("Z"):
            lu = lu.replace("Z", "+00:00")
        last_updated = (
            datetime.fromisoformat(lu).astimezone(timezone.utc)
            if isinstance(lu, str) else datetime.now(timezone.utc)
        )

        return cls(
            name=d["name"],
            platform=platform,
            version=d.get("version", ""),
            description=d.get("description", ""),
            system_prompt=d.get("system_prompt", ""),
            user_prompt=d.get("user_prompt", ""),
            last_updated=last_updated,
        )
