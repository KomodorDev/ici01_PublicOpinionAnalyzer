"""
classification_mapper.py
========================

This module contains the ClassificationMapper class, which is responsible for
converting between:

1) Domain models (business/data layer)
   - Classification
   - ClassificationGroup

2) View models (UI layer)
   - ClassificationViewModel
   - ClassificationGroupDetailViewModel
   - ClassificationGroupListViewModel

What this mapper MUST do:
-------------------------
- Take domain objects as input.
- Return view models as output (or domain objects when mapping back).
- Fill missing optional fields with safe UI defaults ("" / False / [] / {}).
- Convert list-based fields into multiline textbox strings and back.

What this mapper MUST NOT do:
-----------------------------
- Call services.
- Read or write files/databases.
- Validate correctness/business rules.
- Contain UI wiring logic (that belongs in the view).

Why this module exists:
-----------------------
The controller should not manually build UI models field-by-field.
If mapping rules ever change (e.g., categories formatting),
you edit them in exactly one place: here.

Key mapping rules used here:
----------------------------
Classification -> ClassificationViewModel
- categories: List[str]  -> categories_text: "cat1\\ncat2\\n..."
- indicators: Dict[str, List[str]]
    -> indicators_text_by_cat: Dict[str, str]
       where each category maps to a multiline string of indicators.

ClassificationViewModel -> Classification
- categories_text split by newline into categories list.
- indicators_text_by_cat multiline strings split back into per-category lists.
- output_type is preserved as-is (assumed to already be the correct Enum).

Potential failure points / assumptions:
---------------------------------------
- The view model's output_type is assumed to already be a valid Enum instance.
  If the UI passes plain strings and the controller does NOT convert them,
  this mapper will return a domain object with the wrong type.
- indicators_text_by_cat is assumed to contain keys matching categories.
  If the UI sends indicators for categories not listed in categories_text,
  those extra indicators are ignored.
- Ordering is driven by the categories list. If category order matters,
  the UI must preserve it when editing categories_text.

In short:
---------
This file is a "dumb translator" between domain and UI objects.
All real logic (validation, persistence, selection) belongs elsewhere.
"""

from __future__ import annotations

from typing import Dict, List

from models.domain.classification_model import Classification
from models.domain.classification_group_model import ClassificationGroup
from models.view_models.classification.classification_group_list_view_model import ClassificationGroupListViewModel
from models.view_models.classification.classification_view_model import ClassificationViewModel
from models.view_models.classification.classification_group_detail_view_model import (
    ClassificationGroupDetailViewModel,
)


