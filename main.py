# Entry point to start the application
"""
main.py 
====================

Main entry point for the PublicOpinionAnalyzer application.
"""
from controllers.app_controller import AppController

# ----------------------------------------------------------------
def main():
    """Entry point for the Gradio application."""
    app = AppController()
    app.launch()

# ----------------------------------------------------------------

if __name__ == "__main__":
    main()
