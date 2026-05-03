"""DuckDuckGo search via the ddgr CLI subprocess."""

import json
import logging
import subprocess
from pathlib import Path
from shutil import which
from typing import Optional

from ddgr_skill.exceptions import DdgrNotFoundError, DdgrSearchError

logger = logging.getLogger(__name__)

_DDGR_FLAGS = {"d", "w", "m", "y"}
_DDGR_TIMEOUT = 30


def find_ddgr_binary() -> Path:
    """Locate the ddgr binary in PATH.

    Raises:
        DdgrNotFoundError: If ddgr is not installed or not in PATH.
    """
    ddgr_path = which("ddgr")
    if ddgr_path is None:
        raise DdgrNotFoundError(
            "ddgr not found in PATH. Install via: brew install ddgr"
        )
    return Path(ddgr_path)


def _build_ddgr_command(
    ddgr_path: Path,
    query: str,
    num_results: int,
    time_span: Optional[str] = None,
    site: Optional[str] = None,
    region: Optional[str] = None,
    expand_urls: bool = False,
) -> list[str]:
    """Build the ddgr command argument list."""
    cmd = [
        str(ddgr_path),
        "--json",
        "--np",
        "--num",
        str(num_results),
    ]

    if time_span:
        cmd.extend(["-t", time_span])
    if site:
        cmd.extend(["-w", site])
    if region:
        cmd.extend(["-r", region])
    if expand_urls:
        cmd.append("-x")

    cmd.append(query)
    return cmd


def search(
    query: str,
    num_results: int = 10,
    time_span: Optional[str] = None,
    site: Optional[str] = None,
    region: Optional[str] = None,
    expand_urls: bool = False,
    ddgr_path: Optional[Path] = None,
) -> list[dict[str, str]]:
    """Search DuckDuckGo via the ddgr CLI and return results.

    Each result dict has keys: title, url, abstract.

    Args:
        query: Search query string.
        num_results: Number of results (1-25, default 10).
        time_span: Time filter: "d", "w", "m", or "y".
        site: Restrict search to a specific site.
        region: Region code (e.g., "wt-wt" for worldwide).
        expand_urls: If True, expand abbreviated URLs.
        ddgr_path: Optional path to ddgr binary (for testing).

    Returns:
        List of dicts with "title", "url", "abstract" keys.

    Raises:
        DdgrNotFoundError: If ddgr binary not found.
        DdgrSearchError: If subprocess fails or returns invalid JSON.
        ValueError: If time_span is not a valid value.
    """
    if time_span and time_span not in _DDGR_FLAGS:
        raise ValueError(
            f"Invalid time_span: {time_span!r}. Must be one of {_DDGR_FLAGS}"
        )

    num_results = min(max(num_results, 1), 25)

    if ddgr_path is None:
        ddgr_path = find_ddgr_binary()

    cmd = _build_ddgr_command(
        ddgr_path,
        query,
        num_results,
        time_span,
        site,
        region,
        expand_urls,
    )

    logger.debug(f"Executing ddgr command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=_DDGR_TIMEOUT,
    )

    if result.returncode != 0:
        raise DdgrSearchError(
            f"ddgr failed with exit code {result.returncode}: {result.stderr.strip()}"
        )

    try:
        parsed = json.loads(result.stdout)
        logger.info(f"Successfully retrieved {len(parsed)} results from ddgr")
    except json.JSONDecodeError as exc:
        raise DdgrSearchError(
            f"ddgr returned invalid JSON: {exc}"
        ) from exc

    return parsed
