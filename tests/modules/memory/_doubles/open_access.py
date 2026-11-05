"""
Access managers for memory tests.

OpenAccessManager admits every agent into every privilege group. It
is for tests whose subject is not access control (for example the
write-barrier suites, which use generated writer and reader agent
names). Memories still need an ``owner_agent``, and another agent's
memory still needs ``sharing_policy="shared"``.

personalization_access_manager() returns the privilege groups of
memory.access_control in config.yaml.example, for tests where
assistant_agent reads what profile_agent and task_agent wrote.
"""
from aios.memory.access import AccessManager


class OpenAccessManager(AccessManager):
    def check_access(self, sid: str, tid: str) -> bool:
        return True


def personalization_access_manager() -> AccessManager:
    """Profile and task agents admit the assistant agent to their
    privilege groups."""
    return AccessManager({
        "profile_agent": ["assistant_agent"],
        "task_agent": ["assistant_agent"],
    })
