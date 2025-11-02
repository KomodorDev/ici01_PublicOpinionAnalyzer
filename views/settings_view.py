# views/settings_view.py
"""
settings_view.py
================

Renders the Advanced Settings interface using Gradio.

Displays API key configuration (masked for security) and local
provider URLs with save functionality.
"""

import gradio as gr


##################################################################
class SettingsView:
    """Renders the Advanced Settings interface."""

    # ----------------------------------------------------------------
    def __init__(self, controller):
        """
        Initialize the settings view.
        
        Args:
            controller: SettingsController instance for handling actions
        """
        self.controller = controller

    # ----------------------------------------------------------------
    def save_api_key(self, provider_name: str, api_key: str):
        """
        Save an API key via the controller.
        
        Args:
            provider_name: Provider identifier
            api_key: New API key value
            
        Returns:
            Status message string
        """
        if not api_key or api_key.strip() == "" or api_key == "API_KEY":
            return f"⚠️ Please enter a valid {provider_name.title()} API key"

        # Don't save if it's still masked (starts with *** or contains ***)
        if "***" in api_key or "****" in api_key:
            return f"⚠️ Please enter the actual API key, not the masked version"

        success, message = self.controller.update_api_key(provider_name, api_key)

        if success:
            return f"✅ {message}"
        else:
            return f"❌ {message}"

    # ----------------------------------------------------------------
    def save_provider_url(self, provider_name: str, url: str):
        """
        Save a provider URL via the controller.
        
        Args:
            provider_name: Provider identifier
            url: New base URL
            
        Returns:
            Status message string
        """
        if not url or url.strip() == "":
            return f"⚠️ {provider_name.title()} URL cannot be empty"

        success, message = self.controller.update_provider_url(provider_name, url)

        if success:
            return f"✅ {message}"
        else:
            return f"❌ {message}"

    # ----------------------------------------------------------------
    def render_settings_view(self, masked_keys, lmstudio_url, ollama_url, provider_statuses):
        """
        Construct the UI layout for the Advanced Settings tab.
        
        Args:
            masked_keys: Dictionary of provider names to masked API keys
            lmstudio_url: Current LM Studio URL
            ollama_url: Current Ollama URL
            provider_statuses: Dictionary of provider status information
        """
        with gr.Blocks() as settings_ui:
            gr.Markdown("## ⚙️ Advanced Settings")
            gr.Markdown("Configure API keys and local provider URLs. Keys are masked for security.")

            # API Keys Section
            gr.Markdown("### 🔑 API Keys")
            gr.Markdown("*Enter new key to update. Masked keys (****) cannot be saved.*")

            with gr.Group():
                # OpenAI
                openai_status = "✅" if provider_statuses.get("openai", {}).get("available") else "⚠️"
                openai_input = gr.Textbox(
                    label=f"{openai_status} OpenAI API Key",
                    value=masked_keys.get("openai", "API_KEY"),
                    placeholder="sk-proj-...",
                )
                openai_save_btn = gr.Button("Save OpenAI Key", size="sm")
                openai_status_msg = gr.Markdown()

                # Anthropic
                anthropic_status = "✅" if provider_statuses.get("anthropic", {}).get("available") else "⚠️"
                anthropic_input = gr.Textbox(
                    label=f"{anthropic_status} Anthropic API Key",
                    value=masked_keys.get("anthropic", "API_KEY"),
                    placeholder="sk-ant-...",
                )
                anthropic_save_btn = gr.Button("Save Anthropic Key", size="sm")
                anthropic_status_msg = gr.Markdown()

                # Google
                google_status = "✅" if provider_statuses.get("google", {}).get("available") else "⚠️"
                google_input = gr.Textbox(
                    label=f"{google_status} Google API Key (Gemini)",
                    value=masked_keys.get("google", "API_KEY"),
                    placeholder="AIza...",
                )
                google_save_btn = gr.Button("Save Google Key", size="sm")
                google_status_msg = gr.Markdown()

                # DeepSeek
                deepseek_status = "✅" if provider_statuses.get("deepseek", {}).get("available") else "⚠️"
                deepseek_input = gr.Textbox(
                    label=f"{deepseek_status} DeepSeek API Key",
                    value=masked_keys.get("deepseek", "API_KEY"),
                    placeholder="sk-...",
                )
                deepseek_save_btn = gr.Button("Save DeepSeek Key", size="sm")
                deepseek_status_msg = gr.Markdown()

            # Local Provider URLs Section
            gr.Markdown("### 🖥️ Local Provider URLs")
            gr.Markdown("*Configure base URLs for locally running model servers.*")

            with gr.Group():
                # LM Studio
                lmstudio_status = "✅" if provider_statuses.get("lmstudio", {}).get("available") else "⚠️"
                lmstudio_input = gr.Textbox(
                    label=f"{lmstudio_status} LM Studio URL",
                    value=lmstudio_url or "http://localhost:1234/v1",
                    placeholder="http://localhost:1234/v1"
                )
                lmstudio_save_btn = gr.Button("Save LM Studio URL", size="sm")
                lmstudio_status_msg = gr.Markdown()

                # Ollama
                ollama_status = "✅" if provider_statuses.get("ollama", {}).get("available") else "⚠️"
                ollama_input = gr.Textbox(
                    label=f"{ollama_status} Ollama URL",
                    value=ollama_url or "http://localhost:11434",
                    placeholder="http://localhost:11434"
                )
                ollama_save_btn = gr.Button("Save Ollama URL", size="sm")
                ollama_status_msg = gr.Markdown()

            # Wire up individual save buttons
            openai_save_btn.click(
                lambda key: self.save_api_key("openai", key),
                inputs=openai_input,
                outputs=openai_status_msg
            )

            anthropic_save_btn.click(
                lambda key: self.save_api_key("anthropic", key),
                inputs=anthropic_input,
                outputs=anthropic_status_msg
            )

            google_save_btn.click(
                lambda key: self.save_api_key("google", key),
                inputs=google_input,
                outputs=google_status_msg
            )

            deepseek_save_btn.click(
                lambda key: self.save_api_key("deepseek", key),
                inputs=deepseek_input,
                outputs=deepseek_status_msg
            )

            lmstudio_save_btn.click(
                lambda url: self.save_provider_url("lmstudio", url),
                inputs=lmstudio_input,
                outputs=lmstudio_status_msg
            )

            ollama_save_btn.click(
                lambda url: self.save_provider_url("ollama", url),
                inputs=ollama_input,
                outputs=ollama_status_msg
            )

        return settings_ui

    # ----------------------------------------------------------------

##################################################################
