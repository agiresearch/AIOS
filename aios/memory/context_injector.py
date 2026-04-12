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
    ) -> LLMQuery:
        """Retrieve relevant memories and prepend as a system
        message.

        Returns the query unmodified when:
        - ``auto_inject`` is disabled
        - no user-role messages exist in the query
        - no memories survive filtering
        - any exception occurs during retrieval or formatting
        """
        if not self.enabled:
            return query

        try:
            user_text = self._extract_latest_user_message(
                query.messages
            )
            if user_text is None:
                return query

            # Retrieve memories scoped to this agent
            mem_query = MemoryQuery(
                operation_type="retrieve_memory",
                params={
                    "content": user_text,
                    "k": self.max_memories,
                    "user_id": agent_name,
                },
            )
            response = (
                self.memory_manager.provider.retrieve_memory(
                    mem_query
                )
            )

            if (
                not response.success
                or not response.search_results
            ):
                logger.info(
                    "No memories retrieved for user_id=%s",
                    agent_name,
                )
                return query

            results = response.search_results
            logger.info(
                "Retrieved %d memories for user_id=%s",
                len(results),
                agent_name,
            )

            # Filter by relevance threshold
            filtered = []
            for mem in results:
                score = mem.get("score")
                if score is None:
                    # No score from provider — include by default
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

            if not filtered:
                logger.info(
                    "All memories excluded by relevance "
                    "threshold for user_id=%s",
                    agent_name,
                )
                return query

            # Sort by score descending (most relevant first)
            filtered.sort(
                key=lambda m: m.get("score", 0),
                reverse=True,
            )

            # Truncate by token budget, removing least
            # relevant first
            filtered = self._truncate_by_token_budget(
                filtered
            )

            if not filtered:
                return query

            # Build and prepend the system message
            block = self._format_memory_block(filtered)
            system_msg = {
                "role": "system",
                "content": block,
            }
            query.messages = [system_msg] + query.messages

            logger.info(
                "Injected %d memories for user_id=%s",
                len(filtered),
                agent_name,
            )
            return query

        except Exception:
            logger.warning(
                "Context injection failed for "
                "user_id=%s",
                agent_name,
                exc_info=True,
            )
            return query

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
