"""Argument parsing and command dispatch for ddgr-skill."""

import argparse
import json
import sys
from pathlib import Path

from ddgr_skill.exceptions import DdgRSkillError
from ddgr_skill.fetcher import fetch_as_markdown, fetch_urls_concurrent
from ddgr_skill.output import (
    format_fetch_result_json,
    format_fetch_result_markdown,
    format_lookup_results_json,
    format_lookup_results_markdown,
    format_search_results_json,
    save_to_file,
    write_lookup_results,
)
from ddgr_skill.search import search


def _handle_search(args: argparse.Namespace) -> None:
    """Handle the 'search' subcommand."""
    results = search(
        query=args.query,
        num_results=args.num,
        time_span=args.time_span,
        site=args.site,
        region=args.region,
        expand_urls=args.expand,
    )
    print(format_search_results_json(results))


def _handle_fetch(args: argparse.Namespace) -> None:
    """Handle the 'fetch' subcommand."""
    result = fetch_as_markdown(args.url)

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


def _handle_lookup(args: argparse.Namespace) -> None:
    """Handle the 'lookup' subcommand."""
    search_results = search(
        query=args.query,
        num_results=args.num,
        time_span=args.time_span,
        site=args.site,
    )

    if not search_results:
        print(json.dumps([], indent=2))
        return

    urls = [entry["url"] for entry in search_results[:args.num]]
    results = fetch_urls_concurrent(urls)

    if args.output:
        write_lookup_results(results, Path(args.output), format_=args.format)
        return

    if args.format == "json":
        print(format_lookup_results_json(results))
    else:
        print(format_lookup_results_markdown(results))


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="ddgr-skill",
        description="Search the web via DuckDuckGo and fetch page content.",
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
    parser = build_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "handler"):
        try:
            args.handler(args)
            return 0
        except DdgRSkillError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 0
