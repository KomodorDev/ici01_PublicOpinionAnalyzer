"""
classification_view.py
=======================

This module renders the complete Gradio UI for creating, editing and deleting
Classification Groups and individual Classifications.

The UI is intentionally built in a *static layout* style:
- All input components are created once during page load.
- All dynamic behavior is implemented by updating component values/visibility
  through Gradio .update() calls.
- No components are created or destroyed after the initial render.  

Why this matters:
-----------------
Gradio re-renders the UI when the user interacts with it.  
If components were created dynamically, their references would break and the
view would lose state. This implementation avoids that problem by using a
"fixed pool" of textboxes for indicators and updating only their visibility
and content.

What the view shows:
--------------------
1. A dropdown listing all Classification Groups (+ a sentinel to create a new one).
2. A set of text fields to edit the group's name.
3. A list of classifications inside the selected group.
4. A detailed editor for a single classification:
   - name, question, explanation
   - output type (categorical / boolean / numeric / text)
   - category list (for categorical types)
   - a fixed pool of indicator textboxes (max 40), where each textbox is mapped
     to one category when visible.

How indicators work:
--------------------
Indicators cannot be created dynamically.  
Instead, this file pre-builds 40 invisible textboxes.  
When categories change, a refresh function:
- shows only the needed textboxes
- assigns correct labels (e.g. "Indicators for 'pro'")
- fills each box with its saved text from indicators_state
- hides the unused boxes

This avoids all "component not found" errors that Gradio causes when trying to
generate widgets dynamically.

Internal state:
---------------
The UI maintains several gr.State objects:
- old_group_name_state: remembers original group name for rename detection
- old_class_name_state: remembers original classification name
- categories_state: the parsed list of category strings
- indicators_state: dict mapping category -> indicators text
- indicator_keys_state: order of categories mapped to the fixed indicator pool

All handlers always update these state objects explicitly.  
Any mismatch between the number of returned outputs and the number of expected
outputs will break the UI, so every callback must return the exact number
of outputs the wiring expects.

Where things can go wrong:
--------------------------
- If a handler returns fewer outputs than declared in .change()/.click(),
  Gradio will silently inject Nones and the indicators will stop updating.
- If the category list is inconsistent with indicators_state, the mapping
  between categories and indicator textboxes will fail.
- If indicator_keys_state is not updated whenever categories_state changes,
  typing in indicator boxes will write to the wrong category.
- If output_type != "categorical", the indicators must be hidden; forgetting
  to trigger _refresh_indicator_boxes() leads to leftover visible boxes.

This file provides the view only. All persistence, validation and actual
business logic happen in the controller layer via:
- on_group_changed
- on_save_group_clicked
- on_group_delete_clicked
- on_classification_clicked
- on_save_classification_clicked
- on_remove_classification_clicked

These callbacks return view models (ClassificationGroupDetailViewModel,
ClassificationViewModel) which the view then reflects into the UI.

Always keep wiring strict and consistent – this UI is extremely sensitive
to the number and order of outputs.
"""


from __future__ import annotations

from typing import Callable, List, Optional
import gradio as gr

from models.view_models.classification.classification_group_detail_view_model import (
    ClassificationGroupDetailViewModel,
)
from models.view_models.classification.classification_view_model import (
    ClassificationViewModel,
)

from enums.classification_output_enum import ClassificationOutputEnum


