# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

ddgr_skill is a Python 3.12 CLI tool that wraps the [ddgr](https://github.com/jremix/ddgr)
DuckDuckGo search utility. It provides three subcommands:

- **search** -- Query DuckDuckGo and return results as JSON
- **fetch** -- Fetch a URL and convert HTML to markdown or JSON
- **lookup** -- Search and fetch top results in one command

A Claude Code skill is installed at `~/.claude/skills/ddgr-skill/SKILL.md`.

## Dependencies

- Python 3.12.11, managed by `uv` (v0.6.14)
- `ddgr` v2.2 (Homebrew) -- DuckDuckGo search CLI
- `beautifulsoup4` -- HTML parsing for tag stripping
- `httpx` -- HTTP client with async support
- `markdownify` -- HTML-to-markdown conversion

## Environment Setup

```bash
source .venv/bin/activate
uv sync        # Install all dependencies
```

## Commands

| Task | Command |
|---|---|
| Install dependencies | `uv sync` |
| Add a package | `uv add <package>` |
| Run the CLI | `python -m ddgr_skill` |
| Run all tests | `uv run pytest -v` |
| Run unit tests only | `uv run pytest -v -m "not integration"` |
| Run a single test | `uv run pytest tests/test_foo.py::test_bar -v` |
| Run tests with coverage | `uv run pytest --cov=ddgr_skill --cov-report=term-missing` |

## Project Structure

```
ddgr_skill/
├── pyproject.toml              # Project metadata, deps, build config
├── ddgr_skill/
│    ├── __init__.py            # Package version
│    ├── __main__.py            # Entry point (python -m ddgr_skill)
│    ├── cli.py                 # Argparse + command dispatch
│    ├── search.py              # ddgr subprocess wrapper
│    ├── fetcher.py             # HTTP fetching + HTML-to-markdown
│    ├── output.py              # Output formatting utilities
│    └── exceptions.py          # Custom exception hierarchy
└── tests/
     ├── conftest.py            # Shared fixtures
     ├── test_search.py         # search.py tests (mocked subprocess)
     ├── test_fetcher.py        # fetcher.py tests (mocked httpx)
     ├── test_output.py         # output.py tests
     ├── test_cli.py            # CLI parsing tests
     └── test_integration.py    # Real ddgr/network tests (skip by default)
```

## Architecture

- **search.py** runs `ddgr --json --np` via `subprocess.run`, parses JSON output, and maps CLI options to ddgr flags
- **fetcher.py** uses `httpx` for HTTP requests and `markdownify` + `BeautifulSoup` for HTML-to-markdown conversion with nav/header/footer/aside stripping
- **output.py** handles formatting (JSON, markdown) and file output with safe filename generation
- **cli.py** dispatches subcommands via `argparse` with three subparsers
- Integration tests are marked with `@pytest.mark.integration` and skipped by default
