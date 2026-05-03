"""Entry point for python -m ddgr_skill."""

import sys
import time
import logging

from ddgr_skill.cli import main

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    start_time = time.perf_counter()
    # Log to stderr. Note: logging.basicConfig is called in cli.main(),
    # so this will use default settings until main() is called.
    logger.info(f"Process started at {start_time}")
    sys.exit(main())
