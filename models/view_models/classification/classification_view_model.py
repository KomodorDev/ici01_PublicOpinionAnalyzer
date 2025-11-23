"""
classification_view_model.py
============================

Pure UI-facing representation of a `Classification`.

This ViewModel is designed specifically for Gradio:
- It avoids Optional types.
- It stores enums in a UI-friendly manner (same pattern as other VMs).
- It provides helper fields (`categories_text`, `indicators_text_by_cat`)
  required for the dynamic categorical UI.

IMPORTANT:
    The controller is responsible for mapping between domain models
    (`Classification`) and this ViewModel. This object should contain ONLY
    UI-safe values ready to plug directly into Gradio widgets.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

from enums.classification_output_enum import ClassificationOutputEnum


@dataclass
class ClassificationViewModel:
    """
    UI ViewModel for editing and displaying a single Classification.

    This ViewModel intentionally mirrors only the parts needed for UI editing.
    It does NOT perform domain-to-view or view-to-domain conversions — that is
    handled by the controller.

    Core principles:
        - All fields use concrete values (no Optional).
        - Enums are allowed for closed-set choices (output_type).
        - User-defined values (categories, indicators) remain plain strings.
        - UI helper fields exist to support dynamic Gradio components.
    """

    # ---------------------------------------------------------------------
    # Basic classification metadata
    # ---------------------------------------------------------------------
    name: str = ""
    """
    The internal name/identifier for this classification.
    Edited via a simple textbox in the UI.
    """

    original_name: Optional[str] = None

    question: str = ""
    """
    The actual classification prompt/question (e.g. "Is the comment pro-Taiwan?").
    """

    explanation: str = ""
    """
    Additional human-readable instructions for the annotation/model.
    Empty string means "no explanation".
    """

    # ---------------------------------------------------------------------
    # Output configuration
    # ---------------------------------------------------------------------
    output_type: ClassificationOutputEnum = ClassificationOutputEnum.CATEGORICAL
    """
    The output type of the classification.
    Stored as an Enum to match how other ViewModels use enums (e.g., SortByEnum).
    The controller will pass this enum directly into a Gradio Dropdown as a choice.
    """

    allow_multiple: bool = False
    """
    Whether the classification allows selecting multiple categories
    (only relevant if output_type == CATEGORICAL).
    """

    require_llm_explanation: bool = False
    """
    Whether the LLM must produce an explanation for its label.
    Bound to a simple checkbox in the UI.
    """

    # ---------------------------------------------------------------------
    # Categorical configuration (UI-facing)
    # ---------------------------------------------------------------------
    categories_text: str = ""
    """
    Multiline textbox content representing categories.

    The UI shows a textbox where each category is on its own line.
    Controller parses this into a `List[str]` for the domain model.
    Example value:
        "Pro Taiwan\nNeutral\nAnti Taiwan"
    """

    indicators_text_by_cat: Dict[str, str] = field(default_factory=dict)
    """
    Per-category indicator phrases, each expressed as multiline text.

    Key:
        category name (string)
    Value:
        multiline string, each line is one indicator phrase.

    Example:
        {
            "Pro Taiwan": "supports democracy\npositive about Taiwan\nmentions freedom",
            "Anti Taiwan": "pro-China wording\ncriticizes Taiwan\nmentions reunification"
        }

    The dynamic UI generates one textbox per category, and each textbox
    writes into this dict. The controller later parses the multiline strings
    into `List[str]` for the domain model.
    """
