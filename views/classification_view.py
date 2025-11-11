from typing import List, Dict, Optional
import gradio as gr
from models.classification_models import ClassificationGroup, ClassificationOutputEnum

class ClassificationView:
    """Defines the Gradio layout for the Classification management tab (new model)."""

    def render_classification_view(self, groups: List["ClassificationGroup"]):
        def _find_group(gname: Optional[str]) -> Optional["ClassificationGroup"]:
            if not gname:
                return None
            return next((g for g in groups if g.name == gname), None)

        def _find_classification(gname: Optional[str], cname: Optional[str]):
            g = _find_group(gname)
            if not g or not cname:
                return None, None
            c = next((c for c in g.classifications if c.name == cname), None)
            return g, c

        def _vis(flag: bool):
            """Batch visibility updates for categorical controls using gr.update()."""
            return (
                gr.update(visible=flag),  # allow_multiple
                gr.update(visible=flag),  # new_category_name
                gr.update(visible=flag),  # add_category_btn
                gr.update(visible=flag),  # existing_categories_dd
                gr.update(visible=flag),  # rename_category_tb
                gr.update(visible=flag),  # rename_category_btn
                gr.update(visible=flag),  # delete_category_btn
                gr.update(visible=flag),  # indicators_heading_md
                gr.update(visible=flag),  # indicators_help_md
            )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Classification Groups")
                group_names = [g.name for g in groups]
                group_list = gr.Dropdown(
                    choices=group_names,
                    label="Select Group",
                    interactive=True,
                    value=group_names[0] if group_names else None,
                )
                with gr.Row():
                    add_group_btn = gr.Button("Add Group", size="sm")
                    delete_group_btn = gr.Button("Delete Group", size="sm", variant="stop")

            with gr.Column(scale=1):
                gr.Markdown("### Classifications")
                classification_list = gr.Dropdown(choices=[], label="Select Classification", interactive=True)
                with gr.Row():
                    add_classification_btn = gr.Button("Add Classification", size="sm")
                    delete_classification_btn = gr.Button("Delete Classification", size="sm", variant="stop")

        gr.Markdown("---")
        gr.Markdown("### Classification Details")

        categories_state = gr.State([])            # List[str]
        indicators_state = gr.State({})            # Dict[str, List[str]]
        selected_category_state = gr.State(None)   # Optional[str]
        is_categorical_state = gr.State(True)      # toggle for categorical UI

        with gr.Column():
            with gr.Row():
                classification_name = gr.Textbox(
                    label="Name",
                    placeholder="e.g., pro_taiwan",
                    interactive=True,
                )
                output_type = gr.Dropdown(
                    choices=[e.value for e in ClassificationOutputEnum],
                    label="Output Type",
                    value=ClassificationOutputEnum.CATEGORICAL.value,
                    interactive=True,
                )

            classification_question = gr.Textbox(
                label="Question",
                placeholder="e.g., Is the comment pro-Taiwan?",
                lines=2,
                interactive=True,
            )

            with gr.Row():
                explanation = gr.Textbox(
                    label="Explanation (optional)",
                    placeholder="Short description of what this classification measures.",
                    lines=2,
                    interactive=True,
                )
                require_llm_explanation = gr.Checkbox(
                    label="Require LLM Explanation",
                    value=False,
                )

            allow_multiple = gr.Checkbox(
                label="Allow multiple categories",
                value=False,
                visible=True,
            )

            with gr.Row():
                new_category_name = gr.Textbox(
                    label="New Category",
                    placeholder="e.g., pro, con, neutral",
                    interactive=True,
                    visible=True,
                )
                add_category_btn = gr.Button("Add Category", size="sm", visible=True)

            with gr.Row():
                existing_categories_dd = gr.Dropdown(
                    choices=[],
                    label="Existing Categories",
                    interactive=True,
                    visible=True,
                )
                rename_category_tb = gr.Textbox(
                    label="Rename To",
                    placeholder="New name...",
                    interactive=True,
                    visible=True,
                )
                rename_category_btn = gr.Button("Rename", size="sm", visible=True)

            delete_category_btn = gr.Button("Delete Selected Category", size="sm", variant="stop", visible=True)

            indicators_heading_md = gr.Markdown("#### Indicators per Category", visible=True)
            indicators_help_md = gr.Markdown(
                "Add indicator phrases for each category (one per line). "
                "These guide heuristic/rule-based cues or prompt construction.",
                visible=True,
            )

            @gr.render()
            def _render_indicator_sections(is_categorical=is_categorical_state,
                                           categories=categories_state,
                                           indicators=indicators_state):
                if not is_categorical:
                    return
                if not categories:
                    gr.Markdown("_No categories yet. Add one above._")
                    return
                for cat in categories:
                    lines = indicators.get(cat, [])
                    txt = "\n".join(lines)
                    with gr.Accordion(f"Category: {cat}", open=False):
                        tb = gr.Textbox(
                            label=f"Indicators for '{cat}' (one per line)",
                            value=txt,
                            lines=6,
                            interactive=True,
                        )

                        def _on_indicators_change(curr_indicators, text, catname):
                            items = [line.strip() for line in text.splitlines() if line.strip()]
                            new_dict = dict(curr_indicators or {})
                            new_dict[catname] = items
                            return new_dict

                        tb.change(
                            fn=_on_indicators_change,
                            inputs=[indicators_state, tb, gr.State(cat)],
                            outputs=indicators_state,
                        )

            with gr.Row():
                save_btn = gr.Button("Save Changes", variant="primary")
                cancel_btn = gr.Button("Cancel")

        def on_group_selected(selected_group_name):
            if not selected_group_name:
                return gr.update(choices=[], value=None)
            g = _find_group(selected_group_name)
            if not g:
                return gr.update(choices=[], value=None)
            names = [c.name for c in g.classifications]
            return gr.update(choices=names, value=(names[0] if names else None))

        group_list.change(
            fn=on_group_selected,
            inputs=[group_list],
            outputs=[classification_list],
        )

        def on_classification_selected(group_name, classification_name):
            _, c = _find_classification(group_name, classification_name)
            if not c:
                is_cat = True
                return (
                    "", "", ClassificationOutputEnum.CATEGORICAL.value, "", False, False,
                    [], {}, gr.update(choices=[], value=None), is_cat, *_vis(is_cat)
                )
            name = c.name
            q = c.question
            ot = c.output_type.value if hasattr(c.output_type, "value") else str(c.output_type)
            expl = c.explanation or ""
            req_llm = bool(getattr(c, "require_llm_explanation", False))
            cats = list(c.categories or [])
            allow_mult = bool(getattr(c, "allow_multiple", False))
            ind = dict(c.indicators or {})
            dd = gr.update(choices=cats, value=(cats[0] if cats else None))
            is_cat = (ot == ClassificationOutputEnum.CATEGORICAL.value)

            return (
                name, q, ot, expl, req_llm, allow_mult,
                cats, ind, dd,
                is_cat, *_vis(is_cat)
            )

        classification_list.change(
            fn=on_classification_selected,
            inputs=[group_list, classification_list],
            outputs=[
                classification_name,
                classification_question,
                output_type,
                explanation,
                require_llm_explanation,
                allow_multiple,
                categories_state,
                indicators_state,
                existing_categories_dd,
                is_categorical_state,
                allow_multiple,
                new_category_name,
                add_category_btn,
                existing_categories_dd,
                rename_category_tb,
                rename_category_btn,
                delete_category_btn,
                indicators_heading_md,
                indicators_help_md,
            ],
        )

        def on_output_type_changed(ot):
            is_cat = (ot == ClassificationOutputEnum.CATEGORICAL.value)
            return (is_cat, *_vis(is_cat))

        output_type.change(
            fn=on_output_type_changed,
            inputs=[output_type],
            outputs=[
                is_categorical_state,
                allow_multiple,
                new_category_name,
                add_category_btn,
                existing_categories_dd,
                rename_category_tb,
                rename_category_btn,
                delete_category_btn,
                indicators_heading_md,
                indicators_help_md,
            ],
        )

        def add_category(cats: List[str], inds: Dict[str, List[str]], new_name: str):
            new_name = (new_name or "").strip()
            if not new_name:
                return cats, inds, gr.update(), gr.update()
            if new_name in cats:
                return cats, inds, gr.update(value=new_name, choices=cats), gr.update(value="")
            new_cats = list(cats or []) + [new_name]
            new_inds = dict(inds or {})
            new_inds.setdefault(new_name, [])
            return (
                new_cats,
                new_inds,
                gr.update(value=new_name, choices=new_cats),
                gr.update(value=""),
            )

        add_category_btn.click(
            fn=add_category,
            inputs=[categories_state, indicators_state, new_category_name],
            outputs=[categories_state, indicators_state, existing_categories_dd, new_category_name],
        )

        def rename_category(cats: List[str], inds: Dict[str, List[str]], sel: Optional[str], new_name: str):
            if not sel:
                return cats, inds, gr.update(), gr.update()
            new_name = (new_name or "").strip()
            if not new_name or new_name == sel:
                return cats, inds, gr.update(), gr.update(value="")
            if new_name in (cats or []):
                return cats, inds, gr.update(value=new_name, choices=cats), gr.update(value="")
            new_cats = [new_name if c == sel else c for c in (cats or [])]
            new_inds = dict(inds or {})
            if sel in new_inds:
                new_inds[new_name] = new_inds.pop(sel)
            return new_cats, new_inds, gr.update(value=new_name, choices=new_cats), gr.update(value="")

        rename_category_btn.click(
            fn=rename_category,
            inputs=[categories_state, indicators_state, existing_categories_dd, rename_category_tb],
            outputs=[categories_state, indicators_state, existing_categories_dd, rename_category_tb],
        )

        def delete_category(cats: List[str], inds: Dict[str, List[str]], sel: Optional[str]):
            if not sel or sel not in (cats or []):
                return cats, inds, gr.update()
            new_cats = [c for c in cats if c != sel]
            new_inds = dict(inds or {})
            new_inds.pop(sel, None)
            new_value = new_cats[0] if new_cats else None
            return new_cats, new_inds, gr.update(choices=new_cats, value=new_value)

        delete_category_btn.click(
            fn=delete_category,
            inputs=[categories_state, indicators_state, existing_categories_dd],
            outputs=[categories_state, indicators_state, existing_categories_dd],
        )

        existing_categories_dd.change(
            fn=lambda x: x,
            inputs=[existing_categories_dd],
            outputs=[selected_category_state],
        )

        def on_cancel():
            return gr.update()

        cancel_btn.click(fn=on_cancel, inputs=None, outputs=None)

        def on_save(group_name,
                    classification_name_val,
                    question_val,
                    output_type_val,
                    explanation_val,
                    require_llm_val,
                    allow_mult_val,
                    cats_val: List[str],
                    inds_val: Dict[str, List[str]]):
            errors = []
            if not group_name:
                errors.append("No group selected.")
            if not classification_name_val:
                errors.append("Classification name is required.")
            if output_type_val == ClassificationOutputEnum.CATEGORICAL.value:
                if not cats_val:
                    errors.append("At least one category is required for categorical output.")
                else:
                    for c in cats_val:
                        inds_val.setdefault(c, [])
            if errors:
                return gr.Info(" | ".join(errors))
            return gr.Success("Classification saved.")

        save_btn.click(
            fn=on_save,
            inputs=[
                group_list,
                classification_name,
                classification_question,
                output_type,
                explanation,
                require_llm_explanation,
                allow_multiple,
                categories_state,
                indicators_state,
            ],
            outputs=[],
        )

        if group_names:
            _ = on_group_selected(group_names[0])
