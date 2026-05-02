"""Tests for ddgr_skill.fetcher module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from ddgr_skill.exceptions import HTTPError, NetworkError
from ddgr_skill.fetcher import (
    fetch_as_markdown,
    fetch_url,
    fetch_urls_concurrent,
    html_to_markdown,
    _extract_title,
)


def _make_mock_response(status_code=200, text="", reason_phrase="OK"):
    mock = MagicMock(spec=httpx.Response)
    mock.status_code = status_code
    mock.text = text
    mock.reason_phrase = reason_phrase
    if status_code == 200:
        mock.raise_for_status = MagicMock()
    else:
        mock.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                f"{status_code} Error",
                request=MagicMock(),
                response=mock,
            )
        )
    return mock


class TestFetchUrl:
    def test_fetch_url_success(self):
        mock_resp = _make_mock_response(200, "<html><body>Hello</body></html>")
        with patch("httpx.get", return_value=mock_resp):
            result = fetch_url("https://example.com")
            assert result.text == "<html><body>Hello</body></html>"

    def test_fetch_url_timeout(self):
        with patch("httpx.get", side_effect=httpx.TimeoutException("timed out")):
            with pytest.raises(NetworkError, match="Timeout"):
                fetch_url("https://example.com")

    def test_fetch_url_connect_error(self):
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            with pytest.raises(NetworkError, match="Network error"):
                fetch_url("https://example.com")

    def test_fetch_url_ssl_error(self):
        with patch("httpx.get", side_effect=httpx.RequestError("ssl")):
            with pytest.raises(NetworkError, match="Network error"):
                fetch_url("https://example.com")

    def test_fetch_url_too_many_redirects(self):
        with patch("httpx.get", side_effect=httpx.TooManyRedirects("loop")):
            with pytest.raises(NetworkError, match="Too many redirects"):
                fetch_url("https://example.com")

    def test_fetch_url_404(self):
        mock_resp = _make_mock_response(404, "Not Found", "Not Found")
        with patch("httpx.get", return_value=mock_resp):
            with pytest.raises(HTTPError, match="404"):
                fetch_url("https://example.com/page")

    def test_fetch_url_500(self):
        mock_resp = _make_mock_response(500, "Server Error", "Internal Server Error")
        with patch("httpx.get", return_value=mock_resp):
            with pytest.raises(HTTPError, match="500"):
                fetch_url("https://example.com/api")


class TestHtmlToMarkdown:
    def test_converts_headings_and_paragraphs(self):
        html = "<h1>Hello</h1><p>World</p>"
        result = html_to_markdown(html)
        assert "Hello" in result
        assert "World" in result

    def test_strips_script_content(self):
        html = "<p>Keep</p><script>alert(1)</script>"
        result = html_to_markdown(html)
        assert "alert" not in result
        assert "Keep" in result

    def test_strips_style_content(self):
        html = "<p>Content</p><style>.x { color: red }</style>"
        result = html_to_markdown(html)
        assert ".x" not in result
        assert "Content" in result

    def test_strips_nav_content(self):
        html = "<p>Main</p><nav>Skip this</nav>"
        result = html_to_markdown(html)
        assert "Skip this" not in result
        assert "Main" in result


class TestExtractTitle:
    def test_extract_title_from_html(self):
        html = "<html><head><title>My Page</title></head></html>"
        assert _extract_title(html) == "My Page"

    def test_extract_title_with_attributes(self):
        html = '<html><head><title class="x">My Page</title></head></html>'
        assert _extract_title(html) == "My Page"

    def test_no_title_returns_none(self):
        html = "<html><body>No title here</body></html>"
        assert _extract_title(html) is None


class TestFetchAsMarkdown:
    def test_fetch_with_title(self):
        html = "<html><head><title>Test Page</title></head><body><p>Content</p></html>"
        mock_resp = _make_mock_response(200, html)
        with patch("httpx.get", return_value=mock_resp):
            result = fetch_as_markdown("https://example.com")
            assert result["title"] == "Test Page"
            assert result["url"] == "https://example.com"
            assert "Content" in result["content"]

    def test_fetch_fallback_title(self):
        html = "<html><body>No title</body></html>"
        mock_resp = _make_mock_response(200, html)
        with patch("httpx.get", return_value=mock_resp):
            result = fetch_as_markdown("https://example.com/page")
            assert result["title"] == "https://example.com/page"


class TestFetchUrlsConcurrent:
    @patch("ddgr_skill.fetcher._fetch_single_url_async")
    def test_concurrent_fetch_returns_results(self, mock_async):
        mock_async.return_value = {
            "title": "Page A",
            "url": "https://a.com",
            "content": "Body A",
        }
        fetched = fetch_urls_concurrent(["https://a.com", "https://b.com"])
        assert len(fetched) == 2

    @patch("ddgr_skill.fetcher._fetch_single_url_async")
    def test_partial_failure_preserves_success(self, mock_async):
        good = {"title": "OK", "url": "https://a.com", "content": "Body"}
        bad = {"title": "https://b.com", "url": "https://b.com", "error": "Timeout"}

        async def side_effect(*args):
            if args[0] == "https://a.com":
                return good
            return bad

        mock_async.side_effect = side_effect
        fetched = fetch_urls_concurrent(["https://a.com", "https://b.com"])
        assert len(fetched) == 2
        assert "content" in fetched[0]
        assert "error" in fetched[1]
