# controllers/app_controller.py
import gradio as gr
from controllers.analysis_controller import AnalysisController
from controllers.classification_controller import ClassificationController
from controllers.settings_controller import SettingsController
from controllers.prompt_template_controller import PromptTemplateController

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
        self.analysis_controller = AnalysisController()
        self.classification_controller = ClassificationController()
        self.settings_controller = SettingsController()
        self.prompt_template_controller = PromptTemplateController()

        # Placeholder: initialize other controllers when they are implemented

    # ----------------------------------------------------------------
    def launch(self) -> None:
        """
        Start and launch the Gradio‑based interface.

        This method creates a Gradio `Blocks` layout, renders multiple tabs
        corresponding to various features of the application, and finally
        launches the interactive web UI.
        """
        with gr.Blocks(title="AI Public Opinion Analyzer") as demo:
            
            # Analysis tab -------------------------------------------------------------------
            with gr.Tab("Analysis"):
                self.analysis_controller.render_analysis_view()

            # Classification Manager tab --------------------------------------------------------------
            with gr.Tab("Classification Manager"):
                self.classification_controller.render_classification_view()

            # Prompt Manager tab -------------------------------------------------------------
            with gr.Tab("Prompt Manager"):
                self.prompt_template_controller.render_prompt_template_view()

            # Settings tab ----------------------------------------------------------
            with gr.Tab("Settings"):
                self.settings_controller.render_settings_view()
        demo.launch()

    # ----------------------------------------------------------------


##################################################################
