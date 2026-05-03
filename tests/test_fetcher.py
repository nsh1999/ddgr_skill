"""Tests for ddgr_skill.fetcher module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
import asyncio

from ddgr_skill.exceptions import ContentQualityError, HTTPError, NetworkError
from ddgr_skill.fetcher import (
    fetch_as_markdown,
    fetch_url,
    fetch_urls_concurrent,
    fetch_with_fallback,
    html_to_markdown,
    _extract_title,
    validate_content,
    _fetch_single_url_async,
    _fetch_single_url_with_retry,
    _is_retriable_error,
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


class TestValidateContent:
    def test_valid_content_passes(self):
        good_text = "A" * 200
        result = {"content": good_text, "title": "Page", "url": "https://example.com"}
        output = validate_content(result, "https://example.com")
        assert output is result

    def test_content_too_short(self):
        result = {"content": "Short", "title": "Page", "url": "https://example.com"}
        with pytest.raises(ContentQualityError, match="too short"):
            validate_content(result, "https://example.com")

    def test_borderline_length_passes(self):
        result = {"content": "A" * 150, "title": "Page", "url": "https://example.com"}
        output = validate_content(result, "https://example.com")
        assert output is result

    def test_js_only_page_rejected(self):
         # Content passes length check but has low ratio
        content_text = ("A " * 76).strip()
        result = {
            "content": content_text,
            "title": "Page",
            "url": "https://example.com",
            "_html_length": 50000,
        }
        with pytest.raises(ContentQualityError, match="ratio too low"):
            validate_content(result, "https://example.com")

    def test_navigation_dominance_rejected(self):
        nav_text = " ".join(["home"] * 50 + ["actual"] * 10)
        result = {"content": nav_text, "title": "Page", "url": "https://example.com"}
        with pytest.raises(ContentQualityError, match="navigation"):
            validate_content(result, "https://example.com")

    def test_cross_domain_redirect_rejected(self):
        result = {"content": "A" * 200, "title": "Page", "url": "https://a.com"}
        with pytest.raises(ContentQualityError, match="redirect"):
            validate_content(
                result, "https://a.com/page", "https://b.com/other"
             )

    def test_same_domain_redirect_ok(self):
        result = {
             "content": "A" * 200,
             "title": "Page",
             "url": "https://example.com",
         }
        output = validate_content(
             result,
             "http://example.com/page",
             "https://example.com/page",
         )
        assert output is result

    def test_missing_html_length_skips_ratio(self):
        result = {"content": "A" * 200, "title": "Page", "url": "https://example.com"}
        output = validate_content(result, "https://example.com")
        assert output is result


class TestIsRetriableError:
    def test_retries_network_error(self):
        assert _is_retriable_error(NetworkError("timeout"))

    def test_retries_500_error(self):
        assert _is_retriable_error(HTTPError("500 Internal Server Error for url"))

    def test_no_retry_404(self):
        assert not _is_retriable_error(HTTPError("404 Not Found for url"))

    def test_no_retry_403(self):
        assert not _is_retriable_error(HTTPError("403 Forbidden for url"))

    def test_no_retry_quality(self):
        assert not _is_retriable_error(ContentQualityError("too short"))


class TestFetchSingleUrlWithRetry:
    @patch("ddgr_skill.fetcher._fetch_single_url_async")
    def test_success_first_try(self, mock_async):
        good = {
            "title": "Page", "url": "https://a.com",
            "content": "A" * 200,
            "_html_length": 300, "_final_url": "https://a.com",
        }
        mock_async.return_value = good

        async def run():
            return await _fetch_single_url_with_retry(
                 "https://a.com", 10.0, "agent"
              )
        result = asyncio.run(run())
        assert "content" in result
        assert "_html_length" not in result
        assert "_final_url" not in result
        mock_async.assert_called_once()

    @patch("ddgr_skill.fetcher._fetch_single_url_async")
    def test_retry_on_timeout(self, mock_async):
         # First call times out, second succeeds
        error_result = {"title": "https://a.com", "url": "https://a.com",
              "error": "Timeout fetching https://a.com after 10.0s"}
        good = {
            "title": "Page", "url": "https://a.com",
            "content": "A" * 200,
            "_html_length": 300, "_final_url": "https://a.com",
        }
        mock_async.side_effect = [error_result, good]

        async def run():
            return await _fetch_single_url_with_retry(
                 "https://a.com", 10.0, "agent"
              )
        result = asyncio.run(run())
        assert "content" in result
        assert mock_async.call_count == 2

    @patch("ddgr_skill.fetcher._fetch_single_url_async")
    def test_no_retry_on_404(self, mock_async):
        error_result = {"title": "https://a.com", "url": "https://a.com",
              "error": "404 Not Found for https://a.com"}
        mock_async.return_value = error_result

        async def run():
            return await _fetch_single_url_with_retry(
                 "https://a.com", 10.0, "agent"
              )
        result = asyncio.run(run())
        assert "error" in result
        mock_async.assert_called_once()

    @patch("ddgr_skill.fetcher._fetch_single_url_async")
    def test_no_retry_on_quality_fail(self, mock_async):
         # Content fails quality check (too short)
        bad = {
            "title": "Page", "url": "https://a.com",
            "content": "short",
            "_html_length": 300, "_final_url": "https://a.com",
        }
        mock_async.return_value = bad

        async def run():
            return await _fetch_single_url_with_retry(
                 "https://a.com", 10.0, "agent"
              )
        result = asyncio.run(run())
        assert "error" in result
        mock_async.assert_called_once()

    @patch("ddgr_skill.fetcher._fetch_single_url_async")
    def test_exhausted_retries(self, mock_async):
        error_result = {"title": "https://a.com", "url": "https://a.com",
              "error": "Timeout fetching https://a.com after 10.0s"}
        mock_async.return_value = error_result

        async def run():
            return await _fetch_single_url_with_retry(
                 "https://a.com", 10.0, "agent", max_retries=2
              )
        result = asyncio.run(run())
        assert "error" in result
        assert mock_async.call_count == 3


class TestFetchWithFallback:
    def test_returns_good_results(self):
        """All URLs succeed - returns target count."""
        search_results = [
            {"url": "https://a.com", "title": "A"},
            {"url": "https://b.com", "title": "B"},
            {"url": "https://c.com", "title": "C"},
        ]
        good_a = {
            "title": "A", "url": "https://a.com",
            "content": "A" * 200,
            "_html_length": 300, "_final_url": "https://a.com",
        }
        good_b = {
            "title": "B", "url": "https://b.com",
            "content": "B" * 200,
            "_html_length": 300, "_final_url": "https://b.com",
        }
        good_c = {
            "title": "C", "url": "https://c.com",
            "content": "C" * 200,
            "_html_length": 300, "_final_url": "https://c.com",
        }

        with patch(
            "ddgr_skill.fetcher._fetch_single_url_async",
            return_value=good_a,
        ) as mock:
            mock.side_effect = [good_a, good_b, good_c]
            results, all_failed = fetch_with_fallback(
                search_results, num_target=3
            )
            assert len([r for r in results if "content" in r]) == 3
            assert all_failed is False

    def test_fallback_on_first_failure(self):
        """First URL fails, falls back to second."""
        search_results = [
            {"url": "https://a.com", "title": "A"},
            {"url": "https://b.com", "title": "B"},
            {"url": "https://c.com", "title": "C"},
        ]
        error_a = {
            "title": "https://a.com", "url": "https://a.com",
            "error": "404 Not Found for https://a.com",
        }
        good_b = {
            "title": "B", "url": "https://b.com",
            "content": "B" * 200,
            "_html_length": 300, "_final_url": "https://b.com",
        }
        good_c = {
            "title": "C", "url": "https://c.com",
            "content": "C" * 200,
            "_html_length": 300, "_final_url": "https://c.com",
        }

        with patch(
            "ddgr_skill.fetcher._fetch_single_url_async",
        ) as mock:
            mock.side_effect = [error_a, good_b, good_c]
            results, all_failed = fetch_with_fallback(
                search_results, num_target=2
            )
            good_results = [r for r in results if "content" in r]
            error_results = [r for r in results if "error" in r]
            assert len(good_results) == 2
            assert len(error_results) == 1
            assert all_failed is False

    def test_all_failed_returns_error_results(self):
        """When all fetches fail, returns error results with all_failed=True."""
        search_results = [
            {"url": "https://a.com", "title": "A"},
            {"url": "https://b.com", "title": "B"},
        ]
        error_a = {
            "title": "https://a.com", "url": "https://a.com",
            "error": "404 Not Found for https://a.com",
        }
        error_b = {
            "title": "https://b.com", "url": "https://b.com",
            "error": "403 Forbidden for https://b.com",
        }

        with patch(
            "ddgr_skill.fetcher._fetch_single_url_async",
        ) as mock:
            mock.side_effect = [error_a, error_b]
            results, all_failed = fetch_with_fallback(
                search_results, num_target=2
            )
            assert len(results) == 2
            assert all(r.get("error") for r in results)
            assert all_failed is True

    def test_quality_fail_triggers_fallback(self):
        """Content quality failures trigger fallback to next URL."""
        search_results = [
            {"url": "https://a.com", "title": "A"},
            {"url": "https://b.com", "title": "B"},
        ]
        bad_quality = {
            "title": "A", "url": "https://a.com",
            "content": "short",
            "_html_length": 300, "_final_url": "https://a.com",
        }
        good_b = {
            "title": "B", "url": "https://b.com",
            "content": "B" * 200,
            "_html_length": 300, "_final_url": "https://b.com",
        }

        with patch(
            "ddgr_skill.fetcher._fetch_single_url_async",
        ) as mock:
            mock.side_effect = [bad_quality, good_b]
            results, all_failed = fetch_with_fallback(
                search_results, num_target=1
            )
            good_results = [r for r in results if "content" in r]
            assert len(good_results) == 1
            assert all_failed is False

    def test_empty_search_results(self):
        """Empty search results return empty list with all_failed=False."""
        results, all_failed = fetch_with_fallback([], num_target=3)
        assert results == []
        assert all_failed is False

    def test_strips_internal_metadata_on_success(self):
        """Successful results don't expose _html_length or _final_url."""
        search_results = [{"url": "https://a.com", "title": "A"}]
        good = {
            "title": "A", "url": "https://a.com",
            "content": "A" * 200,
            "_html_length": 300, "_final_url": "https://a.com",
        }

        with patch(
            "ddgr_skill.fetcher._fetch_single_url_async",
            return_value=good,
        ):
            results, all_failed = fetch_with_fallback(
                search_results, num_target=1
            )
            assert len(results) == 1
            assert "_html_length" not in results[0]
            assert "_final_url" not in results[0]

    def test_fetches_more_when_needed(self):
        """Fetches extra from buffer when initial results fail."""
        search_results = [
            {"url": f"https://{i}.com", "title": str(i)}
            for i in range(1, 8)
        ]
        error_results = []
        for i in range(1, 4):
            error_results.append({
                "title": f"https://{i}.com",
                "url": f"https://{i}.com",
                "error": f"404 Not Found for https://{i}.com",
            })
        good_results_list = []
        for i in range(4, 8):
            good_results_list.append({
                "title": str(i), "url": f"https://{i}.com",
                "content": f"{i}" * 200,
                "_html_length": 300,
                "_final_url": f"https://{i}.com",
            })

        with patch(
            "ddgr_skill.fetcher._fetch_single_url_async",
        ) as mock:
            mock.side_effect = error_results + good_results_list
            results, all_failed = fetch_with_fallback(
                search_results, num_target=2
            )
            good = [r for r in results if "content" in r]
            assert len(good) >= 2
            assert all_failed is False


