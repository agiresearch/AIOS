"""
Context Injector for the AIOS personalization pipeline.

Retrieves relevant memories from the configured memory provider and
prepends them as a system message to the LLM query's message list,
enabling personalized agent responses based on prior interactions.
"""
import logging
from typing import TYPE_CHECKING, Optional

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery

from aios.memory.access import AccessManager
from aios.memory.memory_formatter import format_memory
from aios.memory.write_barrier import WaitOutcome

if TYPE_CHECKING:
    from aios.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class ContextInjector:
    """Retrieves relevant memories and injects them into LLM
    query messages.

    Uses the memory provider's ``retrieve_memory`` operation to
    find memories scoped to the requesting agent, filters by
    relevance score, formats them into a delimited system message,
    and prepends it at index 0 of the query's message list.
    """

    def __init__(
        self,
        memory_manager: "MemoryManager",
        config: dict,
    ) -> None:
        """
        Args:
            memory_manager: Initialized MemoryManager instance.
            config: Memory config section from config.yaml.
        """
        self.memory_manager = memory_manager
        self.enabled = config.get("auto_inject", False)
        self.max_memories = config.get(
            "max_injected_memories", 5
        )
        self.relevance_threshold = config.get(
            "relevance_threshold", 0.5
        )
        self.max_tokens = config.get("max_memory_tokens", 1500)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def inject(
        self,
        agent_name: str,
        query: LLMQuery,
        user_id: Optional[str] = None,
    ) -> "tuple[LLMQuery, dict]":
        """Retrieve relevant memories and prepend as a system
        message, returning diagnostics alongside the query.

        Args:
            agent_name: The agent making the LLM request.
            query: The LLM query to inject memories into.
            user_id: Optional per-request end-user identity.
                When provided, memory retrieval is scoped to
                this user_id directly. Cross-agent shared memory
                retrieval is ONLY triggered when this parameter
                is a non-empty string different from agent_name.
                When absent or None, only the agent's own
                memories are retrieved (no shared injection).

        Retrieval behavior:

        - **Own memories**: Always retrieved, scoped by
          ``agent_name`` as owner_agent. Uses ``user_id`` as
          the query filter when available, falls back to
          ``agent_name`` for backward compatibility.
        - **Shared memories**: Only retrieved when an explicit
          ``user_id`` is provided. Uses ``user_id`` as the
          filter with ``sharing_policy="shared"``. The
          ``agent_name`` is NEVER used as a user_id for
          shared retrieval.

        Returns ``(query, diagnostics)`` in all code paths:

        - **disabled**: ``auto_inject_enabled=False``, counts
          at 0, empty lists, tokens unchanged.
        - **happy path**: fully populated diagnostics.
        - **exception**: ``injected_count`` forced to 0,
          partially-filled diagnostics.
        """
        if not self.enabled:
            tokens = self._estimate_tokens(
                self._serialize_messages(query.messages)
            )
            return (query, {
                "auto_inject_enabled": False,
                "candidate_count": 0,
                "injected_count": 0,
                "source_agents": [],
                "memory_types": [],
                "prompt_tokens_before": tokens,
                "prompt_tokens_after": tokens,
                "resolved_user_id": None,
                "barrier_waits": [],
            })

        diagnostics: dict = {
            "auto_inject_enabled": True,
            "candidate_count": 0,
            "injected_count": 0,
            "source_agents": [],
            "memory_types": [],
            "prompt_tokens_before": 0,
            "prompt_tokens_after": 0,
            "resolved_user_id": None,
            "barrier_waits": [],
        }

        try:
            diagnostics["prompt_tokens_before"] = (
                self._estimate_tokens(
                    self._serialize_messages(
                        query.messages
                    )
                )
            )

            user_text = self._extract_latest_user_message(
                query.messages
            )
            if user_text is None:
                diagnostics["prompt_tokens_after"] = (
                    diagnostics["prompt_tokens_before"]
                )
                return (query, diagnostics)

            # === Resolve user_id BEFORE own-memory query ===
            # Use the explicit per-request user_id when
            # available. This ensures memory retrieval is
            # scoped to the correct end-user. Without it,
            # only own-agent memories are retrieved (no
            # cross-agent shared retrieval).
            resolved_user_id = self._resolve_user_id(
                agent_name, request_user_id=user_id,
            )

            # Use resolved_user_id for own-memory query when
            # available; fall back to agent_name for backward
            # compatibility (single-user deployments with no
            # per-request identity). NOTE: agent_name is ONLY
            # used for the own-memory path (scoped by
            # owner_agent); it is NEVER used for cross-agent
            # shared-memory retrieval.
            own_query_user_id = (
                resolved_user_id or agent_name
            )

            # Retrieve memories scoped to the resolved
            # end-user (or agent_name as fallback).
            mem_query = MemoryQuery(
                operation_type="retrieve_memory",
                params={
                    "content": user_text,
                    "k": self.max_memories,
                    "agent_name": agent_name,
                    "user_id": own_query_user_id,
                },
            )
            # Wait for any pending writes scoped to
            # own_query_user_id to drain before retrieval.
            # Kernel-internal retrievals bypass the syscall
            # path, so the executor's acceptance-time
            # stamping never runs for them; this inline
            # wait restores write-before-read ordering.
            # The outcome is recorded in
            # ``diagnostics["barrier_waits"]`` when the
            # wait actually ran (i.e., not BYPASSED) so
            # callers can correlate retrieval latency with
            # barrier activity.
            own_wait_outcome = self._await_pending_writes(
                own_query_user_id
            )
            if own_wait_outcome is not WaitOutcome.BYPASSED:
                diagnostics["barrier_waits"].append({
                    "user_id": own_query_user_id,
                    "outcome": own_wait_outcome.name,
                })
            response = (
                self.memory_manager.provider.retrieve_memory(
                    mem_query
                )
            )

            own_results = []
            if response.success and response.search_results:
                own_results = response.search_results
                logger.info(
                    "Retrieved %d own memories for agent=%s"
                    " (user_id=%s)",
                    len(own_results),
                    agent_name,
                    own_query_user_id,
                )

            # --- Cross-agent shared memory retrieval ---
            # The pre-resolved user_id is authoritative for
            # the shared-memory path. Shared retrieval is
            # ONLY attempted when an explicit user_id was
            # provided in the request. When resolved_user_id
            # is None (no per-request identity), shared
            # retrieval is skipped entirely — agent_name is
            # NEVER substituted as a user_id here.
            derived_user_id = resolved_user_id

            # Record resolved_user_id in diagnostics when
            # it differs from agent_name.
            if resolved_user_id and resolved_user_id != agent_name:
                diagnostics["resolved_user_id"] = (
                    resolved_user_id
                )

            results = list(own_results)

            if (
                derived_user_id
                and derived_user_id != agent_name
            ):
                # Wait for any pending writes scoped to the
                # cross-agent ``user_id`` to drain before the
                # shared retrieval. Mirrors the agent-scoped
                # wait above (task 7.2) and closes the
                # auto-inject race documented in
                # test_write_barrier_exploration.py case 2:
                # without this wait, ``ProfileAgent`` /
                # ``TaskAgent`` shared writes parked at the
                # provider would be missed by the injector
                # because kernel-internal retrievals bypass
                # the syscall path's acceptance-time stamping.
                # Outcome is recorded in
                # ``diagnostics["barrier_waits"]`` when the wait
                # actually ran (i.e., not BYPASSED).
                shared_wait_outcome = (
                    self._await_pending_writes(
                        derived_user_id
                    )
                )
                if shared_wait_outcome is not WaitOutcome.BYPASSED:
                    diagnostics["barrier_waits"].append({
                        "user_id": derived_user_id,
                        "outcome": shared_wait_outcome.name,
                    })
                shared = self._retrieve_shared_memories(
                    user_text, derived_user_id, agent_name
                )
                if shared:
                    results = self._merge_and_deduplicate(
                        own_results, shared
                    )
                    shared_agents = list({
                        (m.get("metadata") or {}).get(
                            "owner_agent", ""
                        )
                        for m in shared
                        if (m.get("metadata") or {}).get(
                            "owner_agent", ""
                        )
                    })
                    logger.info(
                        "Retrieved %d shared memories for "
                        "user_id=%s from agents: %s",
                        len(shared),
                        derived_user_id,
                        shared_agents,
                    )

            if not results:
                logger.info(
                    "No memories retrieved for agent=%s "
                    "(resolved_user_id=%s)",
                    agent_name,
                    derived_user_id,
                )
                diagnostics["prompt_tokens_after"] = (
                    diagnostics["prompt_tokens_before"]
                )
                return (query, diagnostics)

            # candidate_count = merged set before filtering
            diagnostics["candidate_count"] = len(results)

            logger.info(
                "Injection pipeline for agent=%s: "
                "resolved_user_id=%s, own=%d, "
                "candidates=%d",
                agent_name,
                derived_user_id,
                len(own_results),
                len(results),
            )

            # Filter by relevance threshold
            filtered = []
            for mem in results:
                score = mem.get("score")
                if score is None:
                    filtered.append(mem)
                elif score >= self.relevance_threshold:
                    filtered.append(mem)
                else:
                    logger.debug(
                        "Excluded memory (score=%.3f < "
                        "threshold=%.3f): %s",
                        score,
                        self.relevance_threshold,
                        (mem.get("content", ""))[:60],
                    )

            logger.info(
                "Injection filtering for agent=%s: "
                "after_relevance=%d (threshold=%.2f), "
                "max_memories=%d",
                agent_name,
                len(filtered),
                self.relevance_threshold,
                self.max_memories,
            )

            if not filtered:
                logger.info(
                    "All memories excluded by relevance "
                    "threshold for agent=%s "
                    "(resolved_user_id=%s)",
                    agent_name,
                    derived_user_id,
                )
                diagnostics["prompt_tokens_after"] = (
                    diagnostics["prompt_tokens_before"]
                )
                return (query, diagnostics)

            # --- User-partition filter (defense in depth) ---
            # Exclude any memory whose metadata user_id does
            # not match the resolved request identity. This
            # prevents cross-user leakage even if the upstream
            # provider returns incorrectly scoped results
            # (e.g., misconfigured collection routing, weakened
            # Mem0 filter, or a future provider that combines
            # user collections).
            #
            # Fail-closed: memories with missing or empty
            # user_id are excluded when a resolved identity
            # exists. This avoids silently treating unscoped
            # memories as belonging to the current user.
            user_partition_id = own_query_user_id
            pre_user_filter_count = len(filtered)
            filtered = [
                mem for mem in filtered
                if (mem.get("metadata") or {}).get(
                    "user_id", ""
                ) == user_partition_id
            ]

            if len(filtered) < pre_user_filter_count:
                logger.info(
                    "User-partition filter for agent=%s: "
                    "retained %d/%d (partition_id=%s)",
                    agent_name,
                    len(filtered),
                    pre_user_filter_count,
                    user_partition_id,
                )

            if not filtered:
                logger.info(
                    "All memories excluded by user-partition "
                    "filter for agent=%s "
                    "(resolved_user_id=%s)",
                    agent_name,
                    derived_user_id,
                )
                diagnostics["prompt_tokens_after"] = (
                    diagnostics["prompt_tokens_before"]
                )
                return (query, diagnostics)

            # Enforce agent-level access: per-user collections
            # contain ALL memories for a user_id; this filter
            # keeps the agent's own memories and the shared
            # memories of owners whose privilege group admits
            # this agent. Without an access manager (test
            # doubles), only the agent's own memories pass.
            access_manager = getattr(
                self.memory_manager, "access_manager", None
            ) or AccessManager()
            filtered = [
                mem for mem in filtered
                if access_manager.can_access(
                    agent_name, mem.get("metadata")
                )
            ]

            if not filtered:
                logger.info(
                    "All memories excluded by access "
                    "control for agent=%s "
                    "(resolved_user_id=%s)",
                    agent_name,
                    derived_user_id,
                )
                diagnostics["prompt_tokens_after"] = (
                    diagnostics["prompt_tokens_before"]
                )
                return (query, diagnostics)

            # Sort by score descending (most relevant first)
            filtered.sort(
                key=lambda m: m.get("score") or 0,
                reverse=True,
            )

            # Format memory content to natural language
            formatted_memories = []
            for mem in filtered:
                formatted = dict(mem)  # shallow copy
                try:
                    formatted["content"] = format_memory(
                        mem.get("content", ""),
                        mem.get("metadata", {}),
                    )
                except Exception:
                    logger.warning(
                        "Memory formatting failed, "
                        "using raw content",
                        exc_info=True,
                    )
                formatted_memories.append(formatted)
            filtered = formatted_memories

            # Truncate by token budget
            filtered = self._truncate_by_token_budget(
                filtered
            )

            if not filtered:
                diagnostics["prompt_tokens_after"] = (
                    diagnostics["prompt_tokens_before"]
                )
                return (query, diagnostics)

            # Record injected_count after all filtering
            diagnostics["injected_count"] = len(filtered)

            # Extract unique source_agents and memory_types
            agents: set = set()
            types: set = set()
            for mem in filtered:
                meta = mem.get("metadata") or {}
                oa = meta.get("owner_agent", "")
                if oa:
                    agents.add(oa)
                mt = meta.get("memory_type", "")
                if mt:
                    types.add(mt)
            diagnostics["source_agents"] = list(agents)
            diagnostics["memory_types"] = list(types)

            # Build and prepend the system message
            block = self._format_memory_block(filtered)
            system_msg = {
                "role": "system",
                "content": block,
            }
            query.messages = [system_msg] + query.messages

            diagnostics["prompt_tokens_after"] = (
                self._estimate_tokens(
                    self._serialize_messages(
                        query.messages
                    )
                )
            )

            logger.info(
                "Injected %d memories (%d own + %d shared) "
                "for agent=%s, resolved_user_id=%s",
                len(filtered),
                sum(
                    1 for m in filtered
                    if (m.get("metadata") or {}).get(
                        "owner_agent", ""
                    ) == agent_name
                ),
                sum(
                    1 for m in filtered
                    if (m.get("metadata") or {}).get(
                        "owner_agent", ""
                    ) != agent_name
                ),
                agent_name,
                derived_user_id,
            )
            return (query, diagnostics)

        except Exception:
            logger.warning(
                "Context injection failed for agent=%s "
                "(resolved_user_id=%s)",
                agent_name,
                diagnostics.get("resolved_user_id"),
                exc_info=True,
            )
            diagnostics["injected_count"] = 0
            # If prompt_tokens_after was never set, match
            # prompt_tokens_before (query was not modified).
            if diagnostics["prompt_tokens_after"] == 0:
                diagnostics["prompt_tokens_after"] = (
                    diagnostics["prompt_tokens_before"]
                )
            return (query, diagnostics)

    # ------------------------------------------------------------------
    # Cross-agent helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_user_id_from_results(
        results: list,
    ) -> Optional[str]:
        """Return the first non-empty ``user_id`` found in the
        metadata of *results*, or ``None`` if none exists."""
        for mem in results:
            meta = mem.get("metadata") or {}
            uid = meta.get("user_id")
            if uid:
                return uid
        return None

    def _resolve_user_id(
        self,
        agent_name: str,
        request_user_id: Optional[str] = None,
    ) -> Optional[str]:
        """Resolve the active end-user's user_id for memory
        retrieval scoping.

        Resolution:
        1. Explicit ``request_user_id`` from the current request
           (per-request identity from ``QueryRequest.user_id``).
        2. ``None`` — signals the caller to skip shared-memory
           retrieval and use ``agent_name`` only for own-memory
           queries (safe: scoped by owner_agent).

        **Invariant**: This method NEVER returns ``agent_name``.
        The agent name is not a valid user_id for cross-agent
        shared-memory retrieval. Returning it would cause the
        shared-memory path to query for memories belonging to
        a non-existent end-user named "assistant_agent", which
        is semantically wrong and would never match real user
        memories.

        When no ``request_user_id`` is provided, this method
        returns ``None`` rather than guessing from global state.
        The caller (``inject()``) uses ``agent_name`` as the
        own-memory query scope, which is safe because it only
        returns that agent's own memories — no cross-user
        contamination is possible.

        .. note:: Previous versions fell back to
           ``MemoryManager.latest_user_id`` or iterated
           ``known_user_ids``. Those fallbacks caused cross-user
           memory contamination in multi-user scenarios and have
           been removed.
        """
        # 1. Prefer explicit per-request user_id.
        if request_user_id and request_user_id != agent_name:
            logger.info(
                "user_id resolved from REQUEST: %s "
                "(agent=%s)",
                request_user_id,
                agent_name,
            )
            return request_user_id

        # No request-scoped identity available. Return None so
        # the caller falls back to agent_name (safe default).
        if not request_user_id:
            logger.debug(
                "No request-scoped user_id for context "
                "injection; skipping user-scoped retrieval "
                "(agent=%s)",
                agent_name,
            )

        return None

    def _retrieve_shared_memories(
        self,
        user_text: str,
        user_id: str,
        agent_name: str | None = None,
    ) -> list:
        """Issue a second retrieval for shared memories from
        other agents that belong to *user_id*.

        Requests extra candidates from the provider because
        the native search ``top_k`` is applied *before* the
        ``_apply_sharing_filter`` post-filter.  Without the
        over-fetch, private conversation memories can fill
        the top-k slots and push shared profile/task memories
        out of the result set entirely.

        Returns an empty list on any failure so the caller can
        fall back to using only the agent's own memories.
        """
        # Over-fetch factor: request 4× the desired count so
        # that post-filtering by sharing_policy still yields
        # enough shared memories even when private conversation
        # memories dominate the relevance ranking.
        fetch_k = self.max_memories * 4
        try:
            params: dict = {
                "content": user_text,
                "k": fetch_k,
                "user_id": user_id,
                "sharing_policy": "shared",
            }
            if agent_name is not None:
                params["agent_name"] = agent_name
            shared_query = MemoryQuery(
                operation_type="retrieve_memory",
                params=params,
            )
            resp = (
                self.memory_manager.provider
                .retrieve_memory(shared_query)
            )
            if resp.success and resp.search_results:
                return resp.search_results
        except Exception:
            logger.debug(
                "Shared memory retrieval failed for "
                "user_id=%s",
                user_id,
                exc_info=True,
            )
        return []

    @staticmethod
    def _merge_and_deduplicate(
        own: list,
        shared: list,
    ) -> list:
        """Merge *own* and *shared* result lists, removing
        duplicates by memory content.

        Own memories always come first so they are never
        dropped in favour of a shared duplicate.
        """
        seen_content: set = set()
        merged: list = []

        for mem in own:
            content = mem.get("content", "")
            seen_content.add(content)
            merged.append(mem)

        for mem in shared:
            content = mem.get("content", "")
            if content not in seen_content:
                seen_content.add(content)
                merged.append(mem)

        return merged

    # ------------------------------------------------------------------
    # Write-barrier helpers
    # ------------------------------------------------------------------

    def _await_pending_writes(self, user_id):
        """Snapshot + wait against the per-user write barrier.

        Kernel-internal retrievals issued by ``inject`` bypass the
        ``MemorySyscall`` path, so the executor's acceptance-time
        stamping never runs for them. This helper performs the
        equivalent ``snapshot`` / ``wait_until_drained`` pair inline,
        immediately before each ``provider.retrieve_memory`` call,
        so a retrieval scoped to ``user_id = U`` cannot be served
        while ``create_memory`` operations for the same ``user_id``
        accepted before it remain uncommitted.

        Short-circuits to ``WaitOutcome.BYPASSED`` (without
        acquiring any lock) when:

        - ``user_id`` is empty/``None`` -- legacy agent-scoped
          retrievals never wait (Clause 3.3).
        - ``self.memory_manager`` has no ``barrier`` attribute --
          defense-in-depth for test doubles or older managers.
        - The barrier is disabled via
          ``memory.write_barrier.enabled: false`` -- the kill-switch
          path takes the existing fast path byte-for-byte.

        The empty-user_id and missing-barrier short-circuits keep
        this helper cheap on the fast path so it can be called
        unconditionally before each retrieval.

        Returns the ``WaitOutcome`` so the caller can record
        non-BYPASSED waits in ``diagnostics["barrier_waits"]``.
        """
        if not user_id:
            return WaitOutcome.BYPASSED
        barrier = getattr(self.memory_manager, "barrier", None)
        if barrier is None:
            return WaitOutcome.BYPASSED
        seq = barrier.snapshot(user_id)
        return barrier.wait_until_drained(user_id, seq)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_latest_user_message(
        messages: list,
    ) -> Optional[str]:
        """Return the content of the last user-role message,
        or ``None`` if none exists."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content")
        return None

    @staticmethod
    def _format_memory_block(
        memories: list,
    ) -> str:
        """Format memories into a delimited system message
        string."""
        lines = [
            "===== MEMORY CONTEXT =====",
            "The following are relevant memories from prior "
            "interactions with this user. Use them to "
            "personalize your response:",
            "",
        ]
        for mem in memories:
            ts = mem.get("timestamp", "unknown")
            content = mem.get("content", "")
            lines.append(f"- [{ts}] {content}")

        lines.append("")
        lines.append("===== END MEMORY CONTEXT =====")
        return "\n".join(lines)

    @staticmethod
    def _serialize_messages(messages: list) -> str:
        """Join all message content strings for token
        estimation."""
        return " ".join(
            m.get("content", "") for m in messages
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimate: words * 1.3."""
        return int(len(text.split()) * 1.3)

    def _truncate_by_token_budget(
        self,
        memories: list,
    ) -> list:
        """Remove least-relevant memories until the formatted
        block fits within ``max_tokens``.

        Memories are assumed to be sorted by score descending.
        We remove from the tail (lowest score) first.
        """
        while memories:
            block = self._format_memory_block(memories)
            if self._estimate_tokens(block) <= self.max_tokens:
                return memories
            # Drop the least relevant (last item)
            memories = memories[:-1]
        return memories
