# services/video_analysis/gemini_adapter.py
"""
gemini_adapter.py
=================

Google Gemini implementation for video analysis.
"""
from typing import Optional
from google import genai
from .base_adapter import VideoAnalysisAdapter


##################################################################
class GoogleAdapter(VideoAnalysisAdapter):
    """Uses Google's Gemini for direct YouTube video analysis."""

    # ----------------------------------------------------------------
    def __init__(self, settings_service=None):
        """
        Initialize Google adapter.

        Args:
            settings_service: SettingsService instance for API key access
        """
        if settings_service is None:
            from services.settings_service import (
                SettingsService,
            )  # pylint: disable=import-outside-toplevel

            settings_service = SettingsService()

        self.settings_service = settings_service
        self.provider_name = "google"

    # ----------------------------------------------------------------
    @property
    def api_key(self):
        """Get fresh API key from settings."""
        return self.settings_service.get_api_key(self.provider_name)

    # ----------------------------------------------------------------
    def supports_native_video(self) -> bool:
        """Gemini supports native video analysis."""
        return True

    # ----------------------------------------------------------------
    def summarize(
        self,
        video_url: str,
        client=None,  # Unused - kept for interface consistency
        custom_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Summarize a YouTube video using Gemini.

        Note: Uses native Gemini API (not LangChain client) because
        video analysis requires file_data parameter.

        Args:
            video_url: YouTube video URL
            client: Unused (kept for interface compatibility)
            custom_prompt: Optional custom prompt
            max_tokens: Maximum tokens in response

        Returns:
            Video summary
        """
        try:
            # Must use native API for video
            genai_client = genai.Client(api_key=self.api_key)

            prompt = custom_prompt or (
                "Summarize this video in detail, highlighting the key points "
                "and main takeaways. Structure your summary with clear sections. "
                "Provide the summary directly without any preamble or meta-commentary."
            )

            # Build generation config
            generation_config = {}
            if max_tokens is not None:
                generation_config["max_output_tokens"] = max_tokens

            response = genai_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[{"text": prompt}, {"file_data": {"file_uri": video_url}}],
                config=generation_config if generation_config else None,
            )

            return response.text

        except Exception as e:
            raise ValueError(f"Error summarizing video with Gemini: {str(e)}")

    # ----------------------------------------------------------------
    def analyze(
        self,
        video_url: str,
        client=None,  # Unused - Gemini uses native API for video
        custom_prompt: str = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Analyze video with custom prompt.

        Args:
            video_url: YouTube video URL
            client: Unused (kept for interface compatibility)
            custom_prompt: Custom analysis prompt
            max_tokens: Maximum tokens in response

        Returns:
            Analysis result
        """
        if not custom_prompt:
            raise ValueError("custom_prompt is required for analyze()")

        return self.summarize(video_url, client, custom_prompt, max_tokens)


##################################################################

##################################################################
# Test Main
##################################################################
def main():
    """
    Test the GoogleAdapter by summarizing a YouTube video.

    This function:
    - Creates a GoogleAdapter instance
    - Tests connection to Google API
    - Summarizes a sample YouTube video
    - Tests custom analysis with max_tokens limit

    Run this script as a main module to verify Google video analysis integration.
    """
    print("=" * 60)
    print("Testing GoogleAdapter")
    print("=" * 60)

    adapter = GoogleAdapter()

    # Check API key and availability
    print("\nChecking Google API availability...")
    try:
        # Test if we can access the API
        genai_client = genai.Client(api_key=adapter.api_key)
        list(genai_client.models.list())
        print("✅ Google API is available")
    except Exception as e:
        print(f"❌ Google API not available: {e}")
        print("\n⚠️  Please configure your Google API key in Settings or .env file.")
        return

    # Test video URL
    test_video_url = "https://www.youtube.com/watch?v=m9coOXt5nuw"
    print(f"\nTest video: {test_video_url}")

    # Test 1: Basic summarization
    print("\n" + "=" * 60)
    print("Test 1: Basic Video Summarization")
    print("=" * 60)

    try:
        print("\n📹 Generating summary...")
        summary = adapter.summarize(video_url=test_video_url)

        print("\n✅ Summary:")
        print("-" * 60)
        print(summary)
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ Summarization failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Custom prompt with token limit
    print("\n" + "=" * 60)
    print("Test 2: Custom Analysis with Token Limit")
    print("=" * 60)

    try:
        print("\n📝 Analyzing with custom prompt (max 100 tokens)...")
        custom_analysis = adapter.analyze(
            video_url=test_video_url,
            custom_prompt="Describe what happens in this video in 2-3 sentences.",
            max_tokens=100,
        )

        print("\n✅ Custom Analysis:")
        print("-" * 60)
        print(custom_analysis)
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ Custom analysis failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Detailed analysis
    print("\n" + "=" * 60)
    print("Test 3: Detailed Analysis")
    print("=" * 60)

    try:
        print("\n🔍 Generating detailed analysis...")
        detailed_analysis = adapter.analyze(
            video_url=test_video_url,
            custom_prompt=(
                "Provide a detailed analysis of this video including: "
                "1) Visual elements, 2) Audio/dialogue, 3) Overall message or purpose"
            ),
            max_tokens=500,
        )

        print("\n✅ Detailed Analysis:")
        print("-" * 60)
        print(detailed_analysis)
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ Detailed analysis failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

# python -m services.video_analysis.google_adapter
