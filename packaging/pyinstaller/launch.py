"""PyInstaller entry point: the desktop app, or the CLI when called as `gamecheck`."""

import os
import sys

if __name__ == "__main__":
    name = os.path.basename(os.environ.get("ARGV0") or sys.argv[0])
    if name == "gamecheck" or (len(sys.argv) > 1 and sys.argv[1] == "cli"):
        from void_gamecheck.cli import main

        argv = sys.argv[2:] if len(sys.argv) > 1 and sys.argv[1] == "cli" else sys.argv[1:]
        sys.exit(main(argv))
    from void_gamecheck.app import main

    sys.exit(main())
