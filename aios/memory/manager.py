"""
Memory Manager for the AIOS system.

This module provides the MemoryManager class that serves as the high-level
interface to the memory management system. It uses pluggable memory providers
to enable different storage backends (in-house, Mem0, Zep).
"""
import logging
import time
from collections import OrderedDict
from typing import Optional, Dict, Any, Set

from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.config.config_manager import config as global_config
from .access import AccessManager
from .providers import ProviderFactory, MemoryProvider
from .providers.in_house import InHouseProvider
from .providers.zep import ZepProvider
from .write_barrier import MemoryWriteBarrier

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory manager using pluggable providers.
    
    This class serves as a high-level interface to the memory management system,
    delegating operations to a configured memory provider. It supports multiple
    backend providers (in-house, Mem0, Zep) through the provider abstraction layer.
    
    The manager maintains backward compatibility with existing code by defaulting
    to the "in-house" provider when no provider is specified.
    
    Attributes:
        provider (MemoryProvider): The configured memory provider instance
        known_user_ids (Set[str]): User IDs observed in memory metadata
            during add_memory operations.  The ContextInjector reads
            this set to discover which real user_ids have memories in
            the store, enabling cross-agent shared retrieval without
            requiring the requesting agent to already have its own
            memories.
        barrier (MemoryWriteBarrier): Per-user_id write barrier that
            tracks accepted-but-uncommitted ``create_memory``
            operations and lets retrievals scoped to the same
            ``user_id`` wait until those writes drain. Read by
            ``SyscallExecutor`` (acceptance-time stamping) and
            ``ContextInjector`` (inline waits). Configured via
            ``memory.write_barrier.*``.
        access_manager (AccessManager): Privilege groups that decide
            whether an agent may read or modify another agent's
            memories. Read by ``ContextInjector`` as well. Configured
            via ``memory.access_control.privilege_groups``.
    """
    
    def __init__(
        self,
        log_mode: str = "console",
        provider: Optional[str] = None,
    ):
        """
        Initialize the MemoryManager.
        
        Args:
            log_mode: Logging mode for memory operations. Defaults to "console".
            provider: Optional provider type to use. If not specified, uses the
                     provider from configuration or defaults to "in-house".
                     Valid values: "in-house", "mem0", "zep"
        """
        self.log_mode = log_mode
        
        # Registry of user_ids seen in memory metadata.
        # Populated by add_memory; read by ContextInjector.
        # Keys: user_id strings. Values: monotonic timestamp of
        # last write. OrderedDict preserves insertion order; we
        # move-to-end on each write for recency tracking.
        self._known_user_ids: OrderedDict[str, float] = OrderedDict()
        
        # Get configuration
        memory_config = global_config.get_memory_config() or {}
        storage_config = global_config.get_storage_config() or {}
        
        # Determine provider type: explicit parameter > config > default
        provider_type = provider or memory_config.get("provider", "in-house")
        
        # Get provider-specific configuration
        provider_config = self._get_provider_config(
            provider_type, memory_config, storage_config
        )
        
        # Create the provider using the factory
        self.provider = ProviderFactory.create(provider_type, provider_config)

        # Per-user_id write barrier. Owns the pending-write registry
        # consulted by SyscallExecutor (acceptance-time stamping) and
        # ContextInjector (inline waits). Reads memory.write_barrier.*
        # once at construction; defaults are coded in the barrier so
        # omitting the section is safe.
        barrier_config = memory_config.get("write_barrier", {}) or {}
        self.barrier = MemoryWriteBarrier(config=barrier_config)

        access_config = memory_config.get("access_control", {}) or {}
        self.access_manager = AccessManager(
            access_config.get("privilege_groups")
        )

    @property
    def known_user_ids(self) -> Set[str]:
        """Backward-compatible set view for existing code."""
        return set(self._known_user_ids.keys())

    @property
    def latest_user_id(self) -> Optional[str]:
        """Return the most recently written user_id, or None."""
        if not self._known_user_ids:
            return None
        # Last key in OrderedDict = most recently moved-to-end
        return next(reversed(self._known_user_ids))

    def _register_user_id(self, user_id: str) -> None:
        """Register a user_id with current timestamp, moving to
        end of the ordered registry."""
        self._known_user_ids[user_id] = time.monotonic()
        self._known_user_ids.move_to_end(user_id)
    
    def _get_provider_config(
        self,
        provider_type: str,
        memory_config: Dict[str, Any],
        storage_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get provider-specific configuration.
        
        Extracts the appropriate configuration section based on the provider type.
        
        Args:
            provider_type: The type of provider ("in-house", "mem0", "zep")
            memory_config: The memory configuration section from config
            storage_config: The storage configuration section from config
        
        Returns:
            Dictionary containing provider-specific configuration
        """
        if provider_type == "in-house":
            return storage_config
        elif provider_type == "mem0":
            return memory_config.get("mem0", {})
        elif provider_type == "zep":
            return memory_config.get("zep", {})
        return {}

    def _provider_supports_barrier(self) -> bool:
        """Return True for providers that participate in the
        per-user write barrier.

        The barrier is meaningful only for providers whose writes
        commit asynchronously (Mem0Provider and Mem0-shaped test
        doubles). InHouseProvider and ZepProvider commit
        synchronously inside their own ``add_memory`` calls, so
        the barrier wait would only add latency without changing
        ordering -- Clause 3.5 of the design requires those paths
        stay byte-for-byte identical to the pre-fix behaviour.

        We use an *exclusion* check (``not isinstance(...,
        (InHouseProvider, ZepProvider))``) rather than a positive
        ``isinstance(self.provider, Mem0Provider)`` so Mem0-shaped
        test doubles -- which subclass ``MemoryProvider`` directly
        -- still take the barrier path. This is also a
        defense-in-depth backstop on top of the barrier's own
        ``_enabled`` check.
        """
        return not isinstance(
            self.provider, (InHouseProvider, ZepProvider)
        )

    def _get_accessible(
        self, agent_name: str, memory_id: str
    ) -> MemoryResponse:
        """Fetch *memory_id* for *agent_name*: the provider's
        response when the agent may access the memory, an error
        response otherwise."""
        existing = self.provider.get_memory(memory_id)
        if not existing.success:
            return existing
        if self.access_manager.can_access(agent_name, existing.metadata):
            return existing
        logger.warning(
            "Denied agent=%s access to memory_id=%s owned by %s",
            agent_name,
            memory_id,
            (existing.metadata or {}).get("owner_agent"),
        )
        return MemoryResponse(
            success=False,
            error=f"Access denied to memory {memory_id}",
        )

    def _accessible(
        self, agent_name: str, items: list, get_metadata
    ) -> list:
        """Keep only the retrieved items *agent_name* may access."""
        return [
            item for item in items
            if self.access_manager.can_access(agent_name, get_metadata(item))
        ]
    
    def _analyze_query_to_memory(self, query: MemoryQuery) -> 'MemoryNote':
        """
        Convert a MemoryQuery to a MemoryNote object.
        
        This method extracts parameters from a MemoryQuery and creates a
        MemoryNote object suitable for provider operations.
        
        Args:
            query: Memory query containing parameters
        
        Returns:
            MemoryNote created from query parameters
        """
        from .note import MemoryNote
        
        params = query.params
        valid_keys = [
            "content", "id", "keywords", "links", "retrieval_count",
            "timestamp", "last_accessed", "context", "evolution_history",
            "category", "tags"
        ]
        
        # Extract metadata if present
        metadata = params.get("metadata", {})
        
        # Create filtered data dictionary
        filtered_data = {}
        
        # Add direct parameters
        for k in params:
            if k in valid_keys:
                filtered_data[k] = params[k]
        
        # Handle memory_id specifically
        if "memory_id" in params and "id" not in filtered_data:
            filtered_data["id"] = params["memory_id"]
        
        # Add metadata fields if they exist
        if "tags" in metadata and "tags" not in filtered_data:
            filtered_data["tags"] = metadata.get("tags", [])
        if "keywords" in metadata and "keywords" not in filtered_data:
            filtered_data["keywords"] = metadata.get("keywords", [])
        if "category" in metadata and "category" not in filtered_data:
            filtered_data["category"] = metadata.get("category", "Uncategorized")
        
        memory_note = MemoryNote(**filtered_data)
        
        # Preserve the full metadata dict on the note so
        # that providers can read cross-agent fields
        # (user_id, owner_agent, sharing_policy, memory_type).
        if metadata:
            memory_note.metadata = metadata
        
        return memory_note
    
    def address_request(self, memory_syscall) -> MemoryResponse:
        """
        Process an agent's memory request.
        
        Routes the memory syscall to the appropriate provider method based
        on the operation type specified in the syscall's query.
        
        Args:
            memory_syscall: Memory syscall object containing the operation
                           and parameters
        
        Returns:
            MemoryResponse containing the result of the operation
        
        Raises:
            TypeError: If memory_syscall is not a MemorySyscall
            ValueError: If the operation type is invalid
        """
        # Import here to avoid circular dependency
        from aios.syscall.memory import MemorySyscall
        
        if not isinstance(memory_syscall, MemorySyscall):
            raise TypeError(f"Expected MemorySyscall, got {type(memory_syscall)}")
        
        query = memory_syscall.query
        operation_type = query.operation_type
        
        if operation_type == "add_memory":
            memory_note = self._analyze_query_to_memory(query)
            # Ensure metadata has a user_id so the memory is
            # scoped properly in Mem0's ChromaDB.  When the SDK
            # caller didn't provide an explicit user_id, fall
            # back to the requesting agent's name — this keeps
            # add and retrieve consistent (both scope to
            # agent_name by default).
            if memory_note.metadata is None:
                memory_note.metadata = {}
            if not memory_note.metadata.get("user_id"):
                memory_note.metadata["user_id"] = (
                    memory_syscall.agent_name
                )
            # The kernel, not the caller, records who owns a
            # memory: an agent cannot plant memories under another
            # agent's name.
            claimed_owner = memory_note.metadata.get("owner_agent")
            if claimed_owner and claimed_owner != memory_syscall.agent_name:
                logger.warning(
                    "add_memory: agent=%s claimed owner_agent=%s; "
                    "recording the calling agent as owner",
                    memory_syscall.agent_name,
                    claimed_owner,
                )
            memory_note.metadata["owner_agent"] = memory_syscall.agent_name
            # Track user_id for cross-agent discovery.
            uid = (memory_note.metadata or {}).get("user_id")
            logger.info(
                "add_memory: agent=%s, uid_from_metadata=%s, "
                "latest_user_id=%s, known=%s",
                memory_syscall.agent_name,
                uid,
                self.latest_user_id,
                self.known_user_ids,
            )
            if uid and uid != memory_syscall.agent_name:
                self._register_user_id(uid)
                logger.info(
                    "Registered user_id=%s (latest=%s, "
                    "known=%s)",
                    uid,
                    self.latest_user_id,
                    self.known_user_ids,
                )
            # Drain the per-user write barrier on commit (or
            # failure / exception) so any retrieval scoped to the
            # same ``user_id`` waiting on this write's ``seq_no``
            # is released. ``barrier_seq`` is stamped on the
            # syscall by ``SyscallExecutor`` (task 6); when absent
            # (e.g., a direct call from a test that bypasses the
            # executor), the sentinel ``0`` makes ``release`` a
            # no-op so the fast path stays free.
            barrier_seq = getattr(memory_syscall, "barrier_seq", 0)
            barrier_user_id = memory_note.metadata.get("user_id")
            resp = None
            try:
                with open("/tmp/per_user_proof.txt", "a") as _f:
                    _f.write(
                        f"provider type={type(self.provider).__name__} "
                        f"module={type(self.provider).__module__}\n"
                    )
                resp = self.provider.add_memory(memory_note)
                logger.info(
                    "[MEM0_DEBUG] add_memory result: "
                    "user_id=%s, success=%s, memory_id=%s, "
                    "error=%s",
                    barrier_user_id,
                    getattr(resp, "success", "?"),
                    getattr(resp, "memory_id", "?"),
                    getattr(resp, "error", None),
                )
                return resp
            finally:
                # ``finally`` guarantees waiters are notified even
                # if the provider raised; failed writes still
                # release waiters so a provider error does not
                # strand retrievals.
                success = bool(
                    resp and getattr(resp, "success", False)
                )
                self.barrier.release(
                    barrier_user_id, barrier_seq, success=success
                )
        
        elif operation_type == "remove_memory":
            memory_id = query.params["memory_id"]
            found = self._get_accessible(
                memory_syscall.agent_name, memory_id
            )
            if not found.success:
                return found
            return self.provider.remove_memory(memory_id)
        
        elif operation_type == "update_memory":
            memory_note = self._analyze_query_to_memory(query)
            found = self._get_accessible(
                memory_syscall.agent_name, memory_note.id
            )
            if not found.success:
                return found
            return self.provider.update_memory(memory_note)
        
        elif operation_type == "get_memory":
            return self._get_accessible(
                memory_syscall.agent_name, query.params["memory_id"]
            )
        
        elif operation_type == "retrieve_memory":
            query.params["agent_name"] = memory_syscall.agent_name
            if not query.params.get("user_id"):
                logger.warning(
                    "retrieve_memory called without request-scoped "
                    "user_id; skipping latest_user_id fallback to "
                    "avoid cross-user contamination (agent=%s)",
                    memory_syscall.agent_name,
                )
            # Wait for any accepted-but-uncommitted ``create_memory``
            # writes scoped to the same ``user_id`` and stamped at or
            # below ``barrier_snapshot`` to drain before serving this
            # retrieval. ``barrier_snapshot`` is stamped on the syscall
            # by ``SyscallExecutor`` (task 6); when absent (sentinel
            # ``0``) or when no ``user_id`` was supplied, skip the
            # wait entirely so the fast path stays free.
            # Provider-type guard (task 5.5): InHouseProvider and
            # ZepProvider commit synchronously and MUST NOT consult
            # the barrier (Clause 3.5).
            barrier_snapshot = getattr(
                memory_syscall, "barrier_snapshot", 0
            )
            barrier_user_id = query.params.get("user_id")
            if (
                barrier_snapshot
                and barrier_user_id
                and self._provider_supports_barrier()
            ):
                self.barrier.wait_until_drained(
                    barrier_user_id, barrier_snapshot
                )
            resp = self.provider.retrieve_memory(query)
            if resp.success and resp.search_results:
                resp.search_results = self._accessible(
                    memory_syscall.agent_name,
                    resp.search_results,
                    lambda item: item.get("metadata"),
                )
            logger.info(
                "[MEM0_DEBUG] retrieve_memory result: "
                "user_id=%s, success=%s, result_count=%d",
                query.params.get("user_id"),
                getattr(resp, "success", "?"),
                len(getattr(resp, "search_results", None) or []),
            )
            return resp
        
        elif operation_type == "retrieve_memory_raw":
            query.params["agent_name"] = memory_syscall.agent_name
            if not query.params.get("user_id"):
                logger.warning(
                    "retrieve_memory_raw called without request-scoped "
                    "user_id; skipping latest_user_id fallback to "
                    "avoid cross-user contamination (agent=%s)",
                    memory_syscall.agent_name,
                )
            # See ``retrieve_memory`` above -- same barrier wait
            # contract for the raw-retrieval path, including the
            # provider-type guard from task 5.5.
            barrier_snapshot = getattr(
                memory_syscall, "barrier_snapshot", 0
            )
            barrier_user_id = query.params.get("user_id")
            if (
                barrier_snapshot
                and barrier_user_id
                and self._provider_supports_barrier()
            ):
                self.barrier.wait_until_drained(
                    barrier_user_id, barrier_snapshot
                )
            return self._accessible(
                memory_syscall.agent_name,
                self.provider.retrieve_memory_raw(query),
                lambda note: note.metadata,
            )
        
        else:
            raise ValueError(f"Invalid operation: {operation_type}")
    
    def close(self) -> None:
        """
        Clean up resources.
        
        Delegates to the provider's close method to release any held resources.
        """
        if self.provider:
            self.provider.close()

    def sync_llm_from_query(
        self,
        llms: "list[dict] | None",
    ) -> None:
        """Propagate the agent's runtime LLM selection to the
        memory provider.

        Delegates to the provider's ``sync_llm_from_query`` method
        so that providers with an internal LLM (e.g., Mem0) can use
        the same model as the assistant agent.

        Args:
            llms: The ``LLMQuery.llms`` field.
        """
        if self.provider:
            self.provider.sync_llm_from_query(llms)
