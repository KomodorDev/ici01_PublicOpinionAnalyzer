from __future__ import annotations

from typing import Callable, List, Tuple
import gradio as gr

from models.view_models.analysis import AnalysisViewModel, ContentItemDetailViewModel

# forward refs for type hints – you already have these dataclasses somewhere
# from models.view.analysis_view_model import AnalysisViewModel
# from models.view.content_item_detail_view_model import ContentItemDetailViewModel


class AnalysisView:
    """
    Gradio view for managing and running comment analysis.

    Parameters (via `render_analysis_view`)
    ---------------------------------------
    initial_view_model : AnalysisViewModel
        Snapshot of the current analysis state used to populate the UI on first render.
        This typically includes:
            - list of parsed contents (videos/posts) grouped by platform
            - current selection (platform + content_id)
            - current sort/limit settings
            - current prompt template + classification group selections
            - current analysis / job status, if any

    on_parse_links_clicked : Callable[[str], AnalysisViewModel]
        Controller callback for the "Parse links" button.
        Called with:
            raw_text: str       - text area content containing one or more URLs
        Returns:
            Updated AnalysisViewModel with parsed content items added / updated.

    on_content_clicked : Callable[[str, str], ContentItemDetailViewModel]
        Controller callback when a user clicks/selects a specific content item.
        Called with:
            platform_str: str   - platform identifier (e.g. "youtube", "reddit")
            content_id: str     - internal content id
        Returns:
            ContentItemDetailViewModel describing that content item (metadata, comments, etc.).

    on_remove_content_clicked : Callable[[str, str], AnalysisViewModel]
        Controller callback for a "Remove content" action.
        Called with:
            platform_str: str
            content_id: str
        Returns:
            Updated AnalysisViewModel after removing the content item.

    on_generate_summary_clicked : Callable[[str, str, str, str], str]
        Controller callback for "Generate summary" on a specific content item.
        Called with:
            platform_str: str
            content_id: str
            provider: str       - LLM provider identifier (e.g. "openai", "google")
            model_name: str     - concrete model name (e.g. "gpt-4o-mini")
        Returns:
            The generated summary text as a string (to fill a summary textbox).

    on_summary_save_clicked : Callable[[str, str, str], None]
        Controller callback when a user edits and saves the summary text.
        Called with:
            platform_str: str
            content_id: str
            new_text: str       - new summary text to persist
        Returns:
            None. Controller is responsible for saving; view will usually show a toast.

    on_sort_changed : Callable[[str, str, str, str], None]
        Controller callback when the user changes the comment sorting.
        Called with:
            platform_str: str
            content_id: str
            sort_by: str        - sort key (e.g. "RELEVANCE", "TIME")
            sort_dir: str       - sort direction ("ASC" / "DESC")
        Returns:
            None. The controller updates internal state; the view will typically trigger
            a refresh via `on_analysis_status_polled` or another callback.

    on_limit_changed : Callable[[str, str, int], None]
        Controller callback when the user changes the "limit" (number of comments).
        Called with:
            platform_str: str
            content_id: str
            limit: int          - new comment limit
        Returns:
            None.

    on_prompt_template_changed : Callable[[str, str, str], None]
        Controller callback when the user selects a different prompt template
        for a given content item.
        Called with:
            platform_str: str
            content_id: str
            template_name: str  - name of the selected prompt template
        Returns:
            None.

    on_classification_group_changed : Callable[[str, str, str], None]
        Controller callback when the user selects a different classification group.
        Called with:
            platform_str: str
            content_id: str
            group_id: str       - identifier of the selected classification group
        Returns:
            None.

    on_run_analysis_clicked : Callable[[List[Tuple[str, str]]], None]
        Controller callback for the main "Run analysis" action.
        Called with:
            selected_models: List[Tuple[provider, model_name]]
                Example: [("openai", "gpt-4o-mini"), ("google", "gemini-1.5-flash")]
        Returns:
            None. The controller starts analysis jobs; the view will usually poll status.

    on_analysis_status_polled : Callable[[], AnalysisViewModel]
        Controller callback used for polling analysis status (e.g. via a Timer).
        Called with:
            no arguments
        Returns:
            Updated AnalysisViewModel (job progress, per-content status, etc.).

    Behavior
    --------
    - Renders the main "Analysis" screen:
        * link input / parse button
        * list of parsed contents per platform
        * per-content controls (sort, limit, prompt template, classification group)
        * summary generation and editing
        * run-analysis controls and live status
    - All stateful operations (parsing, selection, sorting, saving, running jobs)
      are delegated to the controller via the injected callables.
    - The view is stateless between calls: it renders whatever the passed-in
      AnalysisViewModel describes and uses `gr.update(...)` for UI updates.
    """

    # ================================================================
    # ENTRY POINT
    # ================================================================
    def render_analysis_view(
        self,
        *,
        view_model: AnalysisViewModel,
        on_parse_links_clicked: Callable[[str], AnalysisViewModel],
        on_content_clicked: Callable[[str, str], ContentItemDetailViewModel],
        on_remove_content_clicked: Callable[[str, str], AnalysisViewModel],
        on_generate_summary_clicked: Callable[[str, str, str, str], str],
        on_summary_save_clicked: Callable[[str, str, str], None],
        on_sort_changed: Callable[[str, str, str, str], None],
        on_limit_changed: Callable[[str, str, int], None],
        on_prompt_template_changed: Callable[[str, str, str], None],
        on_classification_group_changed: Callable[[str, str, str], None],
        on_run_analysis_clicked: Callable[[List[Tuple[str, str]]], None],
        on_analysis_status_polled: Callable[[], AnalysisViewModel],
    ) -> None:
        """
        Render the complete Analysis management view using Gradio components.

        This method builds the layout (link input, content list, comment table,
        summary editor, model selection, run button, status area) and wires all
        user interactions to the provided controller callbacks.

        The `initial_view_model` snapshot is used to populate the UI on first render;
        subsequent updates are driven via the callbacks and polling.
        """

        # maps radio label -> (platform_enum, content_id)
        content_index: dict[str, tuple[object, str]] = {}

        # maps summary model display label -> (provider, model_name)
        summary_model_index: dict[str, tuple[str, str]] = {}

        # maps analysis model display label -> (provider, model_name)
        analysis_model_index: dict[str, tuple[str, str]] = {}

        PROMPT_SENTINEL = "— Select prompt template —"
        GROUP_SENTINEL = "— Select classification group —"

        # ----------------------------------------------------------------
        # INITIAL ANALYSIS MODEL DROPDOWN CHOICES
        # ----------------------------------------------------------------
        analysis_model_labels: list[str] = []
        analysis_model_index.clear()

        for mdl in view_model.available_llm_models or []:
            provider = getattr(mdl, "provider", "?")
            model_name = getattr(mdl, "model_name", "?")
            display_name = getattr(mdl, "display_name", None)
            if not display_name:
                display_name = f"{provider}:{model_name}"

            analysis_model_labels.append(display_name)
            analysis_model_index[display_name] = (provider, model_name)

        # ================================================================
        # LAYOUT
        # ================================================================
        with gr.Column():

            # ----------------------------------------------------------------
            # 1) TOP: link input + parse button
            # ----------------------------------------------------------------
            link_input_tb = gr.Textbox(
                label="Paste links (one per line or separated by spaces)",
                placeholder="https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...",
                lines=3,
                interactive=True,
            )

            parse_links_btn = gr.Button(
                "Parse Links",
                variant="primary",
                scale=1,
            )

            gr.Markdown("---")

            # ----------------------------------------------------------------
            # 2) MAIN BODY: left list + right detail
            #    Initially: no content items, no details
            # ----------------------------------------------------------------
            with gr.Row():

                # ---------------- LEFT: scrollable content list ----------------
                with gr.Column(scale=1):
                    gr.Markdown("### Content Item List")
                    content_list_radio = gr.Radio(
                        label="Parsed content items",
                        choices=[],  # starts empty
                        value=None,
                        interactive=True,
                    )
                    # We'll keep a parallel list of content_ids in the closure later.

                # ---------------- RIGHT: detail view ----------------
                with gr.Column(scale=3):

                    gr.Markdown("### Content Item Details")

                    # Basic metadata (empty on first render)

                    with gr.Group():
                        with gr.Row():
                            title_md = gr.Markdown(
                                value="""
                                <div style='padding: 12px 16px; margin-bottom: 12px; font-size:1.15rem;'>
                                <a href="#" target="_blank" style="text-decoration:none; color:#4ea1ff;">
                                    -
                                </a>
                                </div>
                                """
                            )

                        with gr.Row():
                            platform_tb = gr.Textbox(
                                label="Platform",
                                value="-",
                                interactive=False,
                            )
                            author_tb = gr.Textbox(
                                label="Author",
                                value="-",
                                interactive=False,
                            )

                        with gr.Row():
                            view_count_tb = gr.Textbox(
                                label="Views",
                                value="0",
                                interactive=False,
                            )
                            like_count_tb = gr.Textbox(
                                label="Likes",
                                value="0",
                                interactive=False,
                            )
                            comment_count_tb = gr.Textbox(
                                label="Comments",
                                value="0",
                                interactive=False,
                            )

                    gr.Markdown("### Summary")

                    # Summary text (empty, editable)
                    summary_tb = gr.Textbox(
                        label="Summary",
                        value="",
                        lines=6,
                        interactive=True,
                    )

                    with gr.Row():
                        summary_source_tb = gr.Textbox(
                            label="Summary Source (read-only)",
                            value="N/A",
                            interactive=False,
                        )

                        summary_model_dd = gr.Dropdown(
                            label="Summary Model",
                            choices=[],  # populated after models are known
                            value=None,
                            interactive=True,
                        )

                    with gr.Row():
                        generate_summary_btn = gr.Button(
                            "Generate Summary",
                            variant="primary",
                        )
                        save_summary_btn = gr.Button(
                            "Save Summary",
                            variant="secondary",
                        )
                        cancel_summary_btn = gr.Button(
                            "Cancel",
                            variant="secondary",
                        )

                    gr.Markdown("### Analysis Configuration")

                    with gr.Row():
                        prompt_template_dd = gr.Dropdown(
                            label="Prompt Template",
                            choices=[],
                            value=None,
                            interactive=True,
                        )
                        class_group_dd = gr.Dropdown(
                            label="Classification Group",
                            choices=[],
                            value=None,
                            interactive=True,
                        )

                    with gr.Row():
                        sort_by_dd = gr.Dropdown(
                            label="Sort By",
                            choices=["RELEVANCE", "TIME", "LIKES"],
                            value="RELEVANCE",
                            interactive=True,
                        )
                        sort_dir_dd = gr.Dropdown(
                            label="Sort Direction",
                            choices=["ASC", "DESC"],
                            value="DESC",
                            interactive=True,
                        )
                        limit_tb = gr.Textbox(
                            label="Limit (number of comments, empty = no limit)",
                            value="",
                            interactive=True,
                        )

                    with gr.Row():
                        remove_content_btn = gr.Button(
                            "Remove Content Item",
                            variant="stop",
                        )

        with gr.Column():

            # ----------------------------------------------------------------
            # 3) Model Selection
            # ----------------------------------------------------------------

            gr.Markdown("---")

            gr.Markdown("### Model Selection")

            # Placeholder for selected models; real UI wired later
            analysis_models_dd = gr.Dropdown(
                label="Models for analysis",
                choices=analysis_model_labels,
                value=[],  # start with nothing selected
                multiselect=True,
                interactive=True,
            )

            # ----------------------------------------------------------------
            # 4) Run Analysis
            # ----------------------------------------------------------------

            gr.Markdown("---")

            gr.Markdown("### Run Analysis")

            run_analysis_btn = gr.Button(
                "Run Analysis",
                variant="primary",
            )

            # Error panel (starts empty / invisible to user)
            analysis_error_md = gr.Markdown(value="")

            # NEW: Progress overview (Markdown table)
            analysis_progress_md = gr.Markdown(
                value="",
                visible=True,
            )

            analysis_timer = gr.Timer(
                value=1.0,  # interval in seconds
                active=False,  # start inactive; we’ll turn it on after “Run Analysis”
            )
        # ================================================================
        # WIRING
        # ================================================================

        # ---------------------------------------------------------
        def _handle_parse_links_clicked(raw_text: str):
            """
            Called when user presses 'Parse Links'.
            - raw_text: content of link_input_tb
            """

            # 1) Ask controller to parse links → returns new AnalysisViewModel
            vm = on_parse_links_clicked(raw_text)

            # 2a) Build new choices for the content list
            new_labels: list[str] = []
            content_index.clear()  # reset mapping

            # 2b) Summary models (VideoModelInfoViewModel → labels)
            sm_choices: list[str] = []
            summary_model_index.clear()

            for mdl in vm.selected.available_summary_models or []:
                provider = getattr(mdl, "provider", "?")
                model_name = getattr(mdl, "model_name", "?")
                display_name = getattr(mdl, "display_name", None)
                if not display_name:
                    display_name = f"{provider}:{model_name}"

                sm_choices.append(display_name)
                summary_model_index[display_name] = (provider, model_name)

            sm_value = sm_choices[0] if sm_choices else None

            # 2c) Build content list labels + index
            if vm.contents:
                for ci in vm.contents:
                    platform_str = getattr(ci.platform, "value", str(ci.platform))
                    label = f"[{platform_str}] {ci.author} — {ci.title}"
                    new_labels.append(label)
                    # store the actual enum + content_id so we can use it later
                    content_index[label] = (ci.platform, ci.content_id)

            # 3) Determine which item should be selected in the radio
            #    We use vm.selected (ContentItemDetailViewModel) if present.
            selected_vm = vm.selected
            auto_value = None

            if selected_vm is not None:
                sel_platform_str = getattr(
                    selected_vm.platform, "value", str(selected_vm.platform)
                )
                sel_label = (
                    f"[{sel_platform_str}] {selected_vm.author} — {selected_vm.title}"
                )
                if sel_label in new_labels:
                    auto_value = sel_label
            elif new_labels:
                # fallback: select the first item if no selected is set
                auto_value = new_labels[0]

            # 4) If we have a selected detail VM, fill the right panel from it
            if selected_vm is not None:
                platform_val = getattr(
                    selected_vm.platform, "value", str(selected_vm.platform)
                )
                author_val = selected_vm.author or "-"
                title_val = (
                    f"""
                <div style='padding: 12px 16px; margin-bottom: 12px; font-size:1.15rem;'>
                <a href="{selected_vm.url}" target="_blank" style="text-decoration:none; color:#4ea1ff;">
                    {selected_vm.title}
                </a>
                </div>
                """
                    or "-"
                )
                view_count_val = str(selected_vm.view_count or 0)
                like_count_val = str(selected_vm.like_count or 0)
                comment_count_val = str(selected_vm.comment_count or 0)

                summary_text_val = selected_vm.summary_text or ""
                summary_source_val = selected_vm.summary_source or "N/A"

                # Prompt templates
                pt_choices = selected_vm.available_prompt_templates or []
                pt_choices_with_empty = [PROMPT_SENTINEL] + pt_choices
                pt_value = selected_vm.selected_prompt_template_name
                if pt_value not in pt_choices:
                    pt_value = PROMPT_SENTINEL

                # Classification groups
                cg_choices = selected_vm.available_classification_groups or []
                cg_choices_with_empty = [GROUP_SENTINEL] + cg_choices
                cg_value = selected_vm.selected_classification_group_name
                if cg_value not in cg_choices:
                    cg_value = GROUP_SENTINEL

                # Sort options
                sort_by_choices = [
                    getattr(opt, "value", str(opt))
                    for opt in (selected_vm.available_sort_by_options or [])
                ]
                sort_by_value = getattr(
                    selected_vm.sort_by, "value", str(selected_vm.sort_by)
                )
                if sort_by_choices and sort_by_value not in sort_by_choices:
                    sort_by_value = sort_by_choices[0]

                sort_dir_choices = [
                    getattr(opt, "value", str(opt))
                    for opt in (selected_vm.available_sort_dir_options or [])
                ]
                sort_dir_value = getattr(
                    selected_vm.sort_dir, "value", str(selected_vm.sort_dir)
                )
                if sort_dir_choices and sort_dir_value not in sort_dir_choices:
                    sort_dir_value = sort_dir_choices[0]

                # Limit (int → textbox string; 0 or None means empty)
                limit_int = selected_vm.limit
                limit_val = (
                    "" if (limit_int is None or limit_int == 0) else str(limit_int)
                )

                # Summary models (VideoModelInfoViewModel → labels)
                sm_choices: list[str] = []
                for mdl in selected_vm.available_summary_models or []:
                    # heuristic: try display_name, fall back to "provider:model_name"
                    display_name = getattr(mdl, "display_name", None)
                    if not display_name:
                        provider = getattr(mdl, "provider", "?")
                        model_name = getattr(mdl, "model_name", "?")
                        display_name = f"{provider}:{model_name}"
                    sm_choices.append(display_name)

                # we don't (yet) have a selected summary model field; start with None
                sm_value = sm_choices[0] if sm_choices else None

                return (
                    gr.update(
                        choices=new_labels, value=auto_value
                    ),  # content_list_radio
                    gr.update(value=title_val),  # title_tb
                    gr.update(value=platform_val),  # platform_tb
                    gr.update(value=author_val),  # author_tb
                    gr.update(value=view_count_val),  # view_count_tb
                    gr.update(value=like_count_val),  # like_count_tb
                    gr.update(value=comment_count_val),  # comment_count_tb
                    gr.update(value=summary_text_val),  # summary_tb
                    gr.update(value=summary_source_val),  # summary_source_tb
                    gr.update(choices=sm_choices, value=sm_value),  # summary_model_dd
                    gr.update(
                        choices=pt_choices_with_empty, value=pt_value
                    ),  # prompt_template_dd
                    gr.update(
                        choices=cg_choices_with_empty, value=cg_value
                    ),  # class_group_dd
                    gr.update(
                        choices=sort_by_choices, value=sort_by_value
                    ),  # sort_by_dd
                    gr.update(
                        choices=sort_dir_choices, value=sort_dir_value
                    ),  # sort_dir_dd
                    gr.update(value=limit_val),  # limit_tb
                )

            # 5) If there is still no selected item, fall back to "empty detail" state
            return (
                gr.update(choices=new_labels, value=auto_value),  # content_list_radio
                gr.update(value="-"),  # title_tb
                gr.update(value="-"),  # platform_tb
                gr.update(value="-"),  # author_tb
                gr.update(value="0"),  # view_count_tb
                gr.update(value="0"),  # like_count_tb
                gr.update(value="0"),  # comment_count_tb
                gr.update(value=""),  # summary_tb
                gr.update(value="N/A"),  # summary_source_tb
                gr.update(choices=[], value=None),  # summary_model_dd
                gr.update(choices=[], value=None),  # prompt_template_dd
                gr.update(choices=[], value=None),  # class_group_dd
                gr.update(
                    choices=["RELEVANCE", "TIME", "LIKES"], value="RELEVANCE"
                ),  # sort_by_dd
                gr.update(choices=["ASC", "DESC"], value="DESC"),  # sort_dir_dd
                gr.update(value=""),  # limit_tb
            )

        parse_links_btn.click(  # pylint: disable=no-member
            fn=_handle_parse_links_clicked,
            inputs=[link_input_tb],
            outputs=[
                content_list_radio,
                title_md,
                platform_tb,
                author_tb,
                view_count_tb,
                like_count_tb,
                comment_count_tb,
                summary_tb,
                summary_source_tb,
                summary_model_dd,
                prompt_template_dd,
                class_group_dd,
                sort_by_dd,
                sort_dir_dd,
                limit_tb,
            ],
        )

        # ---------------------------------------------------------
        # - content_list_radio.change(...)
        def _handle_content_clicked(selected_label: str):
            """
            Called when a user selects a different content item in the radio list.
            We look up platform + content_id from content_index, ask the controller
            for a ContentItemDetailViewModel, and fill the right-hand panel.
            """
            entry = content_index.get(selected_label)
            if entry is None:
                # nothing to do; return no-op updates
                return (
                    gr.update(),  # title_md
                    gr.update(),  # platform_tb
                    gr.update(),  # author_tb
                    gr.update(),  # view_count_tb
                    gr.update(),  # like_count_tb
                    gr.update(),  # comment_count_tb
                    gr.update(),  # summary_tb
                    gr.update(),  # summary_source_tb
                    gr.update(),  # summary_model_dd
                    gr.update(),  # prompt_template_dd
                    gr.update(),  # class_group_dd
                    gr.update(),  # sort_by_dd
                    gr.update(),  # sort_dir_dd
                    gr.update(),  # limit_tb
                )

            platform_enum, content_id = entry

            # Ask controller for detail VM
            selected_vm = on_content_clicked(platform_enum, content_id)
            if selected_vm is None:
                return (
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )

            # Summary models (VideoModelInfoViewModel → labels)
            sm_choices: list[str] = []
            summary_model_index.clear()

            for mdl in selected_vm.available_summary_models or []:
                provider = getattr(mdl, "provider", "?")
                model_name = getattr(mdl, "model_name", "?")
                display_name = getattr(mdl, "display_name", None)
                if not display_name:
                    display_name = f"{provider}:{model_name}"

                sm_choices.append(display_name)
                summary_model_index[display_name] = (provider, model_name)

            sm_value = sm_choices[0] if sm_choices else None

            # Set values from selected_vm
            platform_val = getattr(
                selected_vm.platform, "value", str(selected_vm.platform)
            )
            author_val = selected_vm.author or "-"

            # Nicely formatted HTML link with padding
            title_html = (
                f"<div style='padding: 12px 16px; margin-bottom: 12px; font-size:1.15rem;'>"
                f'<a href="{selected_vm.url}" target="_blank" '
                f'style="text-decoration:none; color:#4ea1ff;">'
                f"{selected_vm.title}"
                f"</a></div>"
            )

            view_count_val = str(selected_vm.view_count or 0)
            like_count_val = str(selected_vm.like_count or 0)
            comment_count_val = str(selected_vm.comment_count or 0)

            summary_text_val = selected_vm.summary_text or ""
            summary_source_val = selected_vm.summary_source or "N/A"

            # Prompt templates
            pt_choices = selected_vm.available_prompt_templates or []
            pt_choices_with_empty = [PROMPT_SENTINEL] + pt_choices
            pt_value = selected_vm.selected_prompt_template_name
            if pt_value not in pt_choices:
                pt_value = PROMPT_SENTINEL

            # Classification groups
            cg_choices = selected_vm.available_classification_groups or []
            cg_choices_with_empty = [GROUP_SENTINEL] + cg_choices
            cg_value = selected_vm.selected_classification_group_name
            if cg_value not in cg_choices:
                cg_value = GROUP_SENTINEL

            # Sort options
            sort_by_choices = [
                getattr(opt, "value", str(opt))
                for opt in (selected_vm.available_sort_by_options or [])
            ]
            sort_by_value = getattr(
                selected_vm.sort_by, "value", str(selected_vm.sort_by)
            )
            if sort_by_choices and sort_by_value not in sort_by_choices:
                sort_by_value = sort_by_choices[0]

            sort_dir_choices = [
                getattr(opt, "value", str(opt))
                for opt in (selected_vm.available_sort_dir_options or [])
            ]
            sort_dir_value = getattr(
                selected_vm.sort_dir, "value", str(selected_vm.sort_dir)
            )
            if sort_dir_choices and sort_dir_value not in sort_dir_choices:
                sort_dir_value = sort_dir_choices[0]

            limit_int = selected_vm.limit
            limit_val = "" if (limit_int is None or limit_int == 0) else str(limit_int)

            # Summary models
            sm_choices: list[str] = []
            for mdl in selected_vm.available_summary_models or []:
                display_name = getattr(mdl, "display_name", None)
                if not display_name:
                    provider = getattr(mdl, "provider", "?")
                    model_name = getattr(mdl, "model_name", "?")
                    display_name = f"{provider}:{model_name}"
                sm_choices.append(display_name)
            sm_value = sm_choices[0] if sm_choices else None

            return (
                gr.update(value=title_html),  # title_md
                gr.update(value=platform_val),  # platform_tb
                gr.update(value=author_val),  # author_tb
                gr.update(value=view_count_val),  # view_count_tb
                gr.update(value=like_count_val),  # like_count_tb
                gr.update(value=comment_count_val),  # comment_count_tb
                gr.update(value=summary_text_val),  # summary_tb
                gr.update(value=summary_source_val),  # summary_source_tb
                gr.update(choices=sm_choices, value=sm_value),  # summary_model_dd
                gr.update(
                    choices=pt_choices_with_empty, value=pt_value
                ),  # prompt_template_dd
                gr.update(
                    choices=cg_choices_with_empty, value=cg_value
                ),  # class_group_dd
                gr.update(choices=sort_by_choices, value=sort_by_value),  # sort_by_dd
                gr.update(
                    choices=sort_dir_choices, value=sort_dir_value
                ),  # sort_dir_dd
                gr.update(value=limit_val),  # limit_tb
            )

        content_list_radio.change(  # pylint: disable=no-member
            fn=_handle_content_clicked,
            inputs=[content_list_radio],
            outputs=[
                title_md,
                platform_tb,
                author_tb,
                view_count_tb,
                like_count_tb,
                comment_count_tb,
                summary_tb,
                summary_source_tb,
                summary_model_dd,
                prompt_template_dd,
                class_group_dd,
                sort_by_dd,
                sort_dir_dd,
                limit_tb,
            ],
        )

        # ---------------------------------------------------------
        def _handle_remove_content_clicked(selected_label: str):
            """
            Called when user presses 'Remove content' for the currently selected item.
            - selected_label: current value of content_list_radio
            """
            entry = content_index.get(selected_label)
            if entry is None:
                # Nothing mapped → nothing to delete → no-op updates
                return (
                    gr.update(),  # content_list_radio
                    gr.update(),  # title_md
                    gr.update(),  # platform_tb
                    gr.update(),  # author_tb
                    gr.update(),  # view_count_tb
                    gr.update(),  # like_count_tb
                    gr.update(),  # comment_count_tb
                    gr.update(),  # summary_tb
                    gr.update(),  # summary_source_tb
                    gr.update(),  # summary_model_dd
                    gr.update(),  # prompt_template_dd
                    gr.update(),  # class_group_dd
                    gr.update(),  # sort_by_dd
                    gr.update(),  # sort_dir_dd
                    gr.update(),  # limit_tb
                )

            platform_enum, content_id = entry

            # 1) Ask controller to remove this content → returns new AnalysisViewModel
            vm = on_remove_content_clicked(platform_enum, content_id)

            # 2) Rebuild left list from vm.contents
            new_labels: list[str] = []
            content_index.clear()

            if vm.contents:
                for ci in vm.contents:
                    plat_str = getattr(ci.platform, "value", str(ci.platform))
                    label = f"[{plat_str}] {ci.author} — {ci.title}"
                    new_labels.append(label)
                    content_index[label] = (ci.platform, ci.content_id)

            # 3) Determine new selected item (vm.selected, or first, or None)
            selected_vm = vm.selected
            auto_value = None

            if selected_vm is not None:
                sel_plat_str = getattr(
                    selected_vm.platform, "value", str(selected_vm.platform)
                )
                sel_label = (
                    f"[{sel_plat_str}] {selected_vm.author} — {selected_vm.title}"
                )
                if sel_label in new_labels:
                    auto_value = sel_label
            elif new_labels:
                auto_value = new_labels[0]

            # 4) If still no selected_vm after removal, clear the detail panel
            if selected_vm is None:
                return (
                    gr.update(
                        choices=new_labels, value=auto_value
                    ),  # content_list_radio
                    gr.update(value="-"),  # title_md
                    gr.update(value="-"),  # platform_tb
                    gr.update(value="-"),  # author_tb
                    gr.update(value="0"),  # view_count_tb
                    gr.update(value="0"),  # like_count_tb
                    gr.update(value="0"),  # comment_count_tb
                    gr.update(value=""),  # summary_tb
                    gr.update(value="N/A"),  # summary_source_tb
                    gr.update(choices=[], value=None),  # summary_model_dd
                    gr.update(choices=[], value=None),  # prompt_template_dd
                    gr.update(choices=[], value=None),  # class_group_dd
                    gr.update(
                        choices=["RELEVANCE", "TIME", "LIKES"], value="RELEVANCE"
                    ),  # sort_by_dd
                    gr.update(choices=["ASC", "DESC"], value="DESC"),  # sort_dir_dd
                    gr.update(value=""),  # limit_tb
                )

            # 5) We have a selected detail VM → fill right panel like in _handle_parse_links
            platform_val = getattr(
                selected_vm.platform, "value", str(selected_vm.platform)
            )
            author_val = selected_vm.author or "-"

            title_html = (
                f"<div style='padding: 12px 16px; margin-bottom: 12px; font-size:1.15rem;'>"
                f'<a href="{selected_vm.url}" target="_blank" '
                f'style="text-decoration:none; color:#4ea1ff;">'
                f"{selected_vm.title}"
                f"</a></div>"
            )

            view_count_val = str(selected_vm.view_count or 0)
            like_count_val = str(selected_vm.like_count or 0)
            comment_count_val = str(selected_vm.comment_count or 0)

            summary_text_val = selected_vm.summary_text or ""
            summary_source_val = selected_vm.summary_source or "N/A"

            # Prompt templates
            pt_choices = selected_vm.available_prompt_templates or []
            pt_choices_with_empty = [PROMPT_SENTINEL] + pt_choices
            pt_value = selected_vm.selected_prompt_template_name
            if pt_value not in pt_choices:
                pt_value = PROMPT_SENTINEL

            # Classification groups
            cg_choices = selected_vm.available_classification_groups or []
            cg_choices_with_empty = [GROUP_SENTINEL] + cg_choices

            cg_value = selected_vm.selected_classification_group_name
            if cg_value not in cg_choices:
                cg_value = GROUP_SENTINEL

            # Sort options
            sort_by_choices = [
                getattr(opt, "value", str(opt))
                for opt in (selected_vm.available_sort_by_options or [])
            ]
            sort_by_value = getattr(
                selected_vm.sort_by, "value", str(selected_vm.sort_by)
            )
            if sort_by_choices and sort_by_value not in sort_by_choices:
                sort_by_value = sort_by_choices[0]

            sort_dir_choices = [
                getattr(opt, "value", str(opt))
                for opt in (selected_vm.available_sort_dir_options or [])
            ]
            sort_dir_value = getattr(
                selected_vm.sort_dir, "value", str(selected_vm.sort_dir)
            )
            if sort_dir_choices and sort_dir_value not in sort_dir_choices:
                sort_dir_value = sort_dir_choices[0]

            limit_int = selected_vm.limit
            limit_val = "" if (limit_int is None or limit_int == 0) else str(limit_int)

            # Summary models
            sm_choices: list[str] = []
            for mdl in selected_vm.available_summary_models or []:
                display_name = getattr(mdl, "display_name", None)
                if not display_name:
                    provider = getattr(mdl, "provider", "?")
                    model_name = getattr(mdl, "model_name", "?")
                    display_name = f"{provider}:{model_name}"
                sm_choices.append(display_name)
            sm_value = sm_choices[0] if sm_choices else None

            return (
                gr.update(choices=new_labels, value=auto_value),  # content_list_radio
                gr.update(value=title_html),  # title_md
                gr.update(value=platform_val),  # platform_tb
                gr.update(value=author_val),  # author_tb
                gr.update(value=view_count_val),  # view_count_tb
                gr.update(value=like_count_val),  # like_count_tb
                gr.update(value=comment_count_val),  # comment_count_tb
                gr.update(value=summary_text_val),  # summary_tb
                gr.update(value=summary_source_val),  # summary_source_tb
                gr.update(choices=sm_choices, value=sm_value),  # summary_model_dd
                gr.update(
                    choices=pt_choices_with_empty, value=pt_value
                ),  # prompt_template_dd
                gr.update(
                    choices=cg_choices_with_empty, value=cg_value
                ),  # class_group_dd
                gr.update(choices=sort_by_choices, value=sort_by_value),  # sort_by_dd
                gr.update(
                    choices=sort_dir_choices, value=sort_dir_value
                ),  # sort_dir_dd
                gr.update(value=limit_val),  # limit_tb
            )

        remove_content_btn.click(   # pylint: disable=no-member
            fn=_handle_remove_content_clicked,
            inputs=[content_list_radio],  # current selection
            outputs=[
                content_list_radio,
                title_md,
                platform_tb,
                author_tb,
                view_count_tb,
                like_count_tb,
                comment_count_tb,
                summary_tb,
                summary_source_tb,
                summary_model_dd,
                prompt_template_dd,
                class_group_dd,
                sort_by_dd,
                sort_dir_dd,
                limit_tb,
            ],
        )

        # ---------------------------------------------------------
        def _handle_generate_summary_clicked(
            selected_label: str,
            selected_model_label: str,
        ):
            """
            Called when user clicks 'Generate Summary'.

            - selected_label: current content_list_radio value
            - selected_model_label: current summary_model_dd value
            """

            # 1) Resolve content (platform_enum, content_id)
            entry = content_index.get(selected_label)
            if entry is None:
                gr.Warning("No content selected.")
                return (
                    gr.update(),  # summary_tb
                    gr.update(),  # summary_source_tb
                )

            platform_enum, content_id = entry

            # 2) Resolve model (provider, model_name)
            model_entry = summary_model_index.get(selected_model_label)
            if model_entry is None:
                gr.Warning("No summary model selected.")
                return (
                    gr.update(),
                    gr.update(),
                )

            provider, model_name = model_entry

            # 3) Ask controller to generate summary text
            try:
                new_summary_text = on_generate_summary_clicked(
                    platform_enum,
                    content_id,
                    provider,
                    model_name,
                )
            except Exception as exc:  # optional: debug safety
                print("Error in on_generate_summary_clicked:", exc)
                gr.Warning("Failed to generate summary.")
                return (
                    gr.update(),  # leave current summary as is
                    gr.update(),  # leave source as is
                )

            # 4) Update summary textbox and source
            # We don’t have a fresh ViewModel here (controller returns str),
            # so we choose a reasonable source tag ("ai").
            return (
                gr.update(value=new_summary_text or ""),
                gr.update(value="ai"),  # or "AI model", up to you
            )

        generate_summary_btn.click( # pylint: disable=no-member
            fn=_handle_generate_summary_clicked,
            inputs=[
                content_list_radio,  # which content
                summary_model_dd,  # which model
            ],
            outputs=[
                summary_tb,
                summary_source_tb,
            ],
        )

        # ---------------------------------------------------------
        def _handle_summary_save_clicked(
            selected_label: str,
            new_summary_text: str,
        ):
            """
            Called when user clicks 'Save Summary'.

            - selected_label: current content_list_radio value
            - new_summary_text: current text in summary_tb
            """
            entry = content_index.get(selected_label)
            if entry is None:
                gr.Warning("No content selected to save summary for.")
                return gr.update()  # no change to summary_source_tb

            platform_enum, content_id = entry

            # Let controller persist the new summary text
            on_summary_save_clicked(platform_enum, content_id, new_summary_text)

            # Mark the source as 'manual' (or whatever label you want)
            return gr.update(value="manual")

        save_summary_btn.click( # pylint: disable=no-member
            fn=_handle_summary_save_clicked,
            inputs=[
                content_list_radio,  # which content item
                summary_tb,  # the edited text
            ],
            outputs=[
                summary_source_tb,  # only update the source label
            ],
        )

        # ---------------------------------------------------------
        def _handle_summary_cancel_clicked(selected_label: str):
            """
            Restore the last saved summary by re-fetching the detail VM.
            """
            entry = content_index.get(selected_label)
            if entry is None:
                gr.Warning("No content selected.")
                return (
                    gr.update(),  # summary_tb
                    gr.update(),  # summary_source_tb
                )

            platform_enum, content_id = entry

            # Re-fetch real state from backend
            selected_vm = on_content_clicked(platform_enum, content_id)
            if selected_vm is None:
                return (
                    gr.update(),  # summary_tb
                    gr.update(),  # summary_source_tb
                )

            summary_text_val = selected_vm.summary_text or ""
            summary_source_val = selected_vm.summary_source or "N/A"

            return (
                gr.update(value=summary_text_val),
                gr.update(value=summary_source_val),
            )

        cancel_summary_btn.click(   # pylint: disable=no-member
            fn=_handle_summary_cancel_clicked,
            inputs=[content_list_radio],
            outputs=[
                summary_tb,
                summary_source_tb,
            ],
        )

        # ---------------------------------------------------------
        def _handle_prompt_template_changed(
            selected_label: str,
            selected_tpl: str,
        ):
            """
            Called when user changes the Prompt Template dropdown.
            - selected_label: current content_list_radio value
            - selected_tpl: new value of prompt_template_dd
            """
            entry = content_index.get(selected_label)
            if entry is None:
                # No content selected → nothing to update in backend
                gr.Warning("No content selected for prompt template change.")
                return

            platform_enum, content_id = entry

            # If user chose the sentinel "no selection" option, we *do not*
            # update the backend (ContentAnalysis stays at None).
            if not selected_tpl or selected_tpl == PROMPT_SENTINEL:
                # If you later change the controller to accept Optional[str],
                # you could call: on_prompt_template_changed(platform_enum, content_id, None)
                return

            # Real template name selected → persist in backend
            on_prompt_template_changed(platform_enum, content_id, selected_tpl)
            # No UI changes needed here; dropdown already shows the correct value.
            return

        prompt_template_dd.change(  # pylint: disable=no-member
            fn=_handle_prompt_template_changed,
            inputs=[content_list_radio, prompt_template_dd],
            outputs=[],
        )

        # ---------------------------------------------------------
        def _handle_classification_group_changed(
            selected_label: str,
            selected_group: str,
        ):
            """
            Called when user changes the Classification Group dropdown.
            - selected_label: current content_list_radio value
            - selected_group: new value of class_group_dd
            """
            entry = content_index.get(selected_label)
            if entry is None:
                gr.Warning("No content selected for classification group change.")
                return

            platform_enum, content_id = entry

            # User picked the sentinel -> treat as "no selection", don't update backend
            if not selected_group or selected_group == GROUP_SENTINEL:
                # If you later change controller to accept Optional[str], you could:
                # on_classification_group_changed(platform_enum, content_id, None)
                return

            # Real group selected -> persist in backend
            on_classification_group_changed(platform_enum, content_id, selected_group)

            return

        class_group_dd.change(  # pylint: disable=no-member
            fn=_handle_classification_group_changed,
            inputs=[content_list_radio, class_group_dd],
            outputs=[],
        )

        # ---------------------------------------------------------
        # - sort_by_dd.change(...)

        # ---------------------------------------------------------
        # - sort_dir_dd.change(...)

        # ---------------------------------------------------------
        def _handle_limit_changed(
            selected_label: str,
            limit_text: str,
        ):
            """
            Called when user edits the 'limit' textbox.
            - selected_label: which content item is active
            - limit_text: string typed into the limit_tb
            """
            entry = content_index.get(selected_label)
            if entry is None:
                return  # no content selected

            platform_enum, content_id = entry

            limit_text = (limit_text or "").strip()

            # Case 1: empty field → treat as None
            if limit_text == "":
                on_limit_changed(platform_enum, content_id, None)
                return

            # Case 2: numeric input
            try:
                new_limit = int(limit_text)
                if new_limit < 0:
                    raise ValueError("Limit must be >= 0")
            except Exception:
                gr.Warning("Limit must be a non-negative integer or empty.")
                return

            # Case 3: valid input
            on_limit_changed(platform_enum, content_id, new_limit)
            return

        limit_tb.change(    # pylint: disable=no-member
            fn=_handle_limit_changed,
            inputs=[content_list_radio, limit_tb],
            outputs=[],
        )

        # ---------------------------------------------------------
        def _handle_run_analysis(selected_model_labels: list[str]):
            """
            selected_model_labels: list of labels from analysis_models_dd
            """

            selected_models: list[tuple[str, str]] = []
            for label in selected_model_labels:
                entry = analysis_model_index.get(label)
                if entry is None:
                    continue
                selected_models.append(entry)  # (provider, model_name)

            # Ask controller to run analysis WITH validation
            status = on_run_analysis_clicked(selected_models)
            ok = bool(status.get("ok"))
            message = status.get("message", "")

            if not ok:
                # Build nice markdown error
                if message:
                    md = f"\n{message}\n"
                else:
                    md = "\nCannot start analysis\n\nUnknown validation error."
                # Also show a toast if you want
                gr.Warning("Cannot start analysis. See details below.")
                return md, gr.update(active=False)

            # Success path -> clear error markdown
            gr.Success(message or "Analysis started.")
            return "", gr.update(active=True)

        run_analysis_btn.click( # pylint: disable=no-member
            fn=_handle_run_analysis,
            inputs=[analysis_models_dd],
            outputs=[analysis_error_md, analysis_timer],
        )

        # ---------------------------------------------------------
        def _poll_analysis_status():
            """
            Called by the timer every tick.
            Fetches latest AnalysisViewModel and turns it into Markdown.

            Returns a tuple: (markdown_str, gr.update(active=...)). The view
            will use the `analysis_running` flag provided by the controller
            to decide whether the timer should remain active. When
            `analysis_running` is False we return `gr.update(active=False)`
            so the timer deactivates itself.
            """
            vm = on_analysis_status_polled()
            md = _analysis_runs_to_markdown(vm)
            # vm.analysis_running is authoritative; if missing, default to False
            running = bool(getattr(vm, "analysis_running", False))
            return md, gr.update(active=running)

        analysis_timer.tick(    # pylint: disable=no-member
            fn=_poll_analysis_status,
            inputs=None,
            outputs=[analysis_progress_md, analysis_timer],
        )

        # ================================================================
        # HELPER
        # ================================================================
        def _analysis_runs_to_markdown(vm: AnalysisViewModel) -> str:
            runs = vm.analysis_runs or []
            if not runs:
                return "_No analyses yet._"

            lines = [
                "| Platform   | Title     |  Fetch   | Model Runs | Export |",
                "|------------|-----------|----------|------------|--------|",
            ]

            for run in runs:
                # Direct string conversion of enum values
                fetch_cell = str(run.fetch_status)
                export_cell = str(run.export_status)

                # Build models cell
                if run.model_runs:
                    model_bits = []
                    for m in run.model_runs:
                        label = f"{m.provider}:{m.model_name}"
                        status_str = str(m.status)

                        # "progress" display e.g. (12/42)
                        progress_str = (
                            f"({m.current_comment}/{m.total_comments})"
                            if m.total_comments
                            else ""
                        )

                        # Base line: `provider:model` STATUS (x/y)
                        base = f"`{label}` {status_str} {progress_str}".strip()

                        if m.error:
                            model_bits.append(f"{base}<br><sub>⚠️ {m.error}</sub>")
                        else:
                            model_bits.append(base)

                    models_cell = "<br>".join(model_bits)
                else:
                    models_cell = "_no models_"

                # Escape pipes in title
                title = run.title.replace("|", "\\|")

                lines.append(
                    f"| {run.platform} | {title} | {fetch_cell} | {models_cell} | {export_cell} |"
                )

            return "\n".join(lines)
