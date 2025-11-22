"""
classification_controller.py
============================

This module defines the ClassificationController, the orchestration layer for the
“Classification” management tab in the app.

Role in architecture:
---------------------
- Sits between Gradio views and domain/services.
- Owns UI-driven control flow and selection rules.
- Delegates all persistence and business rules to ClassificationService.
- Delegates all domain <-> view model translation to ClassificationMapper.
- Never performs file I/O directly and never renders UI itself.

Main responsibilities:
----------------------
1) Initial render
   - Load all ClassificationGroups from the service.
   - Map them into:
       * ClassificationGroupListViewModel for the dropdown.
       * ClassificationGroupDetailViewModel for the editor.
       * ClassificationViewModel for the selected classification.
   - Build a full ClassificationTabViewModel.
   - Pass callback functions into ClassificationView.render_classification_view(...).

2) Group-level callbacks
   - on_group_changed: load one group, map to detail VM.
   - on_save_group_clicked: create/rename/save group via service, then rebuild full tab VM.
   - on_group_delete_clicked: delete group via service, then rebuild full tab VM.

3) Classification-level callbacks
   - on_classification_clicked: load one classification, map to ClassificationViewModel.
   - on_save_classification_clicked: create/update/rename classification via service,
     reload group, map to detail VM, and set selection index.
   - on_remove_classification_clicked: delete classification via service, reload group,
     map to detail VM, and reset selection index.

4) VM rebuilding helpers
   - _build_tab_vm: given the current domain groups, apply deterministic selection
     rules and produce a fresh ClassificationTabViewModel.
   - _map_group_list_vms: lightweight mapping for dropdown contents.

Important boundaries (what this module must NOT do):
----------------------------------------------------
- Must not validate deep business logic (service does that).
- Must not read/write storage (service/repo does that).
- Must not contain Gradio layout code (view does that).
- Must not contain mapping rules (mapper does that).

Selection rules encoded here:
-----------------------------
- If a requested selected_group_name exists, select it; otherwise select first group.
- If a requested selected_classification_name exists in selected group, select it;
  otherwise select first classification.
- After saving a classification, attempt to reselect it by name.
- After deleting a classification, default to index 0 if any remain, else -1.

Assumptions / possible failure points:
--------------------------------------
- Service methods may raise exceptions; group save/delete paths catch some of them,
  but classification save/delete paths currently assume service-level correctness
  and do not catch errors.
- Names are treated as unique identifiers; if duplicates exist on disk, selection
  may be ambiguous.
- The view handles CREATE_SENTINEL filtering; sentinels should never reach controller.
- Mapper is assumed to return correct Enum types; if UI passes plain strings and the
  controller doesn’t normalize them before mapping back, domain objects may contain
  wrong types.

In short:
---------
This file is the “traffic cop” for classification management:
it decides *what happens next* based on user actions, but delegates
*how to store data* and *how to translate models* to other layers.
"""

from __future__ import annotations

from typing import List, Optional

from models.view_models.classification import ClassificationTabViewModel, ClassificationGroupListViewModel, ClassificationGroupDetailViewModel, ClassificationViewModel
from models.domain import ClassificationGroup
from views.classification_view import ClassificationView
from services.classification_service import ClassificationService
from mappers.classification_mapper import ClassificationMapper


