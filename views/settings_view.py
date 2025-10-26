import gradio as gr


##################################################################
class SettingsView:
    """Renders the password‑protected Advanced Settings interface."""

    # ----------------------------------------------------------------
    def __init__(self, settings_service):
        self.service = settings_service

    # ----------------------------------------------------------------
    def unlock_settings(self, password):
        """Attempt to unlock configuration using the password."""
        try:
            # Will attempt decryption internally
            self.service.__init__(password=password)
            return (
                gr.update(visible=False),
                gr.update(visible=True),
                "✅ Access granted. Settings unlocked.",
            )
        except Exception as e:
            return (gr.update(), gr.update(), f"❌ Failed: {e}")

    # ----------------------------------------------------------------
    def render_settings_view(self):
        """Construct the UI layout for the Advanced Settings tab."""
        with gr.Blocks() as settings_ui:
            gr.Markdown("## ⚙️ Advanced Settings (Protected Access)")

            with gr.Column(visible=True) as password_area:
                gr.Markdown("Enter your password to unlock configuration.")
                pwd_input = gr.Textbox(label="Admin password", type="password")
                unlock_btn = gr.Button("Unlock Settings", variant="primary")
                status_msg = gr.Markdown()

            with gr.Column(visible=False) as settings_area:
                openai_key = gr.Textbox(label="OpenAI API Key")
                google_key = gr.Textbox(label="Google API Key")
                deepseek_key = gr.Textbox(label="DeepSeek API Key")
                lmstudio_url = gr.Textbox(label="LM Studio URL")
                save_btn = gr.Button("Save Changes", variant="secondary")
                save_status = gr.Markdown()

            unlock_btn.click(
                self.unlock_settings,
                inputs=pwd_input,
                outputs=[password_area, settings_area, status_msg],
            )

            save_btn.click(
                lambda *_: "💾 Settings saved (coming soon)",
                inputs=[openai_key, google_key, deepseek_key, lmstudio_url],
                outputs=save_status,
            )

        # settings_ui.render()

##################################################################
