"""
Abstract base class for memory providers.

This module defines the MemoryProvider interface that all memory provider
implementations must follow. The interface enables pluggable memory backends
while maintaining a consistent API across different storage solutions.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, TYPE_CHECKING

from cerebrum.memory.apis import MemoryQuery, MemoryResponse

if TYPE_CHECKING:
    from aios.memory.note import MemoryNote


def _apply_sharing_filter(
    candidates: list,
    agent_name: str,
    user_id: str | None,
    sharing_policy: str | None,
    get_metadata: callable,
) -> list:
    """Filter candidate memories by ownership and sharing rules.

    Implements the decision matrix for cross-agent memory retrieval.
    Each candidate is kept or dropped based on the combination of
    ``user_id`` and ``sharing_policy`` supplied by the caller, plus
    the metadata stored on the memory itself.

    Safe defaults:
    - Missing ``sharing_policy`` in metadata → treated as ``"private"``
    - Missing ``owner_agent`` in metadata → never matches any agent

    Privacy invariant: a memory whose ``owner_agent`` differs from
    *agent_name* is **never** returned unless its metadata
    ``sharing_policy`` is exactly ``"shared"``. Being shared is not
    enough: MemoryManager and ContextInjector then keep another
    agent's memory only when the owner's privilege group admits
    *agent_name* (see ``aios/memory/access.py``).

    Args:
        candidates: Raw results from the provider's search.
        agent_name: The requesting agent's name.
        user_id: Optional user_id filter from query.params.
        sharing_policy: Optional sharing_policy filter from
            query.params.
        get_metadata: Callable that extracts a metadata dict from
            a single candidate item.  Must return a dict with keys:
            ``owner_agent``, ``user_id``, ``sharing_policy``.

    Returns:
        Filtered list of candidates that pass the sharing rules.
    """
    result = []
    for candidate in candidates:
        meta = get_metadata(candidate)
        mem_owner = meta.get("owner_agent", "")
        mem_user = meta.get("user_id", "")
        mem_policy = meta.get("sharing_policy", "") or "private"

        is_own = mem_owner == agent_name

        # --- privacy invariant ---
        if not is_own and mem_policy != "shared":
            continue

        if user_id is None and sharing_policy is None:
            # Default: agent-scoped only
            if is_own:
                result.append(candidate)

        elif user_id is None and sharing_policy is not None:
            # Policy filter within agent scope
            if is_own and mem_policy == sharing_policy:
                result.append(candidate)

        elif user_id is not None and sharing_policy is None:
            # User-scoped with implicit privacy
            if mem_user == user_id and (
                is_own or mem_policy == "shared"
            ):
                result.append(candidate)

        elif (
            user_id is not None
            and sharing_policy == "shared"
        ):
            # Cross-agent shared
            if (
                mem_user == user_id
                and mem_policy == "shared"
            ):
                result.append(candidate)

        elif (
            user_id is not None
            and sharing_policy == "private"
        ):
            # Own private only
            if (
                is_own
                and mem_user == user_id
                and mem_policy == "private"
            ):
                result.append(candidate)

        else:
            # Any other sharing_policy value with user_id
            if (
                mem_user == user_id
                and mem_policy == sharing_policy
            ):
                if is_own or mem_policy == "shared":
                    result.append(candidate)

    return result


def _enrich_metadata(metadata: dict) -> dict:
    """Ensure owner_agent, user_id, sharing_policy, memory_type
    are present with empty-string defaults."""
    for key in (
        "owner_agent",
        "user_id",
        "sharing_policy",
        "memory_type",
    ):
        metadata.setdefault(key, "")
    return metadata


class MemoryProvider(ABC):
    """Abstract base class for memory providers.
    
    All memory provider implementations (InHouseProvider, Mem0Provider, 
    ZepProvider) must inherit from this class and implement all abstract methods.
    
    The provider abstraction enables:
    - Pluggable memory backends without changing application code
    - Consistent API across different storage solutions
    - Easy addition of new memory providers
    """
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with configuration.
        
        This method is called after provider instantiation to configure
        the provider with backend-specific settings.
        
        Args:
            config: Provider-specific configuration dictionary.
                   For InHouseProvider: vector_db_backend, etc.
                   For Mem0Provider: api_key, user_id, llm, embedder, etc.
                   For ZepProvider: api_key, base_url, session_id, etc.
        
        Raises:
            ProviderInitializationError: If initialization fails due to
                invalid configuration or connection issues.
        """
        pass
    
    @abstractmethod
    def add_memory(self, memory_note: 'MemoryNote') -> MemoryResponse:
        """Add a memory note to storage.
        
        Args:
            memory_note: The memory note to store, containing content
                        and associated metadata (keywords, tags, category, etc.)
        
        Returns:
            MemoryResponse with success=True and memory_id on success,
            or success=False with error message on failure.
        """
        pass
    
    @abstractmethod
    def remove_memory(self, memory_id: str) -> MemoryResponse:
        """Remove a memory by ID.
        
        Args:
            memory_id: Unique identifier of the memory to remove.
        
        Returns:
            MemoryResponse with success=True on successful removal,
            or success=False with error message if memory not found.
        """
        pass
    
    @abstractmethod
    def update_memory(self, memory_note: 'MemoryNote') -> MemoryResponse:
        """Update an existing memory.
        
        Args:
            memory_note: The memory note with updated content/metadata.
                        The memory_note.id identifies which memory to update.
        
        Returns:
            MemoryResponse with success=True and memory_id on success,
            or success=False with error message if memory not found.
        """
        pass
    
    @abstractmethod
    def get_memory(self, memory_id: str) -> MemoryResponse:
        """Retrieve a memory by ID.
        
        Args:
            memory_id: Unique identifier of the memory to retrieve.
        
        Returns:
            MemoryResponse with success=True, content, and metadata on success,
            or success=False with error message if memory not found.
        """
        pass
    
    @abstractmethod
    def retrieve_memory(self, query: MemoryQuery) -> MemoryResponse:
        """Search for memories matching the query.
        
        Performs semantic search to find memories similar to the query content.
        
        Args:
            query: MemoryQuery containing search parameters:
                  - params["content"]: The search query text
                  - params["k"]: Maximum number of results to return
        
        Returns:
            MemoryResponse with success=True and search_results containing
            a list of matching memories with their content and metadata.
        """
        pass
    
    @abstractmethod
    def retrieve_memory_raw(self, query: MemoryQuery) -> List['MemoryNote']:
        """Retrieve raw memory objects for internal processing.
        
        Similar to retrieve_memory but returns raw MemoryNote objects
        instead of a formatted MemoryResponse. Used for internal operations
        that need direct access to memory objects.
        
        Args:
            query: MemoryQuery containing search parameters:
                  - params["content"]: The search query text
                  - params["k"]: Maximum number of results to return (default: 5)
        
        Returns:
            List of MemoryNote objects matching the query.
        """
        pass
    
    def close(self) -> None:
        """Clean up resources.
        
        Override this method if the provider needs to release resources,
        close connections, or perform cleanup operations when shutting down.
        
        For providers with external connections (Mem0, Zep), this should
        properly disconnect from external services.
        
        The default implementation is a no-op for backward compatibility.
        """
        pass

    def sync_llm_from_query(
        self,
        llms: "list[dict] | None",
    ) -> None:
        """Synchronize the provider's internal LLM with the agent's
        runtime model selection.

        Override in providers that use an LLM internally (e.g., Mem0
        uses an LLM for fact extraction). The default implementation
        is a no-op for providers that don't need LLM synchronization.

        Args:
            llms: The ``LLMQuery.llms`` field — a list of dicts
                each containing ``name`` and optionally ``backend``.
                ``None`` or empty list is a no-op.
        """
        pass
