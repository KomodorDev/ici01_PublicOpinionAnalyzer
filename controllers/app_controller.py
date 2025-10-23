# Orchestrates app-wide startup (Tabs)
# controllers/app_controller.py
import gradio as gr
from views.general_view import GeneralView

class AppController:
    """Top-level Gradio app controller — minimal shell."""

    def __init__(self):
        # Initialize the main view(s)
        self.general_view = GeneralView()

    def launch(self):
        """Start the Gradio interface."""
        with gr.Blocks(title="AI Public Opinion Analyzer") as demo:
            with gr.Tab("General"):
                self.general_view.render()

        # Run the local Gradio app
        demo.launch()