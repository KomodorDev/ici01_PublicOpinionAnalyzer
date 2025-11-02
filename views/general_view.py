# views/general_view.py
"""
general_view.py
===============

Renders the General interface using Gradio.
"""
import gradio as gr


class GeneralView:
    """Defines the Gradio layout for the General tab."""

    def render_general_view(self, models=None, groups=None):
        """
        Builds the Gradio components for the General tab.

        Features:
        - Textarea for multiple YouTube URLs (one per line)
        - Parse button to load videos
        - Left panel: scrollable list of videos
        - Right panel: selected video's URL and editable summary
        - Auto-generate summary button per video
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

        # Model selector — use models provided by the controller if available
        # `models` may be a list of ModelInfo objects or simple strings.
        available_models = []
        if models:
            for m in models:
                try:
                    # ModelInfo-like object
                    name = getattr(m, "name", None) or getattr(m, "id", None) or str(m)
                except Exception:
                    name = str(m)
                if name:
                    available_models.append(name)

        # Fallback to static sample list
        if not available_models:
            available_models = ["Model A", "Model B", "Model C", "Model D"]
        model_selector = gr.Dropdown(
            choices=available_models,
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

        # Layout footer
        with gr.Group():
            gr.Row([model_selector])  # pylint: disable=no-member,too-many-function-args
            gr.Row(
                [selected_models_text]
            )  # pylint: disable=no-member,too-many-function-args
            gr.Row([run_button])  # pylint: disable=no-member,too-many-function-args
