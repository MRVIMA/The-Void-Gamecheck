#!/usr/bin/env bash
# Lint + tests. Every data source is mocked: the tests never contact the real sites.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
.venv/bin/ruff check void_gamecheck tests scripts
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest "$@"
