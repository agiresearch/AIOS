"""
OpenAccessManager - an AccessManager that admits every agent into
every privilege group.

For tests whose subject is not access control (for example the
write-barrier suites, which use generated writer and reader agent
names). Memories still need an ``owner_agent``, and another agent's
memory still needs ``sharing_policy="shared"``.
"""
from aios.memory.access import AccessManager


class OpenAccessManager(AccessManager):
    def check_access(self, sid: str, tid: str) -> bool:
        return True
