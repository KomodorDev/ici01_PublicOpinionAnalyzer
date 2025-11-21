# views/settings_view.py
"""
settings_view.py
================

Renders the Advanced Settings interface using Gradio.

Displays API key configuration (masked for security) and local
provider URLs with save functionality.

Follows the same pattern as AnalysisView:
- Receives ViewModel for initial state
- Receives callable functions (wirebacks) from Controller
- Defines layout first, then wireback functions, then connects buttons
"""

from typing import Callable
import gradio as gr

from models.view_models.settings import SettingsViewModel


##################################################################
class SettingsView:
    """
    Gradio view for managing Advanced Settings.
    
    Parameters (via `render_settings_view`)
    ---------------------------------------
    view_model : SettingsViewModel
        Snapshot of the current settings state used to populate the UI on first render.
        This includes:
            - masked API keys for all providers
            - local provider URLs (LM Studio, Ollama)
            - provider status information
    
    on_api_key_saved : Callable[[str, str], SettingsViewModel]
        Controller callback for saving an API key.
        Called with:
            provider_name: str    - provider identifier (e.g., "openai", "anthropic")
            api_key: str          - new API key value
        Returns:
            Updated SettingsViewModel with new masked keys and statuses.
    
    on_provider_url_saved : Callable[[str, str], SettingsViewModel]
        Controller callback for saving a provider URL.
        Called with:
            provider_name: str    - provider identifier (e.g., "lmstudio", "ollama")
            url: str              - new base URL
        Returns:
            Updated SettingsViewModel with new URL and statuses.
    """

    # ================================================================
    # ENTRY POINT
    # ================================================================
    def render_settings_view(
        self,
        *,
        view_model: SettingsViewModel,
        on_api_key_saved: Callable[[str, str], SettingsViewModel],
        on_provider_url_saved: Callable[[str, str], SettingsViewModel],
    ) -> None:
        """
        Render the complete Settings management view using Gradio components.
        
        This method builds the layout (API key inputs, provider URL inputs)
        and wires all user interactions to the provided controller callbacks.
        
        The `view_model` snapshot is used to populate the UI on first render;
        subsequent updates are driven via the callbacks.
        """
        
        # ================================================================
        # LAYOUT
        # ================================================================
        with gr.Blocks() as settings_ui:
            gr.Markdown("## ⚙️ Advanced Settings")
            gr.Markdown("Configure API keys and local provider URLs. Keys are masked for security.")

            # API Keys Section
            gr.Markdown("### 🔑 API Keys")
            gr.Markdown("*Enter new key to update. Masked keys (****) cannot be saved.*")

            with gr.Group():
                # OpenAI
                openai_status = "✅" if view_model.provider_statuses.get("openai", {}).get("available") else "⚠️"
                openai_input = gr.Textbox(
                    label=f"{openai_status} OpenAI API Key",
                    value=view_model.masked_api_keys.get("openai", "API_KEY"),
                    placeholder="sk-proj-...",
                )
                openai_save_btn = gr.Button("Save OpenAI Key", size="sm")
                openai_status_msg = gr.Markdown()

                # Anthropic
                anthropic_status = "✅" if view_model.provider_statuses.get("anthropic", {}).get("available") else "⚠️"
                anthropic_input = gr.Textbox(
                    label=f"{anthropic_status} Anthropic API Key",
                    value=view_model.masked_api_keys.get("anthropic", "API_KEY"),
                    placeholder="sk-ant-...",
                )
                anthropic_save_btn = gr.Button("Save Anthropic Key", size="sm")
                anthropic_status_msg = gr.Markdown()

                # Google
                google_status = "✅" if view_model.provider_statuses.get("google", {}).get("available") else "⚠️"
                google_input = gr.Textbox(
                    label=f"{google_status} Google API Key (Gemini)",
                    value=view_model.masked_api_keys.get("google", "API_KEY"),
                    placeholder="AIza...",
                )
                google_save_btn = gr.Button("Save Google Key", size="sm")
                google_status_msg = gr.Markdown()

                # DeepSeek
                deepseek_status = "✅" if view_model.provider_statuses.get("deepseek", {}).get("available") else "⚠️"
                deepseek_input = gr.Textbox(
                    label=f"{deepseek_status} DeepSeek API Key",
                    value=view_model.masked_api_keys.get("deepseek", "API_KEY"),
                    placeholder="sk-...",
                )
                deepseek_save_btn = gr.Button("Save DeepSeek Key", size="sm")
                deepseek_status_msg = gr.Markdown()

            # Local Provider URLs Section
            gr.Markdown("### 🖥️ Local Provider URLs")
            gr.Markdown("*Configure base URLs for locally running model servers.*")

            with gr.Group():
                # LM Studio
                lmstudio_status = "✅" if view_model.provider_statuses.get("lmstudio", {}).get("available") else "⚠️"
                lmstudio_input = gr.Textbox(
                    label=f"{lmstudio_status} LM Studio URL",
                    value=view_model.lmstudio_url or "http://localhost:1234/v1",
                    placeholder="http://localhost:1234/v1"
                )
                lmstudio_save_btn = gr.Button("Save LM Studio URL", size="sm")
                lmstudio_status_msg = gr.Markdown()

                # Ollama
                ollama_status = "✅" if view_model.provider_statuses.get("ollama", {}).get("available") else "⚠️"
                ollama_input = gr.Textbox(
                    label=f"{ollama_status} Ollama URL",
                    value=view_model.ollama_url or "http://localhost:11434",
                    placeholder="http://localhost:11434"
                )
                ollama_save_btn = gr.Button("Save Ollama URL", size="sm")
                ollama_status_msg = gr.Markdown()

        # ================================================================
        # WIRING
        # ================================================================
        
        # ----------------------------------------------------------------
        def _handle_openai_key_saved(api_key: str):
            """Wireback for OpenAI API key save button."""
            if not api_key or api_key.strip() == "" or api_key == "API_KEY":
                return (
                    gr.update(value=f"⚠️ Please enter a valid OpenAI API key"),
                    gr.update()  # Keep input unchanged
                )
            
            if "***" in api_key or "****" in api_key:
                return (
                    gr.update(value=f"⚠️ Please enter the actual API key, not the masked version"),
                    gr.update()  # Keep input unchanged
                )
            
            vm = on_api_key_saved("openai", api_key)
            status_icon = "✅" if vm.provider_statuses.get("openai", {}).get("available") else "⚠️"
            new_masked_key = vm.masked_api_keys.get("openai", "API_KEY")
            
            # Use info_message or error_message from ViewModel if available
            status_msg = vm.info_message or vm.error_message or vm.provider_statuses.get('openai', {}).get('message', 'Saved successfully!')
            
            return (
                gr.update(value=status_msg),
                gr.update(label=f"{status_icon} OpenAI API Key", value=new_masked_key)
            )
        
        # ----------------------------------------------------------------
        def _handle_anthropic_key_saved(api_key: str):
            """Wireback for Anthropic API key save button."""
            if not api_key or api_key.strip() == "" or api_key == "API_KEY":
                return (
                    gr.update(value=f"⚠️ Please enter a valid Anthropic API key"),
                    gr.update()  # Keep input unchanged
                )
            
            if "***" in api_key or "****" in api_key:
                return (
                    gr.update(value=f"⚠️ Please enter the actual API key, not the masked version"),
                    gr.update()  # Keep input unchanged
                )
            
            vm = on_api_key_saved("anthropic", api_key)
            status_icon = "✅" if vm.provider_statuses.get("anthropic", {}).get("available") else "⚠️"
            new_masked_key = vm.masked_api_keys.get("anthropic", "API_KEY")
            
            status_msg = vm.info_message or vm.error_message or vm.provider_statuses.get('anthropic', {}).get('message', 'Saved successfully!')
            
            return (
                gr.update(value=status_msg),
                gr.update(label=f"{status_icon} Anthropic API Key", value=new_masked_key)
            )
        
        # ----------------------------------------------------------------
        def _handle_google_key_saved(api_key: str):
            """Wireback for Google API key save button."""
            if not api_key or api_key.strip() == "" or api_key == "API_KEY":
                return (
                    gr.update(value=f"⚠️ Please enter a valid Google API key"),
                    gr.update()  # Keep input unchanged
                )
            
            if "***" in api_key or "****" in api_key:
                return (
                    gr.update(value=f"⚠️ Please enter the actual API key, not the masked version"),
                    gr.update()  # Keep input unchanged
                )
            
            vm = on_api_key_saved("google", api_key)
            status_icon = "✅" if vm.provider_statuses.get("google", {}).get("available") else "⚠️"
            new_masked_key = vm.masked_api_keys.get("google", "API_KEY")
            
            status_msg = vm.info_message or vm.error_message or vm.provider_statuses.get('google', {}).get('message', 'Saved successfully!')
            
            return (
                gr.update(value=status_msg),
                gr.update(label=f"{status_icon} Google API Key (Gemini)", value=new_masked_key)
            )
        
        # ----------------------------------------------------------------
        def _handle_deepseek_key_saved(api_key: str):
            """Wireback for DeepSeek API key save button."""
            if not api_key or api_key.strip() == "" or api_key == "API_KEY":
                return (
                    gr.update(value=f"⚠️ Please enter a valid DeepSeek API key"),
                    gr.update()  # Keep input unchanged
                )
            
            if "***" in api_key or "****" in api_key:
                return (
                    gr.update(value=f"⚠️ Please enter the actual API key, not the masked version"),
                    gr.update()  # Keep input unchanged
                )
            
            vm = on_api_key_saved("deepseek", api_key)
            status_icon = "✅" if vm.provider_statuses.get("deepseek", {}).get("available") else "⚠️"
            new_masked_key = vm.masked_api_keys.get("deepseek", "API_KEY")
            
            status_msg = vm.info_message or vm.error_message or vm.provider_statuses.get('deepseek', {}).get('message', 'Saved successfully!')
            
            return (
                gr.update(value=status_msg),
                gr.update(label=f"{status_icon} DeepSeek API Key", value=new_masked_key)
            )
        
        # ----------------------------------------------------------------
        def _handle_lmstudio_url_saved(url: str):
            """Wireback for LM Studio URL save button."""
            if not url or url.strip() == "":
                return (
                    gr.update(value=f"⚠️ LM Studio URL cannot be empty"),
                    gr.update()  # Keep input unchanged
                )
            
            vm = on_provider_url_saved("lmstudio", url)
            status_icon = "✅" if vm.provider_statuses.get("lmstudio", {}).get("available") else "⚠️"
            new_url = vm.lmstudio_url or "http://localhost:1234/v1"
            
            status_msg = vm.info_message or vm.error_message or vm.provider_statuses.get('lmstudio', {}).get('message', 'Saved successfully!')
            
            return (
                gr.update(value=status_msg),
                gr.update(label=f"{status_icon} LM Studio URL", value=new_url)
            )
        
        # ----------------------------------------------------------------
        def _handle_ollama_url_saved(url: str):
            """Wireback for Ollama URL save button."""
            if not url or url.strip() == "":
                return (
                    gr.update(value=f"⚠️ Ollama URL cannot be empty"),
                    gr.update()  # Keep input unchanged
                )
            
            vm = on_provider_url_saved("ollama", url)
            status_icon = "✅" if vm.provider_statuses.get("ollama", {}).get("available") else "⚠️"
            new_url = vm.ollama_url or "http://localhost:11434"
            
            status_msg = vm.info_message or vm.error_message or vm.provider_statuses.get('ollama', {}).get('message', 'Saved successfully!')
            
            return (
                gr.update(value=status_msg),
                gr.update(label=f"{status_icon} Ollama URL", value=new_url)
            )
        
        # Wire up buttons
        openai_save_btn.click(
            _handle_openai_key_saved,
            inputs=openai_input,
            outputs=[openai_status_msg, openai_input]
        )
        
        anthropic_save_btn.click(
            _handle_anthropic_key_saved,
            inputs=anthropic_input,
            outputs=[anthropic_status_msg, anthropic_input]
        )
        
        google_save_btn.click(
            _handle_google_key_saved,
            inputs=google_input,
            outputs=[google_status_msg, google_input]
        )
        
        deepseek_save_btn.click(
            _handle_deepseek_key_saved,
            inputs=deepseek_input,
            outputs=[deepseek_status_msg, deepseek_input]
        )
        
        lmstudio_save_btn.click(
            _handle_lmstudio_url_saved,
            inputs=lmstudio_input,
            outputs=[lmstudio_status_msg, lmstudio_input]
        )
        
        ollama_save_btn.click(
            _handle_ollama_url_saved,
            inputs=ollama_input,
            outputs=[ollama_status_msg, ollama_input]
        )

##################################################################
