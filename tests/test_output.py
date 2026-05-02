"""Tests for ddgr_skill.output module."""

import json
from pathlib import Path

from ddgr_skill.output import (
     format_fetch_result_json,
     format_fetch_result_markdown,
     format_lookup_results_json,
     format_lookup_results_markdown,
     format_search_results_json,
     generate_safe_filename,
     save_to_file,
     write_lookup_results,
)


class TestFormatSearchResultsJson:
    def test_formats_results_as_json(self, sample_search_results):
        result = format_search_results_json(sample_search_results)
        parsed = json.loads(result)
        assert parsed == sample_search_results

    def test_empty_results(self):
        result = format_search_results_json([])
        assert result == "[]"

    def test_unicode_handling(self):
        results = [{"title": "Café", "url": "https://example.com", "abstract": "é"}]
        result = format_search_results_json(results)
        assert "Café" in result


class TestFormatFetchResultMarkdown:
    def test_without_title(self):
        result = {"title": "Page", "url": "https://example.com", "content": "Body text"}
        output = format_fetch_result_markdown(result)
        assert output == "Body text"

    def test_with_title(self):
        result = {"title": "Page", "url": "https://example.com", "content": "Body text"}
        output = format_fetch_result_markdown(result, include_title=True)
        assert "# Page" in output
        assert "> Source: https://example.com" in output
        assert "Body text" in output


class TestFormatFetchResultJson:
    def test_formats_as_json(self):
        result = {"title": "Page", "url": "https://example.com", "content": "Body text"}
        output = format_fetch_result_json(result)
        parsed = json.loads(output)
        assert parsed == result


class TestFormatLookupResultsMarkdown:
    def test_single_result(self):
        results = [{"title": "Page", "url": "https://example.com", "content": "Body"}]
        output = format_lookup_results_markdown(results)
        assert "# Page" in output
        assert "> Source: https://example.com" in output
        assert "Body" in output

    def test_multiple_results_with_separator(self):
        results = [
            {"title": "Page 1", "url": "https://a.com", "content": "Body 1"},
            {"title": "Page 2", "url": "https://b.com", "content": "Body 2"},
         ]
        output = format_lookup_results_markdown(results)
        assert "---" in output
        assert "Page 1" in output
        assert "Page 2" in output

    def test_error_result(self):
        results = [{"title": "Failed", "url": "https://a.com", "error": "Timeout"}]
        output = format_lookup_results_markdown(results)
        assert "**Error: Timeout**" in output


class TestFormatLookupResultsJson:
    def test_formats_as_json_array(self):
        results = [{"title": "Page", "url": "https://example.com", "content": "Body"}]
        output = format_lookup_results_json(results)
        parsed = json.loads(output)
        assert parsed == results


class TestGenerateSafeFilename:
    def test_basic_title(self):
        result = generate_safe_filename("Hello World", 0)
        assert result == "0_hello-world.md"

    def test_special_characters(self):
        result = generate_safe_filename("Python 3.12 Release!", 1)
        assert result == "1_python-312-release.md"

    def test_long_title_truncation(self):
        long_title = "A" * 100
        result = generate_safe_filename(long_title, 0, max_length=50)
        assert result.startswith("0_a")
        assert len(result.replace("0_", "").replace(".md", "")) <= 50

    def test_json_extension(self):
        result = generate_safe_filename("Test", 0, extension=".json")
        assert result == "0_test.json"

    def test_unicode_removal(self):
        result = generate_safe_filename("Café München", 0)
        assert "é" not in result
        assert "ü" not in result


class TestSaveToFile:
    def test_writes_content(self, tmp_output_dir):
        path = tmp_output_dir / "test.txt"
        save_to_file("hello", path)
        assert path.read_text() == "hello"

    def test_creates_parent_dirs(self, tmp_output_dir):
        path = tmp_output_dir / "sub" / "deep" / "test.txt"
        save_to_file("content", path)
        assert path.exists()
        assert path.read_text() == "content"


class TestWriteLookupResults:
    def test_writes_markdown_files(self, tmp_output_dir):
        results = [
            {"title": "Page One", "url": "https://a.com", "content": "Body 1"},
            {"title": "Page Two", "url": "https://b.com", "content": "Body 2"},
         ]
        files = write_lookup_results(results, tmp_output_dir, format_="markdown")
        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)
        assert all(f.exists() for f in files)

    def test_writes_json_files(self, tmp_output_dir):
        results = [
            {"title": "Page", "url": "https://a.com", "content": "Body"},
         ]
        files = write_lookup_results(results, tmp_output_dir, format_="json")
        assert len(files) == 1
        assert files[0].suffix == ".json"
        parsed = json.loads(files[0].read_text())
        assert parsed["title"] == "Page"