##################################################################
class ClassificationMapper:
    """
    Pure mapping helpers for ClassificationController.

    These methods:
    - take domain objects
    - output view models
    - do NOT call services themselves
    - do NOT perform persistence or validation

    Important:
        This mapper only maps domain -> view models.
        The controller can decide if / how to map back.
    """

    # ================================================================
    # Classification -> ClassificationViewModel
    # ================================================================
    def classification_to_classification_view_model(
        self,
        c: Classification,
    ) -> ClassificationViewModel:
        """
        Map a single Classification domain object into a UI-friendly
        ClassificationViewModel.

        UI decisions:
        - Optionals become concrete defaults ("" / False / [] / {}).
        - output_type stays as Enum (closed set, same as other VMs).
        - categories_text is derived for the multiline textbox.
        - indicators_text_by_cat is derived for dynamic indicator textboxes.
        """
        categories: List[str] = c.categories or []
        indicators: Dict[str, List[str]] = c.indicators or {}

        # Multiline textbox content: one category per line
        categories_text = "\n".join(categories)

        # Dynamic UI needs one multiline textbox per category.
        # Each textbox contains one indicator per line.
        indicators_text_by_cat = {
            cat: "\n".join(indicators.get(cat, []))
            for cat in categories
        }

        return ClassificationViewModel(
            # Core metadata
            name=c.name or "",
            original_name=c.name or "",
            question=c.question or "",
            explanation=c.explanation or "",
            # Enum stays Enum
            output_type=c.output_type,
            # Config
            allow_multiple=bool(c.allow_multiple)
            if c.allow_multiple is not None
            else False,
            require_llm_explanation=bool(c.require_llm_explanation),
            # UI helpers
            categories_text=categories_text,
            indicators_text_by_cat=indicators_text_by_cat,
        )

    # ================================================================
    # ClassificationGroup -> ClassificationGroupDetailViewModel
    # ================================================================
    def classification_group_to_classification_group_detail_view_model(
        self,
        g: ClassificationGroup,
    ) -> ClassificationGroupDetailViewModel:
        """
        Map a ClassificationGroup domain object into a UI-friendly
        ClassificationGroupViewModel.

        UI decisions:
        - name is always a concrete string.
        - each child Classification is mapped using the helper above.
        - selected_index defaults to 0 (controller may overwrite).
        """
        child_vms: List[ClassificationViewModel] = [
            self.classification_to_classification_view_model(c)
            for c in (g.classifications or [])
        ]

        return ClassificationGroupDetailViewModel(
            name=g.name or "",
            classifications=child_vms,
            selected_index=0,
        )

    # ================================================================
    # ClassificationGroup -> ClassificationGroupListViewModel
    # ================================================================
    def classification_group_to_classification_group_list_view_model(
        self,
        g: ClassificationGroup,
    ) -> ClassificationGroupListViewModel:
        """
        Map a ClassificationGroup domain object into a lightweight
        ClassificationGroupListViewModel for the sidebar / dropdown.

        Contains:
          - name
          - number of child classifications
          - maybe more later (icons, sorting order, etc.)
        """
        return ClassificationGroupListViewModel(
            name=g.name or "",
            classification_count=len(g.classifications or []),
        )

    def classification_view_model_to_classification(
        self,
        vm: ClassificationViewModel,
    ) -> Classification:
        """
        Convert a ClassificationViewModel back into a Classification domain object.

        - Split categories_text into a list
        - Split indicators_text_by_cat into dict of lists
        - Preserve output_type (Enum)
        - Preserve allow_multiple, require_llm_explanation
        - vm.name is the *new* name user entered
        """
        # Categories: one per line
        categories = []
        if vm.categories_text:
            categories = [
                line.strip()
                for line in vm.categories_text.split("\n")
                if line.strip()
            ]

        # Indicators: each value is multiline string -> list of indicators
        indicators = {}
        for cat in categories:
            block = vm.indicators_text_by_cat.get(cat, "")
            indicators[cat] = [
                line.strip()
                for line in block.split("\n")
                if line.strip()
            ]

        return Classification(
            name=vm.name.strip(),
            question=vm.question.strip(),
            explanation=vm.explanation.strip(),
            output_type=vm.output_type,
            allow_multiple=vm.allow_multiple,
            require_llm_explanation=vm.require_llm_explanation,
            categories=categories,
            indicators=indicators,
        )


    # ================================================================
    # Bulk helpers (optional but convenient)
    # ================================================================
    def classification_groups_to_classification_group_detail_view_models(
        self,
        groups: List[ClassificationGroup],
    ) -> List[ClassificationGroupDetailViewModel]:
        """
        Map a list of ClassificationGroup domain objects into a list of
        ClassificationGroupDetailViewModel objects.

        Useful for populating dropdowns / sidebars in one go.
        """
        return [self.classification_group_to_classification_group_detail_view_model(g) for g in groups]

    def classifications_to_classification_view_models(
        self,
        classifications: List[Classification],
    ) -> List[ClassificationViewModel]:
        """
        Map a list of Classification domain objects into a list of
        ClassificationViewModel objects.
        """
        return [self.classification_to_classification_view_model(c) for c in classifications]

##################################################################
