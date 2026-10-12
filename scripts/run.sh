#!/usr/bin/env bash
# Start the desktop app from the source folder.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
exec .venv/bin/python -m void_gamecheck.app "$@"
