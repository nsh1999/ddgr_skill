"""Integration tests that use real ddgr and network calls.

Skip by default. Run with: pytest -m integration
"""


import pytest


from ddgr_skill.fetcher import fetch_as_markdown
from ddgr_skill.search import search



@pytest.mark.integration
def test_search_real_query():
    results = search("python", num_results=2)
    assert len(results) > 0
    assert all("title" in result for result in results)
    assert all("url" in result for result in results)



@pytest.mark.integration
def test_fetch_real_url():
    result = fetch_as_markdown("https://example.com", timeout=10)
    assert "Example Domain" in result["title"]
    assert result["url"] == "https://example.com"
    assert len(result["content"]) > 0
