# services/video_analysis_service.py
"""
video_analysis_service.py
=========================

Service for analyzing YouTube videos using various AI providers.
"""

from typing import Optional, List

from enums import ProviderEnum
from models.domain.video_model_info_model import VideoModelInfo
from services.video_analysis.base_adapter import VideoAnalysisAdapter
from services.video_analysis.google_adapter import GoogleAdapter
from services import SettingsService, ModelService


##################################################################
class VideoAnalysisService:
    """Manages video analysis operations across multiple providers."""

    # Map of provider names to their adapters
    ADAPTER_REGISTRY = {
        "google": GoogleAdapter,
        "gemini": GoogleAdapter,  # Alias
    }

    # Models that support video analysis
    VIDEO_CAPABLE_MODELS = {
        "google": [
            "gemini-2.0-flash-exp",
        ]
    }

    # ----------------------------------------------------------------
    def __init__(
        self,
        model_service=None,
        settings_service=None,
    ):
        """
        Initialize video analysis service.

        Args:
            model_service: optional ModelService instance. If None, create one.
            settings_service: optional SettingsService instance. If None, create one.
        """

        # Lazy import to avoid circular dependencies if needed
        if model_service is None:
            model_service = ModelService()
        self.model_service = model_service

        if settings_service is None:
            settings_service = SettingsService()
        self.settings_service = settings_service

        # Adapter cache
        self._adapters = {}

    # ----------------------------------------------------------------
    def _get_adapter(self, provider: str) -> VideoAnalysisAdapter:
        """
        Get or create adapter for provider.

        Args:
            provider: Provider name

        Returns:
            Adapter instance
        """
        provider = provider.lower()

        if provider not in self._adapters:
            adapter_class = self.ADAPTER_REGISTRY.get(provider)

            if not adapter_class:
                available = ", ".join(self.ADAPTER_REGISTRY.keys())
                raise ValueError(
                    f"Unknown provider: {provider}. "
                    f"Available providers: {available}"
                )

            self._adapters[provider] = adapter_class(self.settings_service)

        return self._adapters[provider]

    # ----------------------------------------------------------------
    def list_available_video_models(self) -> List[VideoModelInfo]:
        """
        Return all models that support video analysis,
        represented as VideoModelInfo domain models.
        """
        models: list[VideoModelInfo] = []

        for provider_key, model_names in self.VIDEO_CAPABLE_MODELS.items():

            # Convert provider (str or enum) → ProviderEnum
            if isinstance(provider_key, ProviderEnum):
                provider_enum = provider_key
            else:
                provider_enum = ProviderEnum(provider_key)

            for model_name in model_names:
                models.append(
                    VideoModelInfo(
                        name=model_name,
                        provider=provider_enum,
                        display_name=model_name,
                        supports_native_video=True,
                    )
                )

        return models

    # ----------------------------------------------------------------
    def summarize(
        self,
        video_url: str,
        provider: str,
        model_name: str,
        custom_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Summarize a YouTube video.

        Args:
            video_url: YouTube video URL
            provider: Provider name ('google', 'gemini')
            model_name: Model name (e.g., 'gemini-1.5-flash')
            custom_prompt: Optional custom summarization prompt
            max_tokens: Maximum tokens in response (None = provider default)
            **kwargs: Additional arguments for model client

        Returns:
            Video summary as text
        """
        # Validate model supports video
        if not self._is_video_capable(provider, model_name):
            raise ValueError(
                f"Model {model_name} from {provider} does not support video analysis"
            )

        # Get adapter
        adapter = self._get_adapter(provider)

        # Execute summarization with model_name
        return adapter.summarize(video_url, model_name, custom_prompt, max_tokens)

    # ----------------------------------------------------------------
    def analyze(
        self,
        video_url: str,
        provider: str,
        model_name: str,
        custom_prompt: str,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Analyze video with custom prompt.

        Args:
            video_url: YouTube video URL
            provider: Provider name
            model_name: Model name
            custom_prompt: Custom analysis prompt
            max_tokens: Maximum tokens in response (None = provider default)
            **kwargs: Additional arguments for model client

        Returns:
            Analysis result as text
        """
        # Validate model supports video
        if not self._is_video_capable(provider, model_name):
            raise ValueError(
                f"Model {model_name} from {provider} does not support video analysis"
            )

        # Get adapter
        adapter = self._get_adapter(provider)

        # Execute analysis with model_name
        return adapter.analyze(video_url, model_name, custom_prompt, max_tokens)

    # ----------------------------------------------------------------
    def get_key_points(
        self,
        video_url: str,
        provider: str,
        model_name: str,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Extract key points from video.

        Args:
            video_url: YouTube video URL
            provider: Provider name
            model_name: Model name
            max_tokens: Maximum tokens in response (None = provider default)
            **kwargs: Additional arguments for model client

        Returns:
            Key points as text
        """
        prompt = (
            "List the key points discussed in this video. "
            "Format as a bulleted list with brief explanations for each point."
        )
        return self.analyze(video_url, provider, model_name, prompt, max_tokens, **kwargs)

    # ----------------------------------------------------------------
    def get_transcript_summary(
        self,
        video_url: str,
        provider: str,
        model_name: str,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Get a detailed transcript-style summary.

        Args:
            video_url: YouTube video URL
            provider: Provider name
            model_name: Model name
            max_tokens: Maximum tokens in response (None = provider default)
            **kwargs: Additional arguments for model client

        Returns:
            Transcript summary
        """
        prompt = (
            "Provide a detailed transcript-style summary of this video, "
            "organized chronologically. Include timestamps or time references "
            "where possible."
        )
        return self.analyze(video_url, provider, model_name, prompt, max_tokens, **kwargs)

    # ----------------------------------------------------------------
    def _is_video_capable(self, provider: str, model_name: str) -> bool:
        """
        Check if a model supports video analysis.

        Args:
            provider: Provider name
            model_id: Model identifier

        Returns:
            True if model supports video
        """
        provider = provider.lower()
        models = self.VIDEO_CAPABLE_MODELS.get(provider, [])
        return model_name in models

    # ----------------------------------------------------------------
    @classmethod
    def list_supported_providers(cls) -> List[str]:
        """Get list of supported providers."""
        return list(cls.ADAPTER_REGISTRY.keys())


##################################################################


##################################################################
# Test Main
##################################################################
def main():
    """Test the VideoAnalysisService."""
    print("=" * 60)
    print("Testing VideoAnalysisService")
    print("=" * 60)

    # Import here to avoid circular dependencies


    # Create services
    print("\nInitializing services...")
    model_service = ModelService()
    video_service = VideoAnalysisService(model_service)

    # List supported providers
    print("\nSupported providers:")
    for provider in video_service.list_supported_providers():
        print(f"  - {provider}")

    # List available models
    print("\nAvailable video-capable models:")

    models = video_service.list_available_video_models()

    for i, model in enumerate(models, start=1):
        print(f"\n  {i}. {model.provider}/{model.name}")
        print(f"     Native video: {getattr(model, 'supports_native_video', False)}")

# No availability check an

    # Test video analysis
    print("\n" + "=" * 60)
    print("Video Analysis Test")
    print("=" * 60)

    video_url = input(
        "\nEnter YouTube URL to analyze (or press Enter to skip): "
    ).strip()

    if video_url:
        # Use first available model
        test_model = models[0]
        provider = test_model.provider
        model_name = test_model.name

        print(f"\nUsing: {provider}/{model_name}")

        try:
            # Test summarization
            print("\n📹 Generating summary...")
            summary = video_service.summarize(
                video_url=video_url, provider=provider, model_name=model_name
            )

            print("\n✅ Summary:")
            print("-" * 60)
            print(summary)
            print("-" * 60)

            # Test key points extraction
            print("\n📝 Extracting key points...")
            key_points = video_service.get_key_points(
                video_url=video_url, provider=provider, model_name=model_name
            )

            print("\n✅ Key Points:")
            print("-" * 60)
            print(key_points)
            print("-" * 60)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

# python -m services.video_analysis_service
