"""Entry point: start an AIOS terminal tab.

Kept as a thin wrapper so ``python runtime/run_terminal.py`` keeps working. The
implementation lives in ``aios/terminal/terminal.py``, which this file and
``scripts/run_terminal.py`` both import -- the two entry points used to be
near-identical copies, so every scheduling feature had to be added twice.

Each tab can carry a scheduling priority and submit to its own model::

    python runtime/run_terminal.py --name ollama_tab --model ollama --mode chat

Run with ``--help`` for the priority and model options.
"""

from __future__ import annotations

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aios.terminal.terminal import AIOSTerminal, main  # noqa: E402,F401

if __name__ == "__main__":
    sys.exit(main())