class ClassificationView:
    """
    Gradio view for creating/editing ClassificationGroups and their Classifications.

    Style:
    - Layout first
    - Then handler function heads
    - Then wiring
    """

    # ================================================================
    # ENTRY POINT
    # ================================================================
    def render_classification_view(
        self,
        *,
        view_model,  # ClassificationTabViewModel
        # group-level callbacks
        on_group_changed: Callable[[str], ClassificationGroupDetailViewModel],
        on_save_group_clicked: Callable[[str, str], object],  # old_name, new_name
        on_group_delete_clicked: Callable[[str], object],
        # classification-level callbacks
        on_classification_clicked: Callable[
            [str, str], object
        ],  # group_name, classification_name
        on_save_classification_clicked: Callable[
            [str, ClassificationViewModel], ClassificationGroupDetailViewModel
        ],
        on_remove_classification_clicked: Callable[
            [str, str], ClassificationGroupDetailViewModel
        ],
    ) -> None:
        """
        Render Classification management view.
        """

        # -----------------------------
        # Local helpers for dynamic UI
        # -----------------------------
        def _norm_out_type(x):
            # supports enums or plain strings
            return getattr(x, "value", x)

        def _parse_categories(text: str) -> List[str]:
            return [c.strip() for c in (text or "").split("\n") if c.strip()]

        def _sync_categorical_ui(out_type):
            is_cat = (
                _norm_out_type(out_type) == ClassificationOutputEnum.CATEGORICAL.value
            )

            categories_vis = gr.update(visible=is_cat)
            categories_val = gr.skip()  # <-- NO CLEARING

            allow_mult_vis = gr.update(visible=is_cat)
            allow_mult_val = gr.skip()  # <-- NO RESET

            return categories_vis, categories_val, allow_mult_vis, allow_mult_val

        def _on_categories_change(text: str):
            return _parse_categories(text)

        # Maps "radio label" -> classification name
        classification_index: dict[str, str] = {}

        # indicator_boxes: Dict[str, gr.Textbox] = {}

        GROUP_CREATE_SENTINEL = "➕ Create new group…"
        CLASS_CREATE_SENTINEL = "➕ Add new classification…"

        # ---------------------------------------------------------
        def _build_class_radio(detail_vm: Optional[ClassificationGroupDetailViewModel]):
            """
            Build radio labels + update classification_index mapping.
            Returns (choices, value).
            """
            class_labels: List[str] = []
            classification_index.clear()

            if detail_vm and detail_vm.classifications:
                for c in detail_vm.classifications:
                    q = (c.question or "").strip()
                    short_q = (q[:40] + "…") if len(q) > 40 else q
                    label = f"{c.name} — {short_q}".strip(" —")
                    class_labels.append(label)
                    classification_index[label] = c.name

            choices = [CLASS_CREATE_SENTINEL] + class_labels
            value = class_labels[0] if class_labels else None
            return choices, value

        # ---------------------------------------------------------
        def _fields_to_class_vm(
            name: str,
            original_name: str,
            question: str,
            explanation: str,
            out_type: str,
            allow_multiple: bool,
            require_expl: bool,
            categories_text: str,
            indicators_by_cat_vals: List[str],
            cats: List[str],
        ) -> ClassificationViewModel:
            """
            Convert UI fields into a ClassificationViewModel.
            indicators_by_cat_vals is aligned with cats order.
            """
            indicators_text_by_cat = {
                cat: (
                    indicators_by_cat_vals[i] if i < len(indicators_by_cat_vals) else ""
                )
                for i, cat in enumerate(cats)
            }

            return ClassificationViewModel(
                name=(name or "").strip(),
                original_name=(original_name or "").strip(),
                question=question or "",
                explanation=explanation or "",
                output_type=out_type,  # controller/mapper will convert to enum
                allow_multiple=bool(allow_multiple),
                require_llm_explanation=bool(require_expl),
                categories_text=categories_text or "",
                indicators_text_by_cat=indicators_text_by_cat,
            )

        # ================================================================
        # INITIAL VM NORMALIZATION (for correct initial visibility)
        # ================================================================
        selected_group_vm: Optional[ClassificationGroupDetailViewModel] = getattr(
            view_model, "selected_group", None
        )
        selected_class_vm: Optional[ClassificationViewModel] = getattr(
            view_model, "selected_classification", None
        )

        initial_out_type = (
            _norm_out_type(selected_class_vm.output_type)
            if selected_class_vm and selected_class_vm.output_type
            else ClassificationOutputEnum.CATEGORICAL.value
        )
        initial_is_cat = initial_out_type == ClassificationOutputEnum.CATEGORICAL.value
        initial_categories = (
            _parse_categories(selected_class_vm.categories_text)
            if (selected_class_vm and initial_is_cat)
            else []
        )

        # ================================================================
        # LAYOUT
        # ================================================================
        with gr.Column():

            # ---------------------------------------------------------
            # 1) TOP BAR: group dropdown (includes CREATE sentinel)
            # ---------------------------------------------------------
            group_choices: List[str] = []
            if getattr(view_model, "group_contents", None):
                group_choices = [g.name for g in view_model.group_contents]
            group_choices_with_create = [GROUP_CREATE_SENTINEL] + group_choices

            selected_group_name = selected_group_vm.name if selected_group_vm else None
            if selected_group_name not in group_choices:
                selected_group_name = None

            group_dd = gr.Dropdown(
                label="Classification Group",
                choices=group_choices_with_create,
                value=selected_group_name,
                interactive=True,
            )

            # ---------------------------------------------------------
            # 2) GROUP NAME EDIT ROW
            # ---------------------------------------------------------
            with gr.Row():
                group_name_tb = gr.Textbox(
                    label="Group Name",
                    value=selected_group_vm.name if selected_group_vm else "",
                    interactive=True,
                )
                save_group_btn = gr.Button("Save Group", variant="primary")
                delete_group_btn = gr.Button("Delete Group", variant="stop")

            gr.Markdown("---")

            # ---------------------------------------------------------
            # 3) MAIN BODY: left classification list + right editor
            # ---------------------------------------------------------
            with gr.Row():

                # ---------------- LEFT: list of classifications ----------------
                with gr.Column(scale=1):
                    gr.Markdown("### Classifications in this group")

                    choices, value = _build_class_radio(selected_group_vm)

                    classifications_radio = gr.Radio(
                        label="Classifications",
                        choices=choices,
                        value=value,
                        interactive=True,
                    )

                # ---------------- RIGHT: classification editor ----------------
                with gr.Column(scale=3):
                    gr.Markdown("### Classification Editor")

                    class_name_tb = gr.Textbox(
                        label="Classification Name",
                        value=selected_class_vm.name if selected_class_vm else "",
                        interactive=True,
                    )

                    class_question_tb = gr.Textbox(
                        label="Question",
                        value=selected_class_vm.question if selected_class_vm else "",
                        lines=2,
                        interactive=True,
                    )

                    class_explanation_tb = gr.Textbox(
                        label="Explanation (optional)",
                        value=(
                            selected_class_vm.explanation if selected_class_vm else ""
                        ),
                        lines=3,
                        interactive=True,
                    )

                    # ✅ enum-driven choices
                    output_type_choices = [e.value for e in ClassificationOutputEnum]

                    output_type_dd = gr.Dropdown(
                        label="Output Type",
                        choices=output_type_choices,
                        value=initial_out_type,
                        interactive=True,
                    )

                    # categorical-only checkbox
                    allow_multiple_cb = gr.Checkbox(
                        label="Allow multiple categories",
                        value=(
                            selected_class_vm.allow_multiple
                            if selected_class_vm
                            else False
                        ),
                        visible=initial_is_cat,  # ✅ correct initial visibility
                        interactive=True,
                    )

                    require_expl_cb = gr.Checkbox(
                        label="Require LLM explanation",
                        value=(
                            selected_class_vm.require_llm_explanation
                            if selected_class_vm
                            else False
                        ),
                        interactive=True,
                    )

                    # categorical-only categories textbox
                    categories_tb = gr.Textbox(
                        label="Categories (one per line)",
                        value=(
                            selected_class_vm.categories_text
                            if selected_class_vm
                            else ""
                        ),
                        lines=5,
                        visible=initial_is_cat,  # ✅ correct initial visibility
                        interactive=True,
                    )

                    # -------------------------------------------------
                    # Dynamic indicators editor (one box per category)
                    # -------------------------------------------------
                    # States
                    # Remember selected group old name for rename detection
                    old_group_name_state = gr.State(selected_group_name or "")

                    # remember original_name for rename detection
                    old_class_name_state = gr.State(
                        selected_class_vm.original_name if selected_class_vm else ""
                    )

                    # ✅ initialize from current VM so indicators show on first render
                    categories_state = gr.State(initial_categories)

                    indicators_state = gr.State(
                        selected_class_vm.indicators_text_by_cat
                        if selected_class_vm
                        else {}
                    )

                    # -------------------------------------------------
                    # Stable indicators editor (fixed pool)
                    # -------------------------------------------------
                    MAX_CATS = 40  # adjust if you want more


                    initial_indicators_dict = (
                        selected_class_vm.indicators_text_by_cat
                        if (selected_class_vm and initial_is_cat)
                        else {}
                    )
                    initial_keys = initial_categories if initial_is_cat else []

                    indicator_keys_state = gr.State(initial_keys)

                    indicator_tbs: List[gr.Textbox] = []
                    gr.Markdown("#### Indicators per category")

                    for i in range(MAX_CATS):
                        if i < len(initial_keys):
                            cat = initial_keys[i]
                            tb = gr.Textbox(
                                label=f"Indicators for '{cat}' (one per line)",
                                value=initial_indicators_dict.get(cat, ""),
                                lines=3,
                                interactive=True,
                                visible=True,
                            )
                        else:
                            tb = gr.Textbox(
                                label=f"Indicators {i+1}",
                                value="",
                                lines=3,
                                interactive=True,
                                visible=False,
                            )
                        indicator_tbs.append(tb)


                    def _indicator_box_change(idx: int, text: str, keys: List[str], state: dict):
                        keys = keys or []
                        state = dict(state or {})
                        if idx < len(keys):
                            cat = keys[idx]
                            state[cat] = text
                        return state


                    for i, tb in enumerate(indicator_tbs):
                        tb.change(
                            fn=lambda text, keys, state, i=i: _indicator_box_change(i, text, keys, state),
                            inputs=[tb, indicator_keys_state, indicators_state],
                            outputs=[indicators_state],
                        )


                    def _refresh_indicator_boxes(out_type, cats, indicators_dict):
                        # non-categorical => hide everything
                        if _norm_out_type(out_type) != ClassificationOutputEnum.CATEGORICAL.value:
                            updates = [gr.update(visible=False, value="") for _ in range(MAX_CATS)]
                            return (*updates, [])

                        cats = cats or []
                        indicators_dict = indicators_dict or {}

                        updates = []
                        for i in range(MAX_CATS):
                            if i < len(cats):
                                cat = cats[i]
                                updates.append(
                                    gr.update(
                                        visible=True,
                                        label=f"Indicators for '{cat}' (one per line)",
                                        value=indicators_dict.get(cat, ""),
                                    )
                                )
                            else:
                                updates.append(gr.update(visible=False, value=""))

                        return (*updates, cats)  # last output updates indicator_keys_state



                    # ---- action buttons (STATIC) ----
                    with gr.Row():
                        save_class_btn = gr.Button(
                            "Save Classification", variant="primary"
                        )
                        remove_class_btn = gr.Button(
                            "Remove Selected Classification", variant="stop"
                        )

        # ================================================================
        # Wiring ONLY for the dynamic categorical UI
        # ================================================================

        # sync whenever output_type changes
        output_type_dd.change(  # pylint: disable=no-member
            fn=_sync_categorical_ui,
            inputs=[output_type_dd],
            outputs=[
                categories_tb,
                categories_tb,
                allow_multiple_cb,
                allow_multiple_cb,
            ],
        )

        output_type_dd.change(  # pylint: disable=no-member
            fn=_refresh_indicator_boxes,
            inputs=[output_type_dd, categories_state, indicators_state],
            outputs=[*indicator_tbs, indicator_keys_state],
        )

        # update categories_state when categories_tb changes
        categories_tb.change(  # pylint: disable=no-member
            fn=_on_categories_change,
            inputs=[categories_tb],
            outputs=[categories_state],
        )

        categories_tb.change(   # pylint: disable=no-member
            fn=_refresh_indicator_boxes,
            inputs=[output_type_dd, categories_state, indicators_state],
            outputs=[*indicator_tbs, indicator_keys_state],
        )

        classifications_radio.change(       # pylint: disable=no-member
            fn=_refresh_indicator_boxes,
            inputs=[output_type_dd, categories_state, indicators_state],
            outputs=[*indicator_tbs, indicator_keys_state],
        )

        # ================================================================
        # WIRING
        # ================================================================
        # ---------------------------------------------------------
        def _handle_group_change(group_name: str):
            """
            Dropdown changed.
            - If sentinel: enter create mode (do NOT call controller).
            - Else: ask controller for detail VM and update UI from it.
            """
            # ---------------- CREATE MODE ----------------
            if group_name == GROUP_CREATE_SENTINEL:
                empty_choices = [CLASS_CREATE_SENTINEL]

                return (
                    gr.update(value=""),  # group_name_tb
                    gr.update(
                        choices=empty_choices, value=None
                    ),  # classifications_radio
                    gr.update(interactive=False),  # delete_group_btn
                    gr.update(value=""),  # class_name_tb
                    gr.update(value=""),  # class_question_tb
                    gr.update(value=""),  # class_explanation_tb
                    gr.update(
                        value=ClassificationOutputEnum.CATEGORICAL.value
                    ),  # output_type_dd
                    gr.update(value=False),  # allow_multiple_cb
                    gr.update(value=False),  # require_expl_cb
                    gr.update(value=""),  # categories_tb
                    # States
                    "",  # old_group_name_state  (no old name in create)
                    "",  # old_class_name_state  (no old name in create)
                    [],  # categories_state
                    {},  # indicators_state
                )

            # ---------------- NORMAL SWITCH ----------------
            detail_vm = on_group_changed(group_name)
            if detail_vm is None:
                # Controller couldn't find it -> safe fallback to empty UI
                empty_choices = [CLASS_CREATE_SENTINEL]
                return (
                    gr.update(value=""),
                    gr.update(choices=empty_choices, value=None),
                    gr.update(interactive=False),   # delete_group_btn
                    gr.update(value=""),
                    gr.update(value=""),
                    gr.update(value=""),
                    gr.update(value=ClassificationOutputEnum.CATEGORICAL.value),
                    gr.update(value=False),
                    gr.update(value=False),
                    gr.update(value=""),
                    # States
                    "",  # old_group_name_state  (no old name in create)
                    "",  # old_class_name_state  (no old name in create)
                    [],  # categories_state
                    {},  # indicators_state
                )

            # pick first classification (if any) for right editor
            first_c = (
                detail_vm.classifications[0] if detail_vm.classifications else None
            )

            radio_choices, radio_value = _build_class_radio(detail_vm)

            return (
                gr.update(value=detail_vm.name),  # group_name_tb
                gr.update(
                    choices=radio_choices, value=radio_value
                ),  # classifications_radio
                gr.update(interactive=True),  # delete_group_btn
                gr.update(value=first_c.name if first_c else ""),  # class_name_tb
                gr.update(
                    value=first_c.question if first_c else ""
                ),  # class_question_tb
                gr.update(
                    value=first_c.explanation if first_c else ""
                ),  # class_explanation_tb
                gr.update(
                    value=(
                        getattr(first_c.output_type, "value", first_c.output_type)
                        if first_c
                        else ClassificationOutputEnum.CATEGORICAL.value
                    )
                ),  # output_type_dd
                gr.update(
                    value=first_c.allow_multiple if first_c else False
                ),  # allow_multiple_cb
                gr.update(
                    value=first_c.require_llm_explanation if first_c else False
                ),  # require_expl_cb
                gr.update(
                    value=first_c.categories_text if first_c else ""
                ),  # categories_tb
                # States
                detail_vm.name,  # old_group_name_state
                first_c.name if first_c else "",  # old_class_name_state
                (
                    _parse_categories(first_c.categories_text) if first_c else []
                ),  # categories_state
                first_c.indicators_text_by_cat if first_c else {},
            )

        group_dd.change(  # pylint: disable=no-member
            fn=_handle_group_change,
            inputs=[group_dd],
            outputs=[
                group_name_tb,
                classifications_radio,
                delete_group_btn,
                class_name_tb,
                class_question_tb,
                class_explanation_tb,
                output_type_dd,
                allow_multiple_cb,
                require_expl_cb,
                categories_tb,
                # States
                old_group_name_state,
                old_class_name_state,
                categories_state,
                indicators_state,
            ],
        )

        # ---------------------------------------------------------
        def _handle_save_group_clicked(
            dd_value: str,
            original_group_name: str,
            edited_group_name: str,
        ):
            """
            Save group button clicked.

            Rules (view-side):
            - If dropdown is sentinel -> CREATE (original=None)
            - Else -> UPDATE/RENAME (original=old_group_state)

            Returns explicit gr.update(...) outputs (no _apply_tab_vm).
            """

            edited_name = (edited_group_name or "").strip()

            # decide create vs rename/update
            if dd_value == GROUP_CREATE_SENTINEL:
                original_name_clean = None
            else:
                original_name_clean = (original_group_name or "").strip() or None

            # call controller
            tab_vm = on_save_group_clicked(original_name_clean, edited_name)

            # -------- rebuild dropdown choices/value from returned tab_vm --------
            new_group_choices: List[str] = []
            if getattr(tab_vm, "group_contents", None):
                new_group_choices = [g.name for g in tab_vm.group_contents]
            new_group_choices_with_create = [GROUP_CREATE_SENTINEL] + new_group_choices

            new_selected_group_vm: Optional[ClassificationGroupDetailViewModel] = (
                getattr(tab_vm, "selected_group", None)
            )
            new_selected_group_name = (
                new_selected_group_vm.name if new_selected_group_vm else None
            )

            # fallback if controller returned nothing selected
            if new_selected_group_name not in new_group_choices:
                new_selected_group_name = None
                new_selected_group_vm = None

            # -------- build left radio from selected group --------
            radio_choices, radio_value = _build_class_radio(new_selected_group_vm)

            # -------- pick first classification for right panel --------
            first_c = (
                new_selected_group_vm.classifications[0]
                if new_selected_group_vm and new_selected_group_vm.classifications
                else None
            )

            # delete enabled only if we have a real selected group
            delete_enabled = bool(new_selected_group_vm)

            return (
                # group_dd
                gr.update(
                    choices=new_group_choices_with_create,
                    value=new_selected_group_name,
                ),
                # group_name_tb
                gr.update(value=new_selected_group_name or ""),
                # classifications_radio
                gr.update(choices=radio_choices, value=radio_value),
                # delete_group_btn
                gr.update(interactive=delete_enabled),
                # class_name_tb
                gr.update(value=first_c.name if first_c else ""),
                # class_question_tb
                gr.update(value=first_c.question if first_c else ""),
                # class_explanation_tb
                gr.update(value=first_c.explanation if first_c else ""),
                # output_type_dd
                gr.update(
                    value=(
                        getattr(first_c.output_type, "value", first_c.output_type)
                        if first_c
                        else ClassificationOutputEnum.CATEGORICAL.value
                    )
                ),
                # allow_multiple_cb
                gr.update(value=first_c.allow_multiple if first_c else False),
                # require_expl_cb
                gr.update(value=first_c.require_llm_explanation if first_c else False),
                # categories_tb
                gr.update(value=first_c.categories_text if first_c else ""),
                # States
                # old_group_state (now equals the saved/selected group)
                new_selected_group_name or "",
                # old_class_state
                first_c.name if first_c else "",
                # categories_state
                _parse_categories(first_c.categories_text) if first_c else [],
            )

        save_group_btn.click(  # pylint: disable=no-member
            fn=_handle_save_group_clicked,
            inputs=[
                group_dd,
                old_group_name_state,
                group_name_tb,
            ],
            outputs=[
                group_dd,
                group_name_tb,
                classifications_radio,
                delete_group_btn,
                class_name_tb,
                class_question_tb,
                class_explanation_tb,
                output_type_dd,
                allow_multiple_cb,
                require_expl_cb,
                categories_tb,
                # States
                old_group_name_state,
                old_class_name_state,
                categories_state,
                
            ],
        )

        # ---------------------------------------------------------
        def _handle_delete_group_clicked(current_group_name: str):
            """
            User pressed 'Delete Group'.

            Controller returns a full ClassificationTabViewModel.
            We rebuild UI from it, same style as the save handler.
            """

            # call controller
            tab_vm = on_group_delete_clicked((current_group_name or "").strip())

            # -------- rebuild group dropdown --------
            new_group_choices = (
                [g.name for g in tab_vm.group_contents] if tab_vm.group_contents else []
            )
            new_group_choices_with_create = [GROUP_CREATE_SENTINEL] + new_group_choices

            new_selected_group_vm = tab_vm.selected_group
            new_selected_group_name = (
                new_selected_group_vm.name if new_selected_group_vm else None
            )

            # -------- build classification radio --------
            radio_choices, radio_value = _build_class_radio(new_selected_group_vm)

            # -------- pick classification for right editor --------
            first_c = (
                new_selected_group_vm.classifications[0]
                if new_selected_group_vm and new_selected_group_vm.classifications
                else None
            )

            delete_enabled = bool(new_selected_group_vm)

            return (
                gr.update(
                    choices=new_group_choices_with_create, value=new_selected_group_name
                ),  # group_dd
                gr.update(value=new_selected_group_name or ""),  # group_name_tb
                gr.update(
                    choices=radio_choices, value=radio_value
                ),  # classifications_radio
                gr.update(interactive=delete_enabled),  # delete_group_btn
                gr.update(value=first_c.name if first_c else ""),  # class_name_tb
                gr.update(
                    value=first_c.question if first_c else ""
                ),  # class_question_tb
                gr.update(
                    value=first_c.explanation if first_c else ""
                ),  # class_explanation_tb
                gr.update(
                    value=(
                        getattr(first_c.output_type, "value", first_c.output_type)
                        if first_c
                        else ClassificationOutputEnum.CATEGORICAL.value
                    )
                ),  # output_type_dd
                gr.update(
                    value=first_c.allow_multiple if first_c else False
                ),  # allow_multiple_cb
                gr.update(
                    value=first_c.require_llm_explanation if first_c else False
                ),  # require_expl_cb
                gr.update(
                    value=first_c.categories_text if first_c else ""
                ),  # categories_tb
                # States
                new_selected_group_name or "",  # old_group_name_state
                first_c.name if first_c else "",  # old_class_name_state
                (
                    _parse_categories(first_c.categories_text) if first_c else []
                ),  # categories_state
                first_c.indicators_text_by_cat if first_c else {},  # indicators_state
            )

        delete_group_btn.click(
            fn=_handle_delete_group_clicked,
            inputs=[group_name_tb],  # current group name
            outputs=[
                group_dd,
                group_name_tb,
                classifications_radio,
                delete_group_btn,
                class_name_tb,
                class_question_tb,
                class_explanation_tb,
                output_type_dd,
                allow_multiple_cb,
                require_expl_cb,
                categories_tb,
                # States
                old_group_name_state,
                old_class_name_state,
                categories_state,
                indicators_state,
            ],
        )

        # ---------------------------------------------------------
        def _handle_classification_click(radio_label: str, current_group_name: str):
            """
            Radio changed.
            - If sentinel: clear editor for create mode.
            - Else: call controller with real classification name.
            """
            if radio_label == CLASS_CREATE_SENTINEL:
                # create mode -> clear editor
                return (
                    gr.update(value=""),  # class_name_tb
                    gr.update(value=""),  # class_question_tb
                    gr.update(value=""),  # class_explanation_tb
                    gr.update(
                        value=ClassificationOutputEnum.CATEGORICAL.value
                    ),  # output_type_dd
                    gr.update(value=False),  # allow_multiple_cb
                    gr.update(value=False),  # require_expl_cb
                    gr.update(value=""),  # categories_tb
                    gr.update(interactive=False),

                    # States
                    "",  # old_class_name_state  (no old name in create)
                    [],  # categories_state
                    {},  # indicators_state
                )

            cname = classification_index.get(radio_label)
            if not cname:
                return (gr.update(),) * 11  # no change

            class_vm = on_classification_clicked(current_group_name, cname)
            if class_vm is None:
                return (gr.update(),) * 11

            return (
                gr.update(value=class_vm.name),
                gr.update(value=class_vm.question),
                gr.update(value=class_vm.explanation),
                gr.update(
                    value=getattr(class_vm.output_type, "value", class_vm.output_type)
                ),
                gr.update(value=class_vm.allow_multiple),
                gr.update(value=class_vm.require_llm_explanation),
                gr.update(value=class_vm.categories_text),
                gr.update(interactive=True),

                # States
                (class_vm.name),  # old_class_name_state
                _parse_categories(class_vm.categories_text),  # categories_state
                class_vm.indicators_text_by_cat or {},  # LOAD indicators into state
            )

        classifications_radio.change(
            fn=_handle_classification_click,
            inputs=[classifications_radio, group_name_tb],
            outputs=[
                class_name_tb,
                class_question_tb,
                class_explanation_tb,
                output_type_dd,
                allow_multiple_cb,
                require_expl_cb,
                categories_tb,
                remove_class_btn,

                # States
                old_class_name_state,
                categories_state,
                indicators_state,
            ],
        )

        # ---------------------------------------------------------
        def _handle_save_classification(
            current_group_name: str,
            name: str,
            original_name: str,
            question: str,
            explanation: str,
            out_type: str,
            allow_multiple: bool,
            require_expl: bool,
            categories_text: str,
            cats: List[str],
            indicators_dict: dict,
        ):
            """
            Save (create/update/rename) a classification.

            indicator_vals comes from indicator_boxes in cats order.
            """

            gname = (current_group_name or "").strip()
            if not gname:
                # no group selected -> no-op
                return (gr.update(),) * 10

            indicators_dict = indicators_dict or {}
            indicators_by_cat_vals = [indicators_dict.get(c, "") for c in (cats or [])]

            class_vm = _fields_to_class_vm(
                name=name,
                original_name=original_name,
                question=question,
                explanation=explanation,
                out_type=_norm_out_type(out_type),
                allow_multiple=allow_multiple,
                require_expl=require_expl,
                categories_text=categories_text,
                indicators_by_cat_vals=indicators_by_cat_vals,
                cats=cats or [],
            )

            # controller does create/update/rename logic
            detail_vm = on_save_classification_clicked(gname, class_vm)
            if detail_vm is None:
                return (gr.update(),) * 10

            # rebuild left list
            radio_choices, radio_value = _build_class_radio(detail_vm)

            # select saved classification for right editor
            selected = None
            for c in detail_vm.classifications or []:
                if c.name == class_vm.name:
                    selected = c
                    break
            if selected is None and detail_vm.classifications:
                selected = detail_vm.classifications[0]

            return (
                # --- UI components ---
                gr.update(
                    choices=radio_choices, value=radio_value
                ),  # 1 classifications_radio
                gr.update(value=selected.name if selected else ""),  # 2 class_name_tb
                gr.update(
                    value=selected.question if selected else ""
                ),  # 3 class_question_tb
                gr.update(
                    value=selected.explanation if selected else ""
                ),  # 4 class_explanation_tb
                gr.update(
                    value=(
                        getattr(selected.output_type, "value", selected.output_type)
                        if selected
                        else ClassificationOutputEnum.CATEGORICAL.value
                    )
                ),  # 5 output_type_dd
                gr.update(
                    value=selected.allow_multiple if selected else False
                ),  # 6 allow_multiple_cb
                gr.update(
                    value=selected.require_llm_explanation if selected else False
                ),  # 7 require_expl_cb
                gr.update(
                    value=selected.categories_text if selected else ""
                ),  # 8 categories_tb
                # --- States (always last) ---
                (selected.name if selected else ""),  # 9 old_class_name_state
                (
                    _parse_categories(selected.categories_text) if selected else []
                ),  # 10 categories_state
                (
                    selected.indicators_text_by_cat if selected else {}
                ),  # 11 indicators_state
            )

        save_class_btn.click(  # pylint: disable=no-member
            fn=_handle_save_classification,
            inputs=[
                group_name_tb,
                class_name_tb,
                old_class_name_state,
                class_question_tb,
                class_explanation_tb,
                output_type_dd,
                allow_multiple_cb,
                require_expl_cb,
                categories_tb,
                categories_state,
                indicators_state,
            ],
            outputs=[
                classifications_radio,
                class_name_tb,
                class_question_tb,
                class_explanation_tb,
                output_type_dd,
                allow_multiple_cb,
                require_expl_cb,
                categories_tb,
                # States
                old_class_name_state,
                categories_state,
                indicators_state,
            ],
        )

        # ---------------------------------------------------------
        def _handle_remove_classification(group_name: str, selected_label: str):
            """
            Remove button clicked.
            - Resolve selected radio label -> classification_name
            - Call controller
            - Update left list + right editor based on returned detail VM
            """

            gname = (group_name or "").strip()
            if not gname or gname == GROUP_CREATE_SENTINEL:
                # Nothing valid selected
                return (
                    gr.skip(),  # classifications_radio
                    gr.skip(),  # class_name_tb
                    gr.skip(),  # class_question_tb
                    gr.skip(),  # class_explanation_tb
                    gr.skip(),  # output_type_dd
                    gr.skip(),  # allow_multiple_cb
                    gr.skip(),  # require_expl_cb
                    gr.skip(),  # categories_tb
                    gr.update(interactive=False),

                    # States
                    gr.skip(),  # old_group_name_state
                    gr.skip(),  # old_class_name_state
                    gr.skip(),  # categories_state
                    gr.skip(),  # indicators_state
                )

            # Sentinel or empty selection => no remove
            if not selected_label or selected_label == CLASS_CREATE_SENTINEL:
                gr.Warning("No classification selected to remove.")
                return (
                    gr.skip(),  # classifications_radio
                    gr.skip(),  # class_name_tb
                    gr.skip(),  # class_question_tb
                    gr.skip(),  # class_explanation_tb
                    gr.skip(),  # output_type_dd
                    gr.skip(),  # allow_multiple_cb
                    gr.skip(),  # require_expl_cb
                    gr.skip(),  # categories_tb
                    gr.update(interactive=False),

                    # States
                    gr.skip(),  # old_group_name_state
                    gr.skip(),  # old_class_name_state
                    gr.skip(),  # categories_state
                    gr.skip(),  # indicators_state
                )

            # Translate UI label -> real logical name
            cname = classification_index.get(selected_label)
            if not cname:
                gr.Warning("Could not resolve selected classification.")
                return (
                    gr.skip(),  # classifications_radio
                    gr.skip(),  # class_name_tb
                    gr.skip(),  # class_question_tb
                    gr.skip(),  # class_explanation_tb
                    gr.skip(),  # output_type_dd
                    gr.skip(),  # allow_multiple_cb
                    gr.skip(),  # require_expl_cb
                    gr.skip(),  # categories_tb
                    gr.update(interactive=False),

                    # States
                    gr.skip(),  # old_group_name_state
                    gr.skip(),  # old_class_name_state
                    gr.skip(),  # categories_state
                    gr.skip(),  # indicators_state
                )

            # Call controller
            detail_vm = on_remove_classification_clicked(gname, cname)
            if detail_vm is None:
                # Controller failed -> empty UI
                empty_choices = [CLASS_CREATE_SENTINEL]
                return (
                    gr.update(choices=empty_choices, value=None),
                    gr.update(value=""),
                    gr.update(value=""),
                    gr.update(value=""),
                    gr.update(value=ClassificationOutputEnum.CATEGORICAL.value),
                    gr.update(value=False),
                    gr.update(value=False),
                    gr.update(value=""),
                    gr.update(interactive=False),
                    # States
                    "",  # old_group_name_state  (no old name in create)
                    "",  # old_class_name_state  (no old name in create)
                    [],  # categories_state
                    {},  # indicators_state
                )

            # Rebuild left list
            radio_choices, radio_value = _build_class_radio(detail_vm)

            # Pick selected or first classification for editor
            sel_idx = detail_vm.selected_index or 0
            first_c = (
                detail_vm.classifications[sel_idx]
                if detail_vm.classifications
                and sel_idx < len(detail_vm.classifications)
                else (
                    detail_vm.classifications[0] if detail_vm.classifications else None
                )
            )

            return (
                gr.update(
                    choices=radio_choices, value=radio_value
                ),  # classifications_radio
                gr.update(value=first_c.name if first_c else ""),  # class_name_tb
                gr.update(
                    value=first_c.question if first_c else ""
                ),  # class_question_tb
                gr.update(
                    value=first_c.explanation if first_c else ""
                ),  # class_explanation_tb
                gr.update(  # output_type_dd
                    value=(
                        getattr(first_c.output_type, "value", first_c.output_type)
                        if first_c
                        else ClassificationOutputEnum.CATEGORICAL.value
                    )
                ),
                gr.update(
                    value=first_c.allow_multiple if first_c else False
                ),  # allow_multiple_cb
                gr.update(
                    value=first_c.require_llm_explanation if first_c else False
                ),  # require_expl_cb
                gr.update(
                    value=first_c.categories_text if first_c else ""
                ),  # categories_tb
                gr.update(interactive=True),
                # States
                gr.update(value=gname),  # old_group_name_state
                gr.update(
                    value=first_c.name if first_c else ""
                ),  # old_class_name_state
                (
                    _parse_categories(first_c.categories_text) if first_c else []
                ),  # categories_state
                first_c.indicators_text_by_cat if first_c else {},  # indicators_state
            )

        remove_class_btn.click(  # pylint: disable=no-member
            fn=_handle_remove_classification,
            inputs=[group_dd, classifications_radio],
            outputs=[
                classifications_radio,
                class_name_tb,
                class_question_tb,
                class_explanation_tb,
                output_type_dd,
                allow_multiple_cb,
                require_expl_cb,
                categories_tb,
                remove_class_btn,
                # States
                old_group_name_state,
                old_class_name_state,
                categories_state,
                indicators_state,
            ],
        )
