# views/classification_view.py
from typing import List
import gradio as gr
from models.classification_models import ClassificationGroup


##################################################################
class ClassificationView:
    """Defines the Gradio layout for the Classification management tab."""

    # ----------------------------------------------------------------
    def render_classification_view(self, groups: List[ClassificationGroup]):
        """
        Build and display the classification management UI with a master-detail layout.

        Layout:
        - Left: Scrollable list of classification groups
        - Center: List of classifications within selected group
        - Bottom: Detail view of selected classification with editable fields

        Args:
            groups: List of ClassificationGroup objects to display.
        """
        with gr.Row():
            # Left panel: Classification Groups
            with gr.Column(scale=1):
                gr.Markdown("### Classification Groups")

                # Extract group names for the list
                group_names = [group.name for group in groups]

                group_list = gr.Dropdown(
                    choices=group_names,
                    label="Select Group",
                    interactive=True,
                    value=group_names[0] if group_names else None
                )

                # Buttons for group management
                with gr.Row():
                    add_group_btn = gr.Button("Add Group", size="sm")
                    delete_group_btn = gr.Button("Delete Group", size="sm", variant="stop")

            # Center panel: Classifications in selected group
            with gr.Column(scale=1):
                gr.Markdown("### Classifications")

                classification_list = gr.Dropdown(
                    choices=[],
                    label="Select Classification",
                    interactive=True
                )

                # Buttons for classification management
                with gr.Row():
                    add_classification_btn = gr.Button("Add Classification", size="sm")
                    delete_classification_btn = gr.Button("Delete Classification", size="sm", variant="stop")

        # Bottom panel: Classification details
        gr.Markdown("---")
        gr.Markdown("### Classification Details")

        with gr.Column():
            with gr.Row():
                classification_name = gr.Textbox(
                    label="Name",
                    placeholder="e.g., pro_taiwan",
                    interactive=True
                )
                output_type = gr.Dropdown(
                    choices=["boolean", "probability", "numeric", "categorical", "text"],
                    label="Output Type",
                    value="boolean",
                    interactive=True
                )

            classification_question = gr.Textbox(
                label="Question",
                placeholder="e.g., Is the comment pro-Taiwan?",
                lines=2,
                interactive=True
            )

            # Indicators section
            with gr.Row():
                with gr.Column():
                    pro_indicators = gr.Textbox(
                        label="Pro Indicators (one per line)",
                        placeholder="Taiwan is great\nSupport Taiwan independence\n...",
                        lines=5,
                        interactive=True
                    )

                with gr.Column():
                    con_indicators = gr.Textbox(
                        label="Con Indicators (one per line)",
                        placeholder="China should control Taiwan\nTaiwan belongs to China\n...",
                        lines=5,
                        interactive=True
                    )

                with gr.Column():
                    neutral_indicators = gr.Textbox(
                        label="Neutral Indicators (one per line)",
                        placeholder="Neutral about Taiwan\nNo opinion\n...",
                        lines=5,
                        interactive=True
                    )

            # Action buttons
            with gr.Row():
                save_btn = gr.Button("Save Changes", variant="primary")
                cancel_btn = gr.Button("Cancel")

        # Event handlers
        def on_group_selected(selected_group_name):
            """Update classification list when group is selected."""
            if not selected_group_name:
                return gr.Dropdown(choices=[])

            # Find the selected group
            selected_group = next((g for g in groups if g.name == selected_group_name), None)
            if not selected_group:
                return gr.Dropdown(choices=[])

            # Get classification names from the group
            classification_names = [c.name for c in selected_group.classifications]
            return gr.Dropdown(choices=classification_names, value=classification_names[0] if classification_names else None)

        def on_classification_selected(group_name, classification_name):
            """Load classification details when selected."""
            if not group_name or not classification_name:
                return ("", "", "boolean", "", "", "")

            # Find the group and classification
            selected_group = next((g for g in groups if g.name == group_name), None)
            if not selected_group:
                return ("", "", "boolean", "", "", "")

            selected_classification = next((c for c in selected_group.classifications if c.name == classification_name), None)
            if not selected_classification:
                return ("", "", "boolean", "", "", "")

            # Convert lists to newline-separated strings
            pro_text = "\n".join(selected_classification.pro_indicators)
            con_text = "\n".join(selected_classification.con_indicators)
            neutral_text = "\n".join(selected_classification.neutral_indicators)

            return (
                selected_classification.name,
                selected_classification.question,
                selected_classification.output_type,
                pro_text,
                con_text,
                neutral_text
            )

        # Wire up events
        group_list.change(
            fn=on_group_selected,
            inputs=[group_list],
            outputs=[classification_list]
        )

        classification_list.change(
            fn=on_classification_selected,
            inputs=[group_list, classification_list],
            outputs=[
                classification_name,
                classification_question,
                output_type,
                pro_indicators,
                con_indicators,
                neutral_indicators
            ]
        )

        # TODO: Wire up save, delete, add buttons to controller methods

    # ----------------------------------------------------------------

##################################################################
