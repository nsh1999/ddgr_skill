---
name: ddgr-skill
description: Search the web using DuckDuckGo (ddgr) and fetch page content as markdown or JSON
origin: nsh1999
---

# Web Search and Content Retrieval

Use `ddgr-skill` to search DuckDuckGo and retrieve full web page content. The tool
searches the web and fetches result pages as readable markdown via `fetcher.py`.

Requires [ddgr](https://github.com/jremix/ddgr) installed via Homebrew: `brew install ddgr`.

## Default Behavior

**Always use `lookup`** when the user asks a factual question or wants to research a
topic. `lookup` searches DuckDuckGo and fetches the top results as markdown in one
step. This is the preferred mode for Claude Code integration.

```bash
ddgr-skill lookup "what is the weather in Zurich today?"
```

The output is markdown with page titles, source URLs, and full page content.
Failed fetches include an error message but successful results are still returned.

## Commands

### Lookup (default)

Search and fetch the top results in one command:

```bash
ddgr-skill lookup "your query"
```

Options:
- `--num N` -- Number of results to search and fetch (default 3)
- `--format markdown|json` -- Output format (default: markdown)
- `--output DIR` -- Save each result as a separate file in a directory
- `--time SPAN` -- Time filter: `d`, `w`, `m`, `y`
- `--site SITE` -- Restrict search to a specific site

When `--output` is a directory, each result is saved as `<index>_<safe_filename>.md` or `.json`.

### Search

Search DuckDuckGo and return results as JSON (titles, URLs, abstracts only):

```bash
ddgr-skill search "your query" --num 5
```

Use `search` only when you need a broad scan of titles/URLs without fetching full
page content. Adding `--fetch` turns it into a lookup operation.

Options:
- `--num N` -- Number of results (1-25, default 10)
- `--time SPAN` -- Time filter: `d` (day), `w` (week), `m` (month), `y` (year)
- `--site SITE` -- Restrict search to a specific site
- `--region REG` -- Region code (e.g., `wt-wt` for worldwide)
- `--expand` -- Expand abbreviated URLs to full form
- `--fetch` -- Also fetch each result and include full page content (turns into lookup)

Output is a JSON array to stdout with objects containing `title`, `url`, and `abstract`.

### Fetch

Fetch a single URL and convert HTML to readable markdown:

```bash
ddgr-skill fetch "https://example.com/page"
```

Options:
- `--format markdown|json` -- Output format (default: markdown)
- `--output FILE` -- Save output to a file instead of stdout
- `--title` -- Include page title and source in markdown output

## Workflow Examples

**Answer a question (default):**
```bash
ddgr-skill lookup "what is the weather in Zurich today?"
```

**Research a topic with saved results:**
```bash
ddgr-skill lookup "Python async programming" --num 5 --output ./research
```

**Quick fact-check as JSON:**
```bash
ddgr-skill lookup "event loop implementation" --num 2 --format json
```

**Site-specific research:**
```bash
ddgr-skill lookup "pytest fixtures" --site docs.pytest.org --num 3
```

**Browse titles without fetching (rare):**
```bash
ddgr-skill search "Python async programming" --num 10
```

## Error Handling

- **ddgr not installed**: Clear error with installation instructions
- **Network errors**: 10s timeout per URL, connection failures reported per-URL
- **HTTP errors**: 404, 500 etc. reported with status code
- **Partial failures**: In lookup mode, failed fetches include an "error" key but successful results are still returned
