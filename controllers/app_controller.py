# controllers/app_controller.py
import gradio as gr
from controllers.general_controller import GeneralController
# Future controllers can be implemented later:
# from controllers.label_controller import LabelController
# from controllers.prompt_controller import PromptController
# from controllers.advanced_controller import AdvancedController


class AppController:
    """
    Main application controller that orchestrates startup and manages all top‑level Gradio tabs.

    This class initializes and launches the user interface for the application. It registers
    each functional tab—General, Label Manager, Prompt Manager, and Advanced Settings—
    delegating layout rendering and event wiring responsibilities to their respective controllers.
    """

    def __init__(self) -> None:
        """
        Initialize the application's sub‑controllers.

        Each controller encapsulates its own logic and view layer, ensuring a clean separation
        across modules according to the MVC (Model–View–Controller) pattern.
        """
        self.general_controller = GeneralController()

        # Placeholder: initialize other controllers when they are implemented
        # self.label_controller = LabelController()
        # self.prompt_controller = PromptController()
        # self.advanced_controller = AdvancedController()

    def launch(self) -> None:
        """
        Start and launch the Gradio‑based interface.

        This method creates a Gradio `Blocks` layout, renders multiple tabs
        corresponding to various features of the application, and finally
        launches the interactive web UI.
        """
        with gr.Blocks(title="AI Public Opinion Analyzer") as demo:
            # General tab -------------------------------------------------------------------
            with gr.Tab("General"):
                self.general_controller.render_general_view()

            # Label Manager tab --------------------------------------------------------------
            with gr.Tab("Label Manager"):
                gr.Markdown("### Label Manager (Coming Soon)")
                gr.Textbox(label="Manage label groups here.")

            # Prompt Manager tab -------------------------------------------------------------
            with gr.Tab("Prompt Manager"):
                gr.Markdown("### Prompt Manager (Coming Soon)")
                gr.Textbox(label="Edit or swap prompts for LLMs here.")

            # Advanced Settings tab ----------------------------------------------------------
            with gr.Tab("Advanced Settings"):
                gr.Markdown("### Advanced Settings (Coming Soon)")
                gr.Slider(
                    minimum=0,
                    maximum=1,
                    step=0.1,
                    label="Example setting slider (placeholder)"
                )

        demo.launch()
