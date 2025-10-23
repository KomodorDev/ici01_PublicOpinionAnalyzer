# views/general_view.py
import gradio as gr


class GeneralView:
    """Defines the Gradio layout for the General tab."""

    def render_general_layout(self):
        """
        Builds the Gradio components for the General tab.

        This version includes:
        - A text field for YouTube video URLs
        - A multi-select model chooser (CheckboxGroup)
        - Dynamic label showing how many models are selected
        - A button to run analysis
        """

        gr.Markdown("### General Analysis Tab")

        youtube_input = gr.Textbox(
            label="YouTube Video URL:",
            placeholder="Paste a YouTube link here...",
        )

        # Define available models
        available_models = [
            "Model A",
            "Model B",
            "Model C",
            "Model D",
        ]

 # Multi-select dropdown
        model_selector = gr.Dropdown(
            choices=available_models,
            multiselect=True,
            label="Select Models for Labeling Task:",
            info="Choose one or more models for analysis.",
            value=[],  # Start empty
            interactive=True,
        )

        # Markdown container inside the gray box (same column)
        selected_models_text = gr.Markdown(
            "No models selected yet.",
            elem_id="selected-models-box",
        )

        def update_selection(selected):
            """Show selected models inline with count."""
            if not selected:
                return "No models selected yet."
            joined_models = ", ".join(selected)
            return f"**{len(selected)}** model{'s' if len(selected) != 1 else ''} selected: {joined_models}"

        # Update Markdown box whenever models change
        model_selector.change(  # pylint: disable=no-member,too-many-function-args
            fn=update_selection,
            inputs=model_selector,
            outputs=selected_models_text,
        )

        run_button = gr.Button("Run Analysis", variant="primary")

        # Layout
        with gr.Group():
            gr.Row([youtube_input]) # pylint: disable=no-member,too-many-function-args
            gr.Row([model_selector]) # pylint: disable=no-member,too-many-function-args
            gr.Row([selected_models_text]) # pylint: disable=no-member,too-many-function-args
            gr.Row([run_button]) # pylint: disable=no-member,too-many-function-args
