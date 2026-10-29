"""
Access manager for cross-agent memory operations.

Implements the access control part of the AIOS access manager
(AIOS paper, Section 3.8 and Appendix A.8): every agent owns a
privilege group, kept in a hashmap from the owner agent to the
agents admitted to it.

- ``add_privilege(sid, tid)`` assigns source agent ``sid`` into the
  privilege group of target agent ``tid``.
- ``check_access(sid, tid)`` checks whether ``sid`` is in ``tid``'s
  privilege group.

The MemoryManager and the ContextInjector ask ``can_access`` before
an agent reads or modifies a memory.
"""
import threading
from typing import Dict, Iterable, Mapping, Optional, Set


class AccessManager:
    """Privilege groups that gate cross-agent memory access.

    An agent may access a memory when it owns the memory, or when
    the memory's ``sharing_policy`` is ``"shared"`` and the agent is
    in the owner's privilege group. A memory without ``owner_agent``
    is accessible to no agent.

    Args:
        privilege_groups: Optional mapping from an owner agent to the
            agents admitted to its privilege group, as read from
            ``memory.access_control.privilege_groups``.
    """

    def __init__(
        self,
        privilege_groups: Optional[Mapping[str, Iterable[str]]] = None,
    ) -> None:
        self._groups: Dict[str, Set[str]] = {}
        self._lock = threading.Lock()
        for owner, members in (privilege_groups or {}).items():
            for member in members or ():
                self.add_privilege(member, owner)

    def add_privilege(self, sid: str, tid: str) -> None:
        """Assign agent *sid* into agent *tid*'s privilege group."""
        with self._lock:
            self._groups.setdefault(tid, set()).add(sid)

    def check_access(self, sid: str, tid: str) -> bool:
        """Return True if agent *sid* is in agent *tid*'s privilege
        group. Every agent is in its own group."""
        if sid == tid:
            return True
        with self._lock:
            return sid in self._groups.get(tid, ())

    def can_access(
        self,
        agent_name: str,
        metadata: Optional[Mapping],
    ) -> bool:
        """Return True if *agent_name* may read or modify a memory
        with the given *metadata*."""
        meta = metadata or {}
        owner = meta.get("owner_agent") or ""
        if not owner or not agent_name:
            return False
        if owner == agent_name:
            return True
        if (meta.get("sharing_policy") or "private") != "shared":
            return False
        return self.check_access(agent_name, owner)
