#!/usr/bin/env bash
#
# Start the AIOS kernel server for the live scheduling demo.
#
# Two environment variables are set that the kernel needs but that are easy to
# miss, especially on Windows:
#
#   PYTHONUTF8 / PYTHONIOENCODING
#       runtime/launch.py prints emoji in its start-up messages. On a console
#       whose encoding is cp1252 (the Windows default when output is
#       redirected) those prints raise UnicodeEncodeError, which propagates out
#       of initialize_components() and stops the kernel before it binds a port.
#       UTF-8 mode fixes it and is harmless everywhere else.
#
#   PYTHONPATH
#       `aios` is not an installed package, so the project root has to be
#       importable or `runtime/launch.py` fails with ModuleNotFoundError.
#
# Usage:
#   scripts/run_kernel.sh                            # DEBUG logging (as before)
#   AIOS_LOG_LEVEL=WARNING scripts/run_kernel.sh     # quiet: only scheduler output
#
# Leaving AIOS_LOG_LEVEL at DEBUG reproduces the historical output exactly.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Prefer the project virtualenv; fall back to whatever is on PATH.
if [ -x ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"   # Windows
elif [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"           # macOS / Linux
else
    PYTHON="$(command -v python3 || command -v python)"
fi

# Unbuffered output so the scheduler's lines appear as they happen when the
# log is piped or redirected, rather than in one block at exit.
export PYTHONUNBUFFERED=1
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"
export AIOS_LOG_LEVEL="${AIOS_LOG_LEVEL:-DEBUG}"

echo "AIOS kernel"
echo "  root      : $ROOT_DIR"
echo "  interpreter: $PYTHON"
echo "  log level : $AIOS_LOG_LEVEL"
echo "  policy    : from scheduler.policy in config.yaml (default: fifo)"
echo
echo "The first start takes one to two minutes while the kernel imports"
echo "its components. Press Ctrl-C to stop."
echo

exec "$PYTHON" runtime/launch.py
