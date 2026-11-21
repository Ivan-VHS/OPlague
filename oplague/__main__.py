"""Run OPlague's read-only impact-profile tools."""

from .impact import main

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clife":
        from .clife import main as clife_main
        raise SystemExit(clife_main(sys.argv[2:]))
    raise SystemExit(main())
