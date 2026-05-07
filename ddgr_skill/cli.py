"""Argument parsing and command dispatch for ddgr-skill."""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

from ddgr_skill.exceptions import DdgRSkillError
from ddgr_skill.search import search


_SKILL_INSTALL_TARGETS = [
    (Path.home() / ".claude/skills/ddgr-skill/SKILL.md", "claude_skill.md"),
    (Path.home() / ".hermes/skills/web/ddgr-skill/SKILL.md", "hermes_skill.md"),
]


def _ensure_skills_installed() -> None:
    """Auto-install SKILL.md to agent skill directories on first run."""
    package_dir = Path(__file__).parent
    for target_path, source_name in _SKILL_INSTALL_TARGETS:
        if target_path.exists():
            continue
        source = package_dir / source_name
        if not source.exists():
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_path)
        logger.info(f"Installed skill definition to {target_path}")

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="[ddgr-skill] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def _log(message: str) -> None:
    """Log progress message to stderr.
    Deprecated: Use logger.info() instead.
    """
    logger.info(message)


def _handle_search(args: argparse.Namespace) -> None:
    """Handle the 'search' subcommand."""
    from ddgr_skill.output import (
        format_lookup_results_json,
        format_lookup_results_markdown,
        format_search_results_json,
    )
    from ddgr_skill.fetcher import fetch_with_fallback
    import time

    logger.info(f"Searching for query: {args.query}")
    start = time.perf_counter()
    results = search(
        query=args.query,
        num_results=args.num,
        time_span=args.time_span,
        site=args.site,
        region=args.region,
        expand_urls=args.expand,
    )
    duration = time.perf_counter() - start
    logger.info(f"Search completed in {duration:.2f}s, found {len(results)} results")

    if args.fetch:
        if not results:
            logger.warning("No results found to fetch")
            print(json.dumps([], indent=2))
            return
        logger.info(f"Fetching up to {args.num} URLs from search results...")
        fetch_start = time.perf_counter()
        fetched, all_failed = fetch_with_fallback(
            results, num_target=args.num
        )
        fetch_duration = time.perf_counter() - fetch_start
        logger.info(f"Fetching completed in {fetch_duration:.2f}s")

        if all_failed:
            logger.error("All fetches failed — showing search results")
            print(format_search_results_json(results))
        elif args.format == "json":
            print(format_lookup_results_json(fetched))
        else:
            print(format_lookup_results_markdown(fetched))
        return

    print(format_search_results_json(results))


def _handle_fetch(args: argparse.Namespace) -> None:
    """Handle the 'fetch' subcommand."""
    from ddgr_skill.fetcher import fetch_as_markdown
    from ddgr_skill.output import (
        format_fetch_result_json,
        format_fetch_result_markdown,
        save_to_file,
    )
    import time

    logger.info(f"Fetching URL: {args.url}")
    start = time.perf_counter()
    result = fetch_as_markdown(args.url)
    duration = time.perf_counter() - start
    logger.info(f"Fetch completed in {duration:.2f}s")

    if args.output:
        if args.format == "json":
            content = format_fetch_result_json(result)
        else:
            content = format_fetch_result_markdown(result, include_title=args.title)
        save_to_file(content, Path(args.output))
        return

    if args.format == "json":
        print(format_fetch_result_json(result))
    else:
        print(format_fetch_result_markdown(result, include_title=args.title))


def _output_search_abstracts(search_results: list[dict]) -> None:
    """Output search abstracts as fallback when all fetches fail."""
    for r in search_results:
        print(r.get("title", ""))
        print(r.get("url", ""))
        abstract = r.get("abstract", "")
        if abstract:
            print(abstract)
        print()


