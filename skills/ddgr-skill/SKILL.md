---
name: ddgr-skill
description: Search the web using DuckDuckGo (ddgr) and fetch page content as markdown or JSON
origin: nsh1999
---

# Web Search and Content Retrieval

Use `ddgr-skill` to search DuckDuckGo and retrieve web page content.

Requires [ddgr](https://github.com/jremix/ddgr) installed via Homebrew: `brew install ddgr`.

## Commands

### Search

Search DuckDuckGo and return results as JSON:

```bash
ddgr-skill search "your query" --num 5
```

Options:
- `--num N` -- Number of results (1-25, default 10)
- `--time SPAN` -- Time filter: `d` (day), `w` (week), `m` (month), `y` (year)
- `--site SITE` -- Restrict search to a specific site
- `--region REG` -- Region code (e.g., `wt-wt` for worldwide)
- `--expand` -- Expand abbreviated URLs to full form

Output is a JSON array to stdout with objects containing `title`, `url`, and `abstract`.

### Fetch

Fetch a single URL and convert to readable markdown:

```bash
ddgr-skill fetch "https://example.com/page"
```

Options:
- `--format markdown|json` -- Output format (default: markdown)
- `--output FILE` -- Save output to a file instead of stdout
- `--title` -- Include page title and source in markdown output

### Lookup

Search and fetch the top results in one command:

```bash
ddgr-skill lookup "your query" --num 3
```

Options:
- `--num N` -- Number of results to search and fetch (default 3)
- `--format markdown|json` -- Output format (default: markdown with separators)
- `--output DIR` -- Save each result as a separate file in a directory
- `--time SPAN` -- Time filter: `d`, `w`, `m`, `y`
- `--site SITE` -- Restrict search to a specific site

When `--output` is a directory, each result is saved as `<index>_<safe_filename>.md` or `.json`.

## Workflow Examples

**Research a topic:**
```bash
ddgr-skill search "Python async programming" --num 5
ddgr-skill fetch "https://docs.python.org/3/library/asyncio.html" --title
ddgr-skill lookup "latest Python release notes" --num 3 --output ./research
```

**Quick fact-check:**
```bash
ddgr-skill lookup "event loop implementation" --num 2 --format json
```

**Site-specific research:**
```bash
ddgr-skill search "pytest fixtures" --site docs.pytest.org --num 5
```

## Error Handling

- **ddgr not installed**: Clear error with installation instructions
- **Network errors**: 10s timeout per URL, connection failures reported per-URL
- **HTTP errors**: 404, 500 etc. reported with status code
- **Partial failures**: In lookup mode, failed fetches include an "error" key but successful results are still returned
