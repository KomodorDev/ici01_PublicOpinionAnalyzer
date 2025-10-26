# controllers/app_controller.py
import gradio as gr
from controllers.general_controller import GeneralController
from controllers.classification_controller import ClassificationController
from controllers.settings_controller import SettingsController
# Future controllers can be implemented later:
# from controllers.prompt_controller import PromptController
# from controllers.advanced_controller import AdvancedController


##################################################################
class AppController:
    """
    Main application controller that orchestrates startup and manages all top‑level Gradio tabs.

    This class initializes and launches the user interface for the application. It registers
    each functional tab—General, Label Manager, Prompt Manager, and Advanced Settings—
    delegating layout rendering and event wiring responsibilities to their respective controllers.
    """

    # ----------------------------------------------------------------
    def __init__(self) -> None:
        """
        Initialize the application's sub‑controllers.

        Each controller encapsulates its own logic and view layer, ensuring a clean separation
        across modules according to the MVC (Model–View–Controller) pattern.
        """
        self.general_controller = GeneralController()
        self.classification_controller = ClassificationController()
        self.settings_controller = SettingsController()

        # Placeholder: initialize other controllers when they are implemented

        # self.prompt_controller = PromptController()
        # self.advanced_controller = AdvancedController()

    # ----------------------------------------------------------------
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

            # Classification Manager tab --------------------------------------------------------------
            with gr.Tab("Classification Manager"):
                self.classification_controller.render_classification_view()

            # Prompt Manager tab -------------------------------------------------------------
            with gr.Tab("Prompt Manager"):
                gr.Markdown("### Prompt Manager (Coming Soon)")
                gr.Textbox(label="Edit or swap prompts for LLMs here.")

            # Advanced Settings tab ----------------------------------------------------------
            with gr.Tab("Advanced Settings"):
                # Embed the full password‑locked settings view
                self.settings_controller.render_settings_view()
        demo.launch()

    # ----------------------------------------------------------------

##################################################################
