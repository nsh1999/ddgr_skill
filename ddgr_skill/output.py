"""Output formatting utilities."""

import json
import re
from pathlib import Path
from typing import Optional


def format_search_results_json(results):
    """Format search results as pretty-printed JSON string."""
    return json.dumps(results, indent=2, ensure_ascii=False)


def format_fetch_result_markdown(result, include_title=False):
    """Format a single fetch result as markdown text."""
    parts = []
    if include_title:
        parts.append(f"# {result['title']}\n\n")
        parts.append(f"> Source: {result['url']}\n\n")
    parts.append(result.get("content", ""))
    return "".join(parts)


def format_fetch_result_json(result):
    """Format a single fetch result as JSON object string."""
    return json.dumps(result, indent=2, ensure_ascii=False)


def format_lookup_results_markdown(results, separator="\n---\n\n"):
    """Format multiple lookup results as combined markdown."""
    formatted_parts = []
    for result in results:
        if "error" in result:
            formatted_parts.append(
                f"# {result['title']}\n\n"
                f"> Source: {result['url']}\n\n"
                f"> **Error: {result['error']}**"
              )
        else:
            formatted_parts.append(
                f"# {result['title']}\n\n"
                f"> Source: {result['url']}\n\n"
                f"{result.get('content', '')}"
              )
    return separator.join(formatted_parts)


def format_lookup_results_json(results):
    """Format multiple lookup results as JSON array string."""
    return json.dumps(results, indent=2, ensure_ascii=False)


def generate_safe_filename(title, index, extension=".md", max_length=50):
    """Generate a safe filename from a title."""
    safe = title.lower()
    safe = re.sub(r"[^a-z0-9\s-]", "", safe)
    safe = re.sub(r"\s+", "-", safe).strip("-")
    safe = safe[:max_length]
    return f"{index}_{safe}{extension}"


def save_to_file(content, output_path):
    """Write content string to file, creating parent dirs if needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def _format_single_result_for_file(result, format_):
    """Format a single result for file output, handling errors."""
    if format_ == "json":
        return format_fetch_result_json(result)

    if "error" in result:
        lines = [
            f"# {result['title']}",
            "",
            f"> Source: {result['url']}",
            "",
            f"> **Error: {result['error']}**",
          ]
        return "\n".join(lines)

    lines = [
        f"# {result['title']}",
        "",
        f"> Source: {result['url']}",
        "",
        result.get("content", ""),
      ]
    return "\n".join(lines)


def write_lookup_results(results, output_dir, format_="markdown"):
    """Write each lookup result to a file in output_dir."""
    extension = ".md" if format_ == "markdown" else ".json"
    created_files = []

    for index, result in enumerate(results):
        title = result.get("title", f"result_{index}")
        filename = generate_safe_filename(title, index, extension)
        output_path = output_dir / filename

        content = _format_single_result_for_file(result, format_)
        save_to_file(content, output_path)
        created_files.append(output_path)

    return created_files
