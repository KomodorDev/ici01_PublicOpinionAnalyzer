# controllers/app_controller.py
import time
import gradio as gr
from controllers.general_controller import GeneralController
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
        self.general_controller = GeneralController()
        self.classification_controller = ClassificationController()
        self.settings_controller = SettingsController()
        self.prompt_template_controller = PromptTemplateController()

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
            rerender_tick = gr.State(0)  # 1) dummy state to force re-rendering views
            
            # General tab -------------------------------------------------------------------
            with gr.Tab("General"):
                self.general_controller.render_general_view()

            # Classification Manager tab --------------------------------------------------------------
            with gr.Tab("Classification Manager"):
                self.classification_controller.render_classification_view()

            # Prompt Manager tab -------------------------------------------------------------
            with gr.Tab("Prompt Manager"):
                self.prompt_template_controller.render_prompt_template_view()

            # Advanced Settings tab ----------------------------------------------------------
            with gr.Tab("Advanced Settings") as adv_tab:
                # 3) re-render when `rerender_tick` changes
                @gr.render(inputs=[rerender_tick])
                def _(_tick):
                    # Your function builds the settings UI every time
                    # the tab is selected (because _tick changes).
                    self.settings_controller.render_settings_view()

                # 2) bump state on tab selection
                def _bump(n, data: gr.SelectData):
                    # Only bump when THIS tab gets selected
                    return (n or 0) + 1 if data.selected else n

                adv_tab.select(fn=_bump, inputs=rerender_tick, outputs=rerender_tick)

        demo.launch()

    # ----------------------------------------------------------------

##################################################################
