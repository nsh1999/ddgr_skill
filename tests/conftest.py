"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_search_results():
    """Sample ddgr search results for testing."""
    return [
        {
            "title": "Python.org",
            "url": "https://www.python.org/",
            "abstract": "The official home of the Python programming language.",
        },
        {
            "title": "Docs - Python",
            "url": "https://docs.python.org/3/",
            "abstract": "Python 3 documentation.",
        },
    ]


@pytest.fixture
def sample_html():
    """Sample HTML document for fetcher tests."""
    return """<!DOCTYPE html>
    <html><head><title>Test Page</title></head>
    <body><h1>Hello</h1><p>Content here.</p><script>bad()</script><nav>Skip</nav></body>
    </html>"""


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Empty directory for output file tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
