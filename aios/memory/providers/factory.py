"""
ProviderFactory - Factory for creating memory provider instances.

This module provides a factory class that creates and configures memory
provider instances based on the specified provider type. It supports
extensibility through runtime registration of new provider types.
"""
from typing import Dict, Any, Type

from .base import MemoryProvider
from .in_house import InHouseProvider
from .mem0 import Mem0Provider
from .zep import ZepProvider


class ProviderFactory:
    """Factory for creating memory provider instances.
    
    This factory centralizes provider instantiation and configuration,
    ensuring consistent creation of memory providers across the system.
    
    The factory supports:
    - Creating providers by type name ("in-house", "mem0", "zep")
    - Passing provider-specific configuration to the created provider
    - Runtime registration of new provider types for extensibility
    
    Class Attributes:
        PROVIDERS: Dictionary mapping provider type names to provider classes
    """
    
    PROVIDERS: Dict[str, Type[MemoryProvider]] = {
        "in-house": InHouseProvider,
        "mem0": Mem0Provider,
        "zep": ZepProvider
    }
    
    @classmethod
    def create(cls, provider_type: str, config: Dict[str, Any]) -> MemoryProvider:
        """Create and initialize a memory provider.
        
        Creates an instance of the specified provider type and initializes
        it with the provided configuration.
        
        Args:
            provider_type: The type of provider to create. Must be one of
                          the registered provider types ("in-house", "mem0", "zep")
                          or a custom registered type.
            config: Provider-specific configuration dictionary to pass to
                   the provider's initialize() method.
        
        Returns:
            An initialized MemoryProvider instance of the specified type.
        
        Raises:
            ProviderNotFoundError: If the provider_type is not registered.
        
        Example:
            >>> provider = ProviderFactory.create("in-house", {"vector_db_backend": "chroma"})
            >>> provider = ProviderFactory.create("mem0", {"user_id": "user123"})
        """
        from . import ProviderNotFoundError
        
        if provider_type not in cls.PROVIDERS:
            raise ProviderNotFoundError(
                provider_type=provider_type,
                available=list(cls.PROVIDERS.keys())
            )
        
        provider_class = cls.PROVIDERS[provider_type]
        provider = provider_class()
        provider.initialize(config)
        return provider
    
    @classmethod
    def register(cls, name: str, provider_class: Type[MemoryProvider]) -> None:
        """Register a new provider type.
        
        Allows runtime registration of custom provider implementations,
        enabling extensibility without modifying the factory code.
        
        Args:
            name: The name to register the provider under. This name will
                 be used when calling create() to instantiate the provider.
            provider_class: The provider class to register. Must be a subclass
                           of MemoryProvider.
        
        Example:
            >>> class CustomProvider(MemoryProvider):
            ...     # implementation
            >>> ProviderFactory.register("custom", CustomProvider)
            >>> provider = ProviderFactory.create("custom", config)
        """
        cls.PROVIDERS[name] = provider_class
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get a list of all registered provider type names.
        
        Returns:
            List of registered provider type names.
        
        Example:
            >>> ProviderFactory.get_available_providers()
            ['in-house', 'mem0', 'zep']
        """
        return list(cls.PROVIDERS.keys())
