"""
Memory Provider Module

This module provides a pluggable memory provider architecture for AIOS,
enabling users to choose between different memory backends (in-house, Mem0, Zep).
"""

__all__ = [
    "MemoryProvider",
    "InHouseProvider",
    "Mem0Provider",
    "ZepProvider",
    "ProviderFactory",
    "ProviderInitializationError",
    "ProviderNotFoundError",
]


class ProviderInitializationError(Exception):
    """Raised when a provider fails to initialize."""
    
    def __init__(self, provider_type: str, reason: str):
        self.provider_type = provider_type
        self.reason = reason
        super().__init__(f"Failed to initialize {provider_type} provider: {reason}")


class ProviderNotFoundError(Exception):
    """Raised when an unknown provider type is requested."""
    
    def __init__(self, provider_type: str, available: list):
        self.provider_type = provider_type
        self.available = available
        super().__init__(
            f"Unknown provider type: {provider_type}. "
            f"Available providers: {available}"
        )


from .base import MemoryProvider
from .in_house import InHouseProvider
from .mem0 import Mem0Provider
from .zep import ZepProvider
from .factory import ProviderFactory
