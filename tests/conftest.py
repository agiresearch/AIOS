"""
Root conftest for the AIOS test suite.

Responsibilities:
    1. Register the ``integration`` marker programmatically so that
       pytest never emits an "unknown marker" warning — even if
       pytest.ini is not picked up for any reason.
    2. Ensure the project root is importable (sys.path fix).
"""

import os
import sys

import pytest

# ── sys.path fix ──────────────────────────────────────────────────────
# Many existing test files already do their own
#     sys.path.insert(0, <project_root>)
# This ensures the project root is always available regardless of the
# working directory pytest is invoked from, without duplicating entries.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ── Marker registration ──────────────────────────────────────────────
def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers as a safety-net backup to pytest.ini."""
    config.addinivalue_line(
        "markers",
        "integration: requires external services (Ollama, ChromaDB, etc.)",
    )