def _handle_lookup(args: argparse.Namespace) -> None:
    """Handle the 'lookup' subcommand."""
    from ddgr_skill.fetcher import fetch_with_fallback
    from ddgr_skill.output import (
        format_lookup_results_json,
        format_lookup_results_markdown,
        format_search_results_json,
        write_lookup_results,
    )
    import time

    search_count = min(args.num * 3, 25)
    logger.info(f"Searching for query: {args.query} (requesting {search_count} results)")
    start = time.perf_counter()
    search_results = search(
        query=args.query,
        num_results=search_count,
        time_span=args.time_span,
        site=args.site,
    )
    duration = time.perf_counter() - start
    logger.info(f"Search completed in {duration:.2f}s, found {len(search_results)} results")

    if not search_results:
        logger.warning("No search results found")
        print(json.dumps([], indent=2))
        return

    logger.info(f"Fetching top {args.num} URLs...")
    fetch_start = time.perf_counter()
    fetched, all_failed = fetch_with_fallback(
        search_results, num_target=args.num
    )
    fetch_duration = time.perf_counter() - fetch_start
    logger.info(f"Fetching completed in {fetch_duration:.2f}s")

    if all_failed:
        logger.error("All fetches failed — showing search results")
        _output_search_abstracts(search_results)
    elif args.output:
        write_lookup_results(fetched, Path(args.output), format_=args.format)
    elif args.format == "json":
        print(format_lookup_results_json(fetched))
    else:
        print(format_lookup_results_markdown(fetched))


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="ddgr-skill",
        description="Search the web via DuckDuckGo and fetch page content.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    search_parser = subparsers.add_parser(
        "search", help="Search DuckDuckGo and return results as JSON"
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--num", type=int, default=10, help="Number of results (1-25, default 10)"
    )
    search_parser.add_argument(
        "--time",
        dest="time_span",
        choices=["d", "w", "m", "y"],
        help="Time filter: d (day), w (week), m (month), y (year)",
    )
    search_parser.add_argument(
        "--site", help="Restrict search to a specific site"
    )
    search_parser.add_argument(
        "--region", help="Region code (e.g., wt-wt for worldwide)"
    )
    search_parser.add_argument(
        "--expand",
        action="store_true",
        help="Expand abbreviated URLs to full form",
    )
    search_parser.add_argument(
        "--fetch",
        action="store_true",
        help="Also fetch each result and include full page content",
    )
    search_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="json",
        help="Output format when --fetch is used (default: json)",
    )
    search_parser.set_defaults(handler=_handle_search)

    fetch_parser = subparsers.add_parser(
        "fetch", help="Fetch a URL and convert to markdown or JSON"
    )
    fetch_parser.add_argument("url", help="URL to fetch")
    fetch_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    fetch_parser.add_argument(
        "--output", type=str, help="Save output to file instead of stdout"
    )
    fetch_parser.add_argument(
        "--title",
        action="store_true",
        help="Include page title in markdown output",
    )
    fetch_parser.set_defaults(handler=_handle_fetch)

    lookup_parser = subparsers.add_parser(
        "lookup",
        help="Search and fetch top results in one command",
    )
    lookup_parser.add_argument("query", help="Search query")
    lookup_parser.add_argument(
        "--num",
        type=int,
        default=3,
        help="Number of results to search and fetch (default 3)",
    )
    lookup_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    lookup_parser.add_argument(
        "--output",
        type=str,
        help="Output directory for individual result files",
    )
    lookup_parser.add_argument(
        "--time",
        dest="time_span",
        choices=["d", "w", "m", "y"],
        help="Time filter: d (day), w (week), m (month), y (year)",
    )
    lookup_parser.add_argument(
        "--site", help="Restrict search to a specific site"
    )
    lookup_parser.set_defaults(handler=_handle_lookup)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the ddgr-skill CLI.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 for success, 1 for errors.
    """
    import time

    _ensure_skills_installed()
    parser = build_parser()
    args = parser.parse_args(argv)

    # Initialize logging level based on verbosity flag
    level = logging.DEBUG if getattr(args, "verbose", False) else logging.INFO
    logging.getLogger().setLevel(level)

    if hasattr(args, "handler"):
        try:
            logger.info(f"Dispatching command: {args.command} with args: {vars(args)}")
            args.handler(args)
            return 0
        except DdgRSkillError as exc:
            logger.exception("An error occurred during execution")
            print(str(exc), file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 0
