"""
video_model_info_model.py
=========================

Metadata descriptor for video-capable multimodal models.
Structured similarly to LLMModelInfo but with
capabilities relevant to video ingestion and analysis.
"""

from dataclasses import dataclass
from typing import Optional
from enums.provider_enum import ProviderEnum


@dataclass
class VideoModelInfo:
    """
    Metadata/configuration descriptor for a video-capable multimodal model.

    Attributes:
        name:                     Unique identifier (e.g., "gemini-1.5-flash").
        provider:                 ProviderEnum specifying hosting/provider platform.

        display_name:             Optional user-friendly name for UI.
        description:              Optional longer explanation (e.g., latency/recommended use).
        favorite:                 Indicates preferred/default models.
        is_local:                 Whether this model runs locally or via API.

        supports_native_video:    True if the model accepts raw video input.
        supports_image:           Optional—whether it can ingest images.
        supports_audio:           Optional—whether it can ingest audio.
        max_video_duration:       Optional—max allowed video length in seconds.
        max_video_resolution:     Optional—e.g., "1080p", "4k".
    """

    # Core identity
    name: str
    provider: ProviderEnum

    # Display/UI helpers
    display_name: str = ""
    description: str = ""
    favorite: bool = False
    is_local: bool = False

    # Capabilities
    supports_native_video: bool = True
    supports_image: Optional[bool] = None
    supports_audio: Optional[bool] = None
    max_video_duration: Optional[int] = None          # seconds
    max_video_resolution: Optional[str] = None        # e.g. "720p", "1080p", "4k"
