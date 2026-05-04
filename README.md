# ddgr-skill

CLI tool for web search via [ddgr](https://github.com/jremix/ddgr) and page content fetching.

## Disclaimer

This tool is provided "as is", without warranty of any kind, express or implied. Use it at your own risk.

The authors are not responsible for any misuse of this software, including but not limited to:
- Excessive or automated requests to DuckDuckGo servers
- Scraping of content that violates third-party terms of service or applicable laws
- Any decisions made based on search or fetched content returned by this tool

Users are responsible for ensuring their usage complies with DuckDuckGo's terms of service and all applicable laws and regulations.

## ⚠️ Limitations

### Bot Protection & Cloudflare
`ddgr-skill` is designed as a lightweight CLI tool using static HTTP clients. Consequently, it cannot bypass advanced bot protection mechanisms (such as Cloudflare's "Under Attack" mode) used by some websites (e.g., `timeanddate.com`).

These sites require:
- **JavaScript Execution:** To solve browser challenges.
- **Cookie Handling:** Support for complex challenge-response cookie flows.
- **TLS Fingerprinting:** Evasion of detection patterns used by libraries like `httpx` or `requests`.

To support these sites, a headless browser (e.g., Playwright or Selenium) would be required. To keep the tool lightweight and minimize dependencies, this has not been implemented. The tool continues to work reliably for the vast majority of sites using standard header checks.


## Prerequisites

- **Python 3.12+**
- **[uv](https://astral.sh/uv)** - Python package manager
- **[ddgr](https://github.com/jremix/ddgr)** - Install via `brew install ddgr`

## Installation

### Quick Install (Claude Code)

```bash
git clone https://github.com/nsh1999/ddgr_skill.git
cd ddgr_skill
bash install/install_ddgr_skill.sh
```

This installs dependencies, sets up the CLI, and copies the skill definition to `~/.claude/skills/ddgr-skill/`. Restart Claude Code to activate.

### Manual Install

```bash
git clone https://github.com/nsh1999/ddgr_skill.git
cd ddgr_skill
uv sync
mkdir -p ~/.claude/skills/ddgr-skill
cp skills/ddgr-skill/SKILL.md ~/.claude/skills/ddgr-skill/
```

## Usage

### Lookup (default - search + fetch)

The `lookup` command searches DuckDuckGo and fetches full page content as markdown. It will return exactly the first $N$ successfully fetched results, automatically skipping and ignoring any URLs that return errors (e.g., 403 Forbidden or 404 Not Found).

```bash
uv run ddgr-skill lookup "what is the weather in Zurich today?" --num 3
```

### Search with Fetch

Use `search --fetch` to search and fetch results in one step:

```bash
uv run ddgr-skill search "Python async programming" --num 5 --fetch --format markdown
```

### Verbose Logging

Enable detailed logging (including exact `ddgr` commands and HTTP requests) by adding the `-v` or `--verbose` flag:

```bash
uv run ddgr-skill -v lookup "what is the weather in Zurich today?"
```

### Other Commands

| Command | Example |
|---------|---------|
| Search (titles only) | `uv run ddgr-skill search "python" --num 5` |
| Fetch single URL | `uv run ddgr-skill fetch "https://example.com"` |
| Lookup (search + fetch) | `uv run ddgr-skill lookup "topic" --num 3` |
| Save to directory | `uv run ddgr-skill lookup "topic" --output ./research` |

## Development

```bash
uv run pytest -v                      # All tests
uv run pytest -v -m "not integration" # Unit tests only
uv run pytest --cov=ddgr_skill       # With coverage
```

## License

MIT License

Copyright (c) 2026 ddgr-skill contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
