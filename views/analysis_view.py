"""
analysis_view.py
================

Gradio-based view for the Analysis page.

This module is UI-only:
- Renders the AnalysisViewModel returned by the controller.
- Wires user actions back to the AnalysisController.
- Uses dataclasses, not dicts, for view models.
"""

from __future__ import annotations
from typing import List, Optional, Tuple, TYPE_CHECKING
import gradio as gr

if TYPE_CHECKING:
    from controllers.analysis_controller import AnalysisController


from models.view_models.analysis import (
    AnalysisViewModel,
    ContentItemListViewModel,
    ContentItemDetailViewModel,
    ContentAnalysisRunViewModel,
    LLMModelInfoViewModel,
)


class AnalysisView:
    """
    Gradio view for the Analysis page.

    Responsible for:
    - Rendering the UI layout.
    - Wiring events to AnalysisController callbacks via _handle_* methods.
    """

    def __init__(self, analysis_controller: AnalysisController) -> None:
        self.analysis_controller = analysis_controller

        # UI component handles (set in render_analysis_view)
        self.urls_tb: Optional[gr.Textbox] = None

        self.content_radio: Optional[gr.Radio] = None
        self.remove_btn: Optional[gr.Button] = None

        self.summary_model_dd: Optional[gr.Dropdown] = None
        self.prompt_template_dd: Optional[gr.Dropdown] = None
        self.class_group_dd: Optional[gr.Dropdown] = None

        self.summary_tb: Optional[gr.Textbox] = None
        self.limit_slider: Optional[gr.Slider] = None
        self.run_models_cb: Optional[gr.CheckboxGroup] = None

        self.progress_md: Optional[gr.Markdown] = None
        self.info_md: Optional[gr.Markdown] = None
        self.error_md: Optional[gr.Markdown] = None

    # ================================================================
    # ENTRY POINT
    # ================================================================
    def render_analysis_view(self, view_model: AnalysisViewModel) -> None:
        """
        Render the complete Analysis view using Gradio components.

        This is the main entry point called by the controller.
        """
        # ----------------------------------------------------------------
        # Helper: extract choices from LLMModelInfoViewModel list
        # ----------------------------------------------------------------
        def _llm_choices(models: Optional[List[LLMModelInfoViewModel]]) -> List[str]:
            if not models:
                return []
            # You may decide to encode provider+model_name into the label later.
            return [m.label for m in models]

        # ----------------------------------------------------------------
        # Layout
        # ----------------------------------------------------------------
        with gr.Column():

            # ============================================================
            # TOP ROW: Paste URLs + "Parse links"
            # ============================================================
            with gr.Row():
                self.urls_tb = gr.Textbox(
                    label="Paste URLs",
                    placeholder="One URL per line…",
                    lines=4,
                    interactive=True,
                )
                parse_btn = gr.Button("Parse links", variant="primary")

            # Messages (info / error)
            with gr.Row():
                self.info_md = gr.Markdown(
                    value=view_model.info_message or "",
                    elem_id="analysis-info-message",
                )
                self.error_md = gr.Markdown(
                    value=view_model.error_message or "",
                    elem_id="analysis-error-message",
                )

            gr.Markdown("---")

            # ============================================================
            # SECOND ROW: Left = content list, Right = detail + run
            # ============================================================
            with gr.Row():

                # ---------------- LEFT COLUMN: Content list ----------------
                with gr.Column(scale=1):
                    gr.Markdown("### Parsed content")

                    contents = view_model.contents or []
                    content_choices = self._content_choices_from_list(contents)

                    self.content_radio = gr.Radio(
                        label="Content items",
                        choices=content_choices,
                        value=content_choices[0] if content_choices else None,
                        interactive=True,
                    )

                    self.remove_btn = gr.Button("Remove selected")

                # ---------------- RIGHT COLUMN: Detail / Settings / Run -----
                with gr.Column(scale=3):
                    gr.Markdown("### Details & Analysis")

                    # Summary model dropdown
                    self.summary_model_dd = gr.Dropdown(
                        label="Summary model",
                        choices=_llm_choices(view_model.available_llm_models),
                        interactive=True,
                    )

                    # Prompt template + classification group
                    self.prompt_template_dd = gr.Dropdown(
                        label="Prompt template",
                        choices=[],  # will be provided by detail view model later
                        interactive=True,
                    )
                    self.class_group_dd = gr.Dropdown(
                        label="Classification group",
                        choices=[],
                        interactive=True,
                    )

                    # Summary text
                    self.summary_tb = gr.Textbox(
                        label="Summary",
                        lines=10,
                        interactive=True,
                    )

                    with gr.Row():
                        gen_sum_btn = gr.Button("Generate summary", variant="primary")
                        save_sum_btn = gr.Button("Save summary")

                    gr.Markdown("---")

                    # Limit slider
                    self.limit_slider = gr.Slider(
                        minimum=10,
                        maximum=500,
                        step=10,
                        value=100,
                        label="Max comments to analyze",
                        interactive=True,
                    )

                    gr.Markdown("---")

                    # Select LLM models for analysis
                    self.run_models_cb = gr.CheckboxGroup(
                        label="LLM models for analysis",
                        choices=_llm_choices(view_model.available_llm_models),
                        interactive=True,
                    )

                    run_btn = gr.Button("Run analysis", variant="primary")

                    gr.Markdown("### Analysis progress")
                    self.progress_md = gr.Markdown(value="No runs yet.")

            # ============================================================
            # POLLING TIMER
            # ============================================================
            # You can later wire outputs to specific components (e.g. progress_md)
            timer = gr.Timer(1.0, active=True)  # 1.0 seconds between ticks

            timer.tick(
                fn=self._handle_analysis_status_polled,
                outputs=[],  # or just omit this if you really don't return anything
            )

        # ================================================================
        # EVENT WIRING
        # ================================================================
        # Parse links
        parse_btn.click(  # pylint: disable=no-member
            fn=self._handle_parse_links_clicked,
            inputs=[self.urls_tb],
            outputs=[],
        )

        # Content selection changed
        self.content_radio.change(  # pylint: disable=no-member
            fn=self._handle_content_clicked,
            inputs=[self.content_radio],
            outputs=[],
        )

        # Remove selected content
        self.remove_btn.click(  # pylint: disable=no-member
            fn=self._handle_remove_content_clicked,
            inputs=[self.content_radio],
            outputs=[],
        )

        # Generate summary
        gen_sum_btn.click(  # pylint: disable=no-member
            fn=self._handle_generate_summary_clicked,
            inputs=[
                self.content_radio,       # which content
                self.summary_model_dd,    # which model
            ],
            outputs=[self.summary_tb],
        )

        # Save summary (manual text)
        save_sum_btn.click(  # pylint: disable=no-member
            fn=self._handle_summary_save_clicked,
            inputs=[
                self.content_radio,
                self.summary_tb,
            ],
            outputs=[],
        )

        # Limit changed
        self.limit_slider.change(  # pylint: disable=no-member
            fn=self._handle_limit_changed,
            inputs=[self.content_radio, self.limit_slider],
            outputs=[],
        )

        # Prompt/template/classification dropdowns
        self.prompt_template_dd.change(  # pylint: disable=no-member
            fn=self._handle_prompt_template_changed,
            inputs=[self.content_radio, self.prompt_template_dd],
            outputs=[],
        )

        self.class_group_dd.change(  # pylint: disable=no-member
            fn=self._handle_classification_group_changed,
            inputs=[self.content_radio, self.class_group_dd],
            outputs=[],
        )

        # Run analysis
        run_btn.click(  # pylint: disable=no-member
            fn=self._handle_run_analysis_clicked,
            inputs=[self.run_models_cb],
            outputs=[],
        )

    # ================================================================
    # INTERNAL HELPERS
    # ================================================================
    def _content_choices_from_list(
        self,
        contents: List[ContentItemListViewModel],
    ) -> List[str]:
        """
        Build labels used in the Radio from ContentItemListViewModel list.

        We encode platform + content_id in the label so handlers can decode it.
        Format: "{platform}|{content_id}|{title}"
        """
        choices: List[str] = []
        for c in contents:
            # platform is likely an enum; use its value or str(c.platform)
            plat_str = getattr(c.platform, "value", str(c.platform))
            label = f"{plat_str}|{c.content_id}|{c.title}"
            choices.append(label)
        return choices

    def _decode_content_label(self, label: str) -> Optional[Tuple[str, str]]:
        """
        Reverse of _content_choices_from_list:
        given "platform|content_id|title" → (platform_str, content_id).
        """
        if not label:
            return None
        parts = label.split("|", 2)
        if len(parts) < 2:
            return None
        platform_str, content_id = parts[0], parts[1]
        return platform_str, content_id

    # ================================================================
    # CALLBACK WRAPPERS (_handle_* → controller)
    # ================================================================
    def _handle_parse_links_clicked(self, raw_text: str):
        """
        Forward 'parse links' event to controller.

        TODO: map AnalysisViewModel → gr.update(...) for list/detail/progress.
        """
        _vm: AnalysisViewModel = self.analysis_controller.on_parse_links_clicked(raw_text)
        # For now we ignore the VM and rely on external re-render.
        # Later: return a tuple of gr.update(...) for bound components.
        return

    def _handle_content_clicked(self, selection_label: str):
        """
        Forward content selection to controller.

        TODO: use returned ContentItemDetailViewModel to update detail panel.
        """
        decoded = self._decode_content_label(selection_label)
        if not decoded:
            return
        platform_str, content_id = decoded
        # Controller expects PlatformEnum, but we keep platform_str here.
        # It can convert inside.
        self.analysis_controller.on_content_clicked(platform_str, content_id)
        return

    def _handle_remove_content_clicked(self, selection_label: str):
        """
        Forward 'remove content' event to controller.

        TODO: use returned AnalysisViewModel to update list + detail.
        """
        decoded = self._decode_content_label(selection_label)
        if not decoded:
            return
        platform_str, content_id = decoded
        _vm: AnalysisViewModel = self.analysis_controller.on_remove_content_clicked(
            platform_str, content_id
        )
        return

    def _handle_generate_summary_clicked(
        self,
        selection_label: str,
        model_label: str,
    ) -> str:
        """
        Forward 'generate summary' event to controller.

        Returns the new summary text for the summary textbox.
        """
        decoded = self._decode_content_label(selection_label)
        if not decoded:
            return ""
        platform_str, content_id = decoded

        # TODO: map model_label back to (provider, model_name).
        # For now we just pass the label as model_name and a dummy provider.
        provider = "openai"
        model_name = model_label

        summary: str = self.analysis_controller.on_generate_summary_clicked(
            platform_str,
            content_id,
            provider,
            model_name,
        )
        return summary

    def _handle_summary_save_clicked(
        self,
        selection_label: str,
        summary_text: str,
    ):
        """
        Forward 'save summary' event to controller.
        """
        decoded = self._decode_content_label(selection_label)
        if not decoded:
            return
        platform_str, content_id = decoded
        self.analysis_controller.on_summary_save_clicked(
            platform_str,
            content_id,
            summary_text,
        )
        return

    def _handle_limit_changed(
        self,
        selection_label: str,
        limit: int,
    ):
        """
        Forward limit changes to controller.
        """
        decoded = self._decode_content_label(selection_label)
        if not decoded:
            return
        platform_str, content_id = decoded
        self.analysis_controller.on_limit_changed(
            platform_str,
            content_id,
            int(limit),
        )
        return

    def _handle_prompt_template_changed(
        self,
        selection_label: str,
        template_name: str,
    ):
        """
        Forward prompt template selection to controller.
        """
        decoded = self._decode_content_label(selection_label)
        if not decoded:
            return
        platform_str, content_id = decoded
        self.analysis_controller.on_prompt_template_changed(
            platform_str,
            content_id,
            template_name,
        )
        return

    def _handle_classification_group_changed(
        self,
        selection_label: str,
        group_id: str,
    ):
        """
        Forward classification group selection to controller.
        """
        decoded = self._decode_content_label(selection_label)
        if not decoded:
            return
        platform_str, content_id = decoded
        self.analysis_controller.on_classification_group_changed(
            platform_str,
            content_id,
            group_id,
        )
        return

    def _handle_run_analysis_clicked(
        self,
        selected_model_labels: List[str],
    ):
        """
        Forward 'run analysis' event to controller.

        TODO: map model labels → List[(provider, model_name)].
        """
        # Here we just pass dummy provider with model label as model_name.
        selected_models: List[Tuple[str, str]] = [
            ("openai", label) for label in (selected_model_labels or [])
        ]
        self.analysis_controller.on_run_analysis_clicked(selected_models)
        return

    def _handle_analysis_status_polled(self):
        """
        Periodic polling: ask controller for latest AnalysisViewModel.

        TODO: map vm.analysis_runs into progress_md text and other UI elements.
        """
        _vm: AnalysisViewModel = self.analysis_controller.on_analysis_status_polled()
        # For now, ignore and rely on external re-render.
        return