##################################################################
class ClassificationController:
    """Controller for the entire 'Classification' management tab."""

    # ----------------------------------------------------------------
    def __init__(self):
        self.classification_service = ClassificationService()
        self.classification_view = ClassificationView()
        self.mapper = ClassificationMapper()

    # ================================================================
    # Entry point
    # ================================================================
    def render_classification_view(self) -> None:
        """
        Initial entry point.

        Loads all groups from service, builds the initial ClassificationTabViewModel,
        defines callback signatures (WITHOUT implementation),
        and renders the Gradio view.

        IMPORTANT:
            Only this initial render passes a full ClassificationTabViewModel.
            Most callbacks return smaller VMs.
        """

        # ============================================================
        # 1) LOAD DOMAIN GROUPS
        # ============================================================
        domain_groups = self.classification_service.load_all_classification_groups()

        # ============================================================
        # 2) MAP DOMAIN -> LIST + DETAIL VMS
        # ============================================================
        group_list_vms: List[ClassificationGroupListViewModel] = [
            self.mapper.classification_group_to_classification_group_list_view_model(g)
            for g in (domain_groups or [])
        ]

        selected_group_detail_vm: Optional[ClassificationGroupDetailViewModel] = (
            self.mapper.classification_group_to_classification_group_detail_view_model(
                domain_groups[0]
            )
            if domain_groups
            else None
        )

        selected_class_vm: Optional[ClassificationViewModel] = (
            selected_group_detail_vm.classifications[0]
            if selected_group_detail_vm and selected_group_detail_vm.classifications
            else None
        )

        # ============================================================
        # 3) BUILD TAB VM (YOUR SHAPE)
        # ============================================================
        tab_vm = ClassificationTabViewModel(
            group_contents=group_list_vms,
            selected_group=selected_group_detail_vm,
            selected_classification=selected_class_vm,
            info_message=None,
            error_message=None,
        )

        # ============================================================
        # 5) RENDER VIEW
        # ============================================================
        self.classification_view.render_classification_view(
            view_model=tab_vm,

            # group-level
            on_group_changed=self.on_group_changed,
            on_save_group_clicked=self.on_save_group_clicked,
            on_group_delete_clicked=self.on_group_delete_clicked,

            # classification-level
            on_classification_clicked=self.on_classification_clicked,
            on_save_classification_clicked=self.on_save_classification_clicked,
            on_remove_classification_clicked=self.on_remove_classification_clicked,
        )

    # ================================================================
    # Callback method heads (NO implementation yet)
    # ================================================================
    # ----------------------------------------------------------------
    def on_group_changed(
        self,
        group_name: str,
    ) -> Optional[ClassificationGroupDetailViewModel]:
        """
        Return ClassificationGroupDetailViewModel for the selected group.

        - If no group selected (empty string / None), return None.
        - Otherwise load domain group, map to detail VM, return it.

        Note:
            The CREATE_SENTINEL is handled in the view, so it does not reach here.
        """
        # No group selected
        if not group_name:
            return None

        name = group_name.strip()

        # Load and return selected group
        domain_group = self.classification_service.load_classification_group(name)
        return self.mapper.classification_group_to_classification_group_detail_view_model(
            domain_group
        )

    # ----------------------------------------------------------------
    def on_save_group_clicked(
        self,
        original_group_name: Optional[str],
        edited_group_name: str,
    ) -> ClassificationTabViewModel:
        """
        Save group header.

        Args:
            original_group_name:
                The group selected in the dropdown BEFORE editing.
                None if create-mode (sentinel handled in view).
            edited_group_name:
                Textbox value for the group name.

        Returns:
            Fresh ClassificationTabViewModel built from reloaded domain state.
        """
        edited = (edited_group_name or "").strip()

        # ----------------------------
        # CASE A: CREATE NEW GROUP
        # ----------------------------
        if original_group_name is None:
            if not edited:
                return self._build_tab_vm(
                    self.classification_service.load_all_classification_groups(),
                    error_message="Group name cannot be empty.",
                )

            try:
                self.classification_service.create_classification_group(edited)
                domain_groups = self.classification_service.load_all_classification_groups()
                return self._build_tab_vm(
                    domain_groups,
                    selected_group_name=edited,
                    info_message=f"Group '{edited}' created.",
                )
            except Exception as exc:
                domain_groups = self.classification_service.load_all_classification_groups()
                return self._build_tab_vm(
                    domain_groups,
                    selected_group_name=None,
                    error_message=str(exc),
                )

        original = original_group_name.strip()

        # ----------------------------
        # CASE B: RENAME GROUP
        # ----------------------------
        if original != edited:
            if not edited:
                domain_groups = self.classification_service.load_all_classification_groups()
                return self._build_tab_vm(
                    domain_groups,
                    selected_group_name=original,
                    error_message="New group name cannot be empty.",
                )

            try:
                self.classification_service.rename_classification_group(original, edited)
                domain_groups = self.classification_service.load_all_classification_groups()
                return self._build_tab_vm(
                    domain_groups,
                    selected_group_name=edited,
                    info_message=f"Group renamed to '{edited}'.",
                )
            except Exception as exc:
                domain_groups = self.classification_service.load_all_classification_groups()
                return self._build_tab_vm(
                    domain_groups,
                    selected_group_name=original,
                    error_message=str(exc),
                )

        # ----------------------------
        # CASE C: NO RENAME
        # ----------------------------
        domain_groups = self.classification_service.load_all_classification_groups()
        return self._build_tab_vm(
            domain_groups,
            selected_group_name=original,
            info_message="Group saved.",
        )

    # ----------------------------------------------------------------
    def on_group_delete_clicked(self, group_name: str) -> ClassificationTabViewModel:
        """
        Delete a classification group.

        Responsibilities:
        - Validate the input group name
        - Ensure the group actually exists
        - Delegate deletion to the service
        - Reload all groups after deletion
        - Pick a new selected group (first in list)
        - Return a fresh ClassificationTabViewModel
        """
        name = (group_name or "").strip()

        # ------------------------------------------
        # 1) Validate
        # ------------------------------------------
        if not name:
            domain_groups = self.classification_service.load_all_classification_groups()
            return self._build_tab_vm(
                domain_groups,
                selected_group_name=None,
                error_message="No group selected for deletion.",
            )

        existing = self.classification_service.list_classification_group_names()
        if name not in existing:
            domain_groups = self.classification_service.load_all_classification_groups()
            return self._build_tab_vm(
                domain_groups,
                selected_group_name=None,
                error_message=f"Group '{name}' does not exist.",
            )

        # ------------------------------------------
        # 2) Delete group (service → repo)
        # ------------------------------------------
        try:
            self.classification_service.delete_classification_group(name)
        except Exception as exc:
            domain_groups = self.classification_service.load_all_classification_groups()
            return self._build_tab_vm(
                domain_groups,
                selected_group_name=name,
                error_message=str(exc),
            )

        # ------------------------------------------
        # 3) Reload domain groups
        # ------------------------------------------
        domain_groups = self.classification_service.load_all_classification_groups()

        # ------------------------------------------
        # 4) Choose new selected group
        #     (first in alphabetical order — consistent UX)
        # ------------------------------------------
        new_selected = domain_groups[0].name if domain_groups else None

        # ------------------------------------------
        # 5) Build & return updated tab VM
        # ------------------------------------------
        return self._build_tab_vm(
            domain_groups,
            selected_group_name=new_selected,
            info_message=f"Group '{name}' deleted.",
        )

    # ----------------------------------------------------------------
    def on_classification_clicked(
        self,
        group_name: str,
        classification_name: str,
    ) -> ClassificationViewModel:
        """
        Return ClassificationViewModel for (group_name, classification_name).

        Flow:
        1) If input missing → return empty ClassificationViewModel (view clears editor).
        2) Load domain Classification from service.
        3) Map domain -> ClassificationViewModel.
        4) Return it.

        Note:
            CREATE sentinels are handled in the view and must not reach here.
        """

        # 1) Guard: nothing selected
        if not group_name or not classification_name:
            return ClassificationViewModel()

        gname = group_name.strip()
        cname = classification_name.strip()

        if not gname or not cname:
            return ClassificationViewModel()

        # 2) Load domain classification (service owns persistence)
        domain_c = self.classification_service.load_classification(gname, cname)

        # 3) Map to VM
        return self.mapper.classification_to_classification_view_model(domain_c)

    # ----------------------------------------------------------------
    def on_save_classification_clicked(
        self,
        group_name: str,
        class_vm: ClassificationViewModel,
    ) -> ClassificationGroupDetailViewModel:
        """
        Save (create/update/rename) a classification inside a group.

        Logic:
        - Determine if this is CREATE or UPDATE or RENAME.
        - Apply the appropriate repo operations via service.
        - Reload the updated group.
        - Return a fresh ClassificationGroupDetailViewModel.
        """

        gname = (group_name or "").strip()
        if not gname:
            # Invalid state; return empty detail VM
            return ClassificationGroupDetailViewModel(name="", classifications=[])

        new_name = (class_vm.name or "").strip()
        old_name = class_vm.original_name.strip() if class_vm.original_name else None

        # 1) Build domain object from VM
        domain_c = self.mapper.classification_view_model_to_classification(class_vm)

        print("DEBUB SAVE CLASS in CONTROLLER", gname, "orig=", class_vm.original_name, "new=", class_vm.name)
        # 2) Let service decide CREATE / UPDATE / RENAME+UPDATE
        self.classification_service.save_classification(
            gname,
            old_name,
            domain_c,
        )
        # 3) Reload group
        updated_group = self.classification_service.load_classification_group(gname)

        # 4) Map back to detail VM and fix selection index
        detail_vm = self.mapper.classification_group_to_classification_group_detail_view_model(
            updated_group
        )

        # Find the index of the saved classification and select it
        for i, c_vm in enumerate(detail_vm.classifications):
            if c_vm.name == new_name:
                detail_vm.selected_index = i
                break

        return detail_vm

    # ----------------------------------------------------------------
    def on_remove_classification_clicked(
        self,
        group_name: str,
        classification_name: str,
    ) -> ClassificationGroupDetailViewModel:
        """
        Delete a classification inside a group.

        Responsibilities:
        - validate minimal inputs
        - call service.delete_classification
        - reload group from disk
        - map to ClassificationGroupDetailViewModel
        - fix selected_index (default = 0)
        """

        gname = (group_name or "").strip()
        cname = (classification_name or "").strip()

        if not gname:
            return ClassificationGroupDetailViewModel(name="", classifications=[])

        if not cname:
            # Nothing to delete → just reload group
            updated_group = self.classification_service.load_classification_group(gname)
            return self.mapper.classification_group_to_classification_group_detail_view_model(
                updated_group
            )

        # 1) Delete at service-level (service does business checks)
        self.classification_service.delete_classification(gname, cname)

        # 2) Reload group
        updated_group = self.classification_service.load_classification_group(gname)

        # 3) Map domain → VM
        detail_vm = self.mapper.classification_group_to_classification_group_detail_view_model(
            updated_group
        )

        # 4) Fix selection:
        # always select index 0 unless empty
        if detail_vm.classifications:
            detail_vm.selected_index = 0
        else:
            detail_vm.selected_index = -1  # view can interpret this as "none selected"

        return detail_vm

    # ================================================================
    # VM builders
    # ================================================================
    def _build_tab_vm(
        self,
        domain_groups: Optional[List[ClassificationGroup]],
        *,
        selected_group_name: Optional[str] = None,
        selected_classification_name: Optional[str] = None,
        info_message: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> ClassificationTabViewModel:
        """
        Build a full ClassificationTabViewModel from current domain state.

        Selection rules:
        1) If selected_group_name is given and exists -> select it
        2) Else select first group (if any)
        3) If selected_classification_name is given and exists in that group -> select it
        4) Else select first classification in the selected group (if any)

        Args:
            domain_groups:
                Full list of domain ClassificationGroups (may be empty / None).
            selected_group_name:
                Optional group name to select.
            selected_classification_name:
                Optional classification name to select.
            info_message / error_message:
                Optional page-level feedback.

        Returns:
            ClassificationTabViewModel for rendering.
        """
        groups = domain_groups or []

        group_list_vms = self._map_group_list_vms(groups)

        # -----------------------------
        # choose selected group (domain)
        # -----------------------------
        selected_group_domain: Optional[ClassificationGroup] = None
        if selected_group_name:
            for g in groups:
                if g.name == selected_group_name:
                    selected_group_domain = g
                    break

        if selected_group_domain is None and groups:
            selected_group_domain = groups[0]

        # -----------------------------
        # map selected group to detail VM
        # -----------------------------
        selected_group_detail_vm: Optional[ClassificationGroupDetailViewModel] = (
            self.mapper.classification_group_to_classification_group_detail_view_model(
                selected_group_domain
            )
            if selected_group_domain
            else None
        )

        # -----------------------------
        # choose selected classification VM
        # -----------------------------
        selected_class_vm: Optional[ClassificationViewModel] = None
        if selected_group_detail_vm and selected_group_detail_vm.classifications:
            if selected_classification_name:
                for c in selected_group_detail_vm.classifications:
                    if c.name == selected_classification_name:
                        selected_class_vm = c
                        break

            if selected_class_vm is None:
                selected_class_vm = selected_group_detail_vm.classifications[0]

        return ClassificationTabViewModel(
            group_contents=group_list_vms,
            selected_group=selected_group_detail_vm,
            selected_classification=selected_class_vm,
            info_message=info_message,
            error_message=error_message
        )

    # ----------------------------------------------------------------
    def _map_group_list_vms(
        self,
        domain_groups: List[ClassificationGroup],
    ) -> List[ClassificationGroupListViewModel]:
        """
        Map domain groups into list VMs for the top dropdown.
        """
        return [
            self.mapper.classification_group_to_classification_group_list_view_model(g)
            for g in domain_groups
        ]

    # ----------------------------------------------------------------
