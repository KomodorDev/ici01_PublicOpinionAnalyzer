# services/video_analysis_service.py
"""
video_analysis_service.py
=========================

Service for analyzing YouTube videos using various AI providers.
"""
from typing import Optional, List, Dict, Any
from services.video_analysis.base_adapter import VideoAnalysisAdapter
from services.video_analysis.google_adapter import GoogleAdapter

##################################################################
class VideoAnalysisService:
    """Manages video analysis operations across multiple providers."""

    # Map of provider names to their adapters
    ADAPTER_REGISTRY = {
        'google': GoogleAdapter,
        'gemini': GoogleAdapter,  # Alias
    }

    # Models that support video analysis
    VIDEO_CAPABLE_MODELS = {
        'google': [
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-2.0-flash-exp',
            'gemini-2.0-pro-exp',
        ]
    }

    # ----------------------------------------------------------------
    def __init__(self, model_service, settings_service=None):
        """
        Initialize video analysis service.
        
        Args:
            model_service: ModelService instance for getting LLM clients
            settings_service: Optional SettingsService instance
        """
        self.model_service = model_service
        self.settings_service = settings_service
        self._adapters = {}  # Cache adapters

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
                available = ', '.join(self.ADAPTER_REGISTRY.keys())
                raise ValueError(
                    f"Unknown provider: {provider}. "
                    f"Available providers: {available}"
                )

            self._adapters[provider] = adapter_class(self.settings_service)

        return self._adapters[provider]

    # ----------------------------------------------------------------
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all models that support video analysis.
        
        Returns:
            List of dicts with model information:
            [
                {
                    'provider': 'google',
                    'model_id': 'gemini-1.5-flash',
                    'supports_native_video': True,
                    'available': True
                },
                ...
            ]
        """
        available_models = []

        for provider, model_ids in self.VIDEO_CAPABLE_MODELS.items():
            # Check if provider is configured
            try:
                adapter = self._get_adapter(provider)
                provider_available = True
            except Exception:
                provider_available = False

            for model_id in model_ids:
                model_info = {
                    'provider': provider,
                    'model_id': model_id,
                    'supports_native_video': True,  # All listed models support it
                    'available': provider_available
                }
                available_models.append(model_info)

        return available_models

    # ----------------------------------------------------------------
    def summarize(
        self,
        video_url: str,
        provider: str,
        model_id: str,
        custom_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Summarize a YouTube video.
        
        Args:
            video_url: YouTube video URL
            provider: Provider name ('google', 'gemini')
            model_id: Model identifier (e.g., 'gemini-1.5-flash')
            custom_prompt: Optional custom summarization prompt
            **kwargs: Additional arguments for model client
            
        Returns:
            Video summary as text
        """
        # Validate model supports video
        if not self._is_video_capable(provider, model_id):
            raise ValueError(
                f"Model {model_id} from {provider} does not support video analysis"
            )

        # Get adapter
        adapter = self._get_adapter(provider)

        # Get model client (may not be used by all adapters)
        client = None
        if not adapter.supports_native_video():
            client = self.model_service.get_model_client(
                provider, model_id, **kwargs
            )

        # Execute summarization
        return adapter.summarize(video_url, client, custom_prompt)

    # ----------------------------------------------------------------
    def analyze(
        self,
        video_url: str,
        provider: str,
        model_id: str,
        custom_prompt: str,
        **kwargs
    ) -> str:
        """
        Analyze video with custom prompt.
        
        Args:
            video_url: YouTube video URL
            provider: Provider name
            model_id: Model identifier
            custom_prompt: Custom analysis prompt
            **kwargs: Additional arguments for model client
            
        Returns:
            Analysis result as text
        """
        # Validate model supports video
        if not self._is_video_capable(provider, model_id):
            raise ValueError(
                f"Model {model_id} from {provider} does not support video analysis"
            )

        # Get adapter
        adapter = self._get_adapter(provider)

        # Get model client (may not be used by all adapters)
        client = None
        if not adapter.supports_native_video():
            client = self.model_service.get_model_client(
                provider, model_id, **kwargs
            )

        # Execute analysis
        return adapter.analyze(video_url, client, custom_prompt)

    # ----------------------------------------------------------------
    def get_key_points(
        self,
        video_url: str,
        provider: str,
        model_id: str,
        **kwargs
    ) -> str:
        """
        Extract key points from video.
        
        Args:
            video_url: YouTube video URL
            provider: Provider name
            model_id: Model identifier
            **kwargs: Additional arguments for model client
            
        Returns:
            Key points as text
        """
        prompt = (
            "List the key points discussed in this video. "
            "Format as a bulleted list with brief explanations for each point."
        )
        return self.analyze(video_url, provider, model_id, prompt, **kwargs)

    # ----------------------------------------------------------------
    def get_transcript_summary(
        self,
        video_url: str,
        provider: str,
        model_id: str,
        **kwargs
    ) -> str:
        """
        Get a detailed transcript-style summary.
        
        Args:
            video_url: YouTube video URL
            provider: Provider name
            model_id: Model identifier
            **kwargs: Additional arguments for model client
            
        Returns:
            Transcript summary
        """
        prompt = (
            "Provide a detailed transcript-style summary of this video, "
            "organized chronologically. Include timestamps or time references "
            "where possible."
        )
        return self.analyze(video_url, provider, model_id, prompt, **kwargs)

    # ----------------------------------------------------------------
    def _is_video_capable(self, provider: str, model_id: str) -> bool:
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
        return model_id in models

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
    print("="*60)
    print("Testing VideoAnalysisService")
    print("="*60)

    # Import here to avoid circular dependencies
    from services.model_service import ModelService

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
    models = video_service.list_available_models()
    for i, model in enumerate(models, 1):
        status = "✅ Available" if model['available'] else "❌ Not configured"
        print(f"\n  {i}. {model['provider']}/{model['model_id']}")
        print(f"     Status: {status}")
        print(f"     Native video: {model['supports_native_video']}")

    # Check if any models are available
    available_models = [m for m in models if m['available']]
    if not available_models:
        print("\n⚠️  No video-capable models configured!")
        print("Please configure API keys in Settings.")
        return

    # Test video analysis
    print("\n" + "="*60)
    print("Video Analysis Test")
    print("="*60)

    video_url = input("\nEnter YouTube URL to analyze (or press Enter to skip): ").strip()

    if video_url:
        # Use first available model
        test_model = available_models[0]
        provider = test_model['provider']
        model_id = test_model['model_id']

        print(f"\nUsing: {provider}/{model_id}")

        try:
            # Test summarization
            print("\n📹 Generating summary...")
            summary = video_service.summarize(
                video_url=video_url,
                provider=provider,
                model_id=model_id
            )

            print("\n✅ Summary:")
            print("-" * 60)
            print(summary)
            print("-" * 60)

            # Test key points extraction
            print("\n📝 Extracting key points...")
            key_points = video_service.get_key_points(
                video_url=video_url,
                provider=provider,
                model_id=model_id
            )

            print("\n✅ Key Points:")
            print("-" * 60)
            print(key_points)
            print("-" * 60)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)


if __name__ == "__main__":
    main()
