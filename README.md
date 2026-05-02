# ddgr-skill

CLI tool for web search via [ddgr](https://github.com/jremix/ddgr) and page content fetching.

## Disclaimer

This tool is provided "as is", without warranty of any kind, express or implied. Use it at your own risk.

The authors are not responsible for any misuse of this software, including but not limited to:
- Excessive or automated requests to DuckDuckGo servers
- Scraping of content that violates third-party terms of service or applicable laws
- Any decisions made based on search or fetched content returned by this tool

Users are responsible for ensuring their usage complies with DuckDuckGo's terms of service and all applicable laws and regulations.

## Installation


### Installing ddgr-skill

ddgr-skill is available only via GitHub. Clone the repository and install dependencies:

```bash
git clone https://github.com/nsh1999/ddgr_skill.git
cd ddgr_skill
uv sync
```

### Installing as a Claude Code Skill

Copy the skill definition to your Claude Code skills directory:

```bash
mkdir -p ~/.claude/skills/ddgr-skill
cp path/to/ddgr_skill/.claude/skills/ddgr-skill/SKILL.md ~/.claude/skills/ddgr-skill/
```

Restart Claude Code. The skill is now available via `/ddgr-skill` or automatically triggered when you ask about web search.

### Installing as a Hermes-Agent Skill

Copy the skill definition to your Hermes-Agent skills directory:

```bash
mkdir -p ~/.hermes/skills/web/ddgr-skill
cp path/to/ddgr_skill/.claude/skills/ddgr-skill/SKILL.md ~/.hermes/skills/web/ddgr-skill/
```

Or install from a URL:

```bash
hermes skills install https://raw.githubusercontent.com/nsh1999/ddgr_skill/main/.claude/skills/ddgr-skill/SKILL.md
```

Verify the skill is installed:

```bash
hermes skills list
```

The skill is now available via `/ddgr-skill` or `hermes chat --toolsets skills -q "use ddgr-skill to..."`.

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
