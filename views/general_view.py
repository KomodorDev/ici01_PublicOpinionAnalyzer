# views/general_view.py
"""
general_view.py
===============

Renders the General interface using Gradio.
"""
import gradio as gr


class GeneralView:
    """Defines the Gradio layout for the General tab."""

    def render_general_view(self, controller=None, models=None, groups=None, prompt_styles=None):
        """
        Builds the Gradio components for the General tab.

        Features:
        - Textarea for multiple YouTube URLs (one per line)
        - Parse button to load videos
        - Left panel: scrollable list of videos
        - Right panel: selected video's URL and editable summary
        - Auto-generate summary button per video
        
        Args:
            controller: GeneralController instance for handling analysis
            models: List of ModelInfo objects
            groups: List of classification group names
            prompt_styles: List of prompt style names
        """

        gr.Markdown("### General Analysis Tab")

        # Input: Multiple YouTube URLs
        youtube_input = gr.Textbox(
            label="YouTube Video URLs",
            placeholder="Paste YouTube links here (one per line)...",
            lines=5,
            max_lines=15,
        )

        parse_button = gr.Button("Parse Videos", variant="secondary")

        # Two-column layout: list on left, details on right
        with gr.Row():
            # Left column: Video list (scrollable)
            with gr.Column(scale=1, min_width=300):
                gr.Markdown("#### Video List")
                video_list = gr.Radio(
                    choices=[],
                    label="",
                    interactive=True,
                    elem_id="video-list",
                )

            # Right column: Selected video details
            with gr.Column(scale=2, min_width=400):
                gr.Markdown("#### Selected Video")

                selected_url = gr.Textbox(
                    label="Video URL",
                    interactive=False,
                    placeholder="Select a video from the list...",
                )

                summary_box = gr.Textbox(
                    label="Summary",
                    placeholder="Enter summary manually or click 'Auto-Generate'...",
                    lines=6,
                    interactive=True,
                )

                auto_gen_btn = gr.Button(
                    "Auto-Generate Summary",
                    variant="secondary",
                    size="sm",
                )

        # Classification group selector — allow choosing a label group
        group_choices = []
        if groups:
            try:
                group_choices = list(groups)
            except Exception:
                group_choices = []

        group_selector = gr.Dropdown(
            choices=group_choices,
            label="Classification Group",
            value=group_choices[0] if group_choices else None,
            interactive=True,
        )

        # Prompt style selector
        prompt_choices = []
        if prompt_styles:
            try:
                prompt_choices = list(prompt_styles)
            except Exception:
                prompt_choices = []

        prompt_selector = gr.Dropdown(
            choices=prompt_choices,
            label="Prompt Style",
            value=prompt_choices[0] if prompt_choices else "default",
            interactive=True,
        )

        # Model selector — use models provided by the controller if available
        # Store models as State to preserve full ModelInfo objects
        models_state = gr.State(models or [])
        
        # Build display choices with provider info
        available_model_choices = []
        if models:
            for m in models:
                try:
                    # ModelInfo object with provider, id, and name
                    display_name = f"{m.provider}: {m.name}"
                    available_model_choices.append(display_name)
                except Exception:
                    display_name = str(m)
                    available_model_choices.append(display_name)

        # Fallback to static sample list
        if not available_model_choices:
            available_model_choices = ["openai: gpt-4", "openai: gpt-3.5-turbo"]
            
        model_selector = gr.Dropdown(
            choices=available_model_choices,
            multiselect=True,
            label="Select Models",
            value=[],
            interactive=True,
        )

        selected_models_text = gr.Markdown("No models selected yet.")

        def update_selection(selected):
            """Update selected models display."""
            if not selected:
                return "No models selected yet."
            return f"**{len(selected)}** model(s) selected: {', '.join(selected)}"

        model_selector.change(  # pylint: disable=no-member,too-many-function-args
            fn=update_selection,
            inputs=model_selector,
            outputs=selected_models_text,
        )

        run_button = gr.Button("Run Analysis", variant="primary")
        
        # Results display area
        progress_text = gr.Markdown("Ready to start analysis...")
        results_output = gr.JSON(label="Analysis Results", visible=False)
        results_download = gr.File(label="Download Results", visible=False)

        # --- Event Handlers ---

        # Store parsed video data (URL -> summary mapping)
        video_data = gr.State({})  # Dictionary: {url: summary}

        def parse_videos(urls_text):
            """Parse URLs and populate the video list."""
            if not urls_text or not urls_text.strip():
                return [], {}, ""

            urls = [url.strip() for url in urls_text.split("\n") if url.strip()]

            if not urls:
                return [], {}, ""

            # Create display labels (shortened URLs)
            video_choices = [
                f"Video {i+1}: {url[:40]}..." for i, url in enumerate(urls)
            ]

            # Initialize empty summaries
            data = {url: "" for url in urls}

            return (
                gr.Radio(
                    choices=video_choices,
                    value=video_choices[0] if video_choices else None,
                ),
                data,
                urls[0] if urls else "",
            )

        parse_button.click(  # pylint: disable=no-member,too-many-function-args
            fn=parse_videos,
            inputs=youtube_input,
            outputs=[video_list, video_data, selected_url],
        )

        def select_video(selected_label, data, urls_text):
            """
            When a video is selected from the list, show its URL and summary.
            """
            if not selected_label or not urls_text:
                return "", ""

            # Extract index from label (e.g., "Video 1: ..." -> index 0)
            try:
                video_num = int(selected_label.split(":")[0].replace("Video ", ""))
                urls = [url.strip() for url in urls_text.split("\n") if url.strip()]
                selected_url_val = urls[video_num - 1]
                summary = data.get(selected_url_val, "")
                return selected_url_val, summary
            except (ValueError, IndexError):
                return "", ""

        video_list.change(  # pylint: disable=no-member,too-many-function-args
            fn=select_video,
            inputs=[video_list, video_data, youtube_input],
            outputs=[selected_url, summary_box],
        )

        def generate_summary(url):
            """
            Placeholder for automatic summary generation.
            Replace with actual service call later.
            """
            if not url:
                return ""
            return f"[Auto-generated summary for {url[:50]}...]"

        auto_gen_btn.click(  # pylint: disable=no-member,too-many-function-args
            fn=generate_summary,
            inputs=selected_url,
            outputs=summary_box,
        )

        # Update stored summary when user edits
        def save_summary(url, summary, data):
            """Save edited summary back to state."""
            if url and url in data:
                data[url] = summary
            return data

        summary_box.change(  # pylint: disable=no-member,too-many-function-args
            fn=save_summary,
            inputs=[selected_url, summary_box, video_data],
            outputs=video_data,
        )

        # Run analysis handler
        def handle_run_analysis(
            data, 
            selected_model_names, 
            all_models, 
            prompt_style, 
            group_name
        ):
            """
            Handle the Run Analysis button click.
            
            Args:
                data: Dict of {url: summary}
                selected_model_names: List of display names (e.g., "openai: gpt-4")
                all_models: List of ModelInfo objects
                prompt_style: Selected prompt style name
                group_name: Selected classification group name
            """
            # Validation
            if not data or not any(data.values()):
                return (
                    "❌ Please add videos and summaries first!",
                    gr.JSON(visible=False),
                    gr.File(visible=False)
                )
            
            if not selected_model_names:
                return (
                    "❌ Please select at least one model!",
                    gr.JSON(visible=False),
                    gr.File(visible=False)
                )
            
            if not group_name:
                return (
                    "❌ Please select a classification group!",
                    gr.JSON(visible=False),
                    gr.File(visible=False)
                )
            
            if not controller:
                return (
                    "❌ Controller not initialized!",
                    gr.JSON(visible=False),
                    gr.File(visible=False)
                )
            
            # Convert display names back to (provider, model_id) tuples
            model_selections = []
            for display_name in selected_model_names:
                # Find matching ModelInfo object
                for model in all_models:
                    if f"{model.provider}: {model.name}" == display_name:
                        model_selections.append((model.provider, model.id))
                        break
            
            if not model_selections:
                return (
                    "❌ Could not resolve selected models!",
                    gr.JSON(visible=False),
                    gr.File(visible=False)
                )
            
            # Progress callback (for future streaming updates)
            progress_messages = []
            def progress_callback(current, total, message):
                progress_messages.append(f"[{current}/{total}] {message}")
                print(f"Progress: {message}")  # Log to console
            
            try:
                # Call controller's run_analysis
                results = controller.run_analysis(
                    summaries=data,
                    model_selections=model_selections,
                    prompt_style_name=prompt_style,
                    classification_group_name=group_name,
                    progress_callback=progress_callback
                )
                
                # Format results for display
                results_dict = []
                for analysis in results:
                    result_item = {
                        "url": analysis.content.url,
                        "title": analysis.content.title,
                        "summary": analysis.content.summary,
                        "comments_analyzed": len(analysis.comments),
                        "labels": [
                            {
                                "comment": c.text,
                                "labels": c.labels
                            }
                            for c in analysis.comments[:10]  # Show first 10
                        ]
                    }
                    results_dict.append(result_item)
                
                return (
                    "✅ Analysis completed successfully!",
                    gr.JSON(value=results_dict, visible=True),
                    gr.File(visible=False)  # TODO: Add CSV export
                )
                
            except Exception as e:
                return (
                    f"❌ Error during analysis: {str(e)}",
                    gr.JSON(visible=False),
                    gr.File(visible=False)
                )
        
        run_button.click(  # pylint: disable=no-member,too-many-function-args
            fn=handle_run_analysis,
            inputs=[
                video_data,
                model_selector,
                models_state,
                prompt_selector,
                group_selector
            ],
            outputs=[
                progress_text,
                results_output,
                results_download
            ]
        )

        # Layout footer
        with gr.Group():
            gr.Row([model_selector])  # pylint: disable=no-member,too-many-function-args
            gr.Row(
                [selected_models_text]
            )  # pylint: disable=no-member,too-many-function-args
            gr.Row([run_button])  # pylint: disable=no-member,too-many-function-args
