"""HTTP fetching and HTML-to-markdown conversion."""

import asyncio
import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import httpx
import markdownify

from ddgr_skill.exceptions import ContentQualityError, HTTPError, NetworkError

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10.0
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_STRIP_TAGS = ["nav", "header", "footer", "aside"]
_MIN_CONTENT_LENGTH = 150
_MAX_NAV_WORD_RATIO = 0.40
_MIN_CONTENT_RATIO = 0.05
_NAV_WORDS = frozenset({
    "home", "about", "contact", "privacy", "terms", "login", "sign",
    "register", "menu", "skip", "search", "copyright", "cookies",
})
_STRIP_PUNCT = re.compile(r"[^\w\s]")
_DEFAULT_NUM = 3
_RETRIABLE_HTTP_CODES = frozenset(range(500, 600))
_MAX_RETRIES = 2
_RETRY_DELAYS = [0.5, 1.0]


def fetch_url(url, timeout=_DEFAULT_TIMEOUT, headers=_DEFAULT_HEADERS):
    """Fetch a URL and return the response."""
    try:
        # Use a client to enable HTTP/2 support
        with httpx.Client(http2=True) as client:
            response = client.get(
                url, timeout=timeout, follow_redirects=True,
                headers=headers
            )
            # Copy the response content so it's available outside the client context
            response.read()
            return response
    except httpx.TimeoutException as exc:
        raise NetworkError(
            f"Timeout fetching {url} after {timeout}s"
        ) from exc
    except httpx.TooManyRedirects as exc:
        raise NetworkError(
            f"Too many redirects for {url}"
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(
            f"Network error fetching {url}: {exc}"
        ) from exc
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPError(
            f"{exc.response.status_code} {exc.response.reason_phrase} "
            f"for {url}"
        ) from exc
    return response


def html_to_markdown(html_content):
    """Convert HTML content to markdown."""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    return markdownify.markdownify(str(soup)).strip()


def _extract_title(html_content):
    """Extract the page title from HTML."""
    match = _TITLE_RE.search(html_content)
    if match:
        return markdownify.markdownify(match.group(1)).strip()
    return None


def validate_content(result, original_url, final_url=None):
    """Validate fetched content quality.

    Checks content length, HTML ratio, navigation dominance, and redirects.

    Args:
        result: Result dict with content, title, url keys.
        original_url: The URL that was requested.
        final_url: The URL after redirects (None if no redirect).

    Returns:
        The result dict if valid.

    Raises:
        ContentQualityError: If content fails any quality check.
    """
    content_text = result.get("content", "").strip()

    if len(content_text) < _MIN_CONTENT_LENGTH:
        reason = f"Content too short: {len(content_text)} chars"
        logger.debug(f"Quality check failed for {original_url}: {reason}")
        raise ContentQualityError(reason)

    html_length = result.get("_html_length")
    if html_length is not None and html_length > 0:
        ratio = len(content_text) / html_length
        if ratio < _MIN_CONTENT_RATIO:
            reason = f"Content-to-HTML ratio too low: {ratio:.2%}"
            logger.debug(f"Quality check failed for {original_url}: {reason}")
            raise ContentQualityError(reason)

    words = content_text.split()
    if words:
        word_set = {_STRIP_PUNCT.sub("", w).lower() for w in words}
        nav_count = len(word_set & _NAV_WORDS)
        if nav_count / len(word_set) > _MAX_NAV_WORD_RATIO:
            reason = "Content dominated by navigation text"
            logger.debug(f"Quality check failed for {original_url}: {reason}")
            raise ContentQualityError(reason)

    if final_url:
        orig = urlparse(original_url)
        final = urlparse(final_url)
        if orig.netloc and final.netloc and orig.netloc != final.netloc:
            reason = f"Unexpected redirect from {orig.netloc} to {final.netloc}"
            logger.debug(f"Quality check failed for {original_url}: {reason}")
            raise ContentQualityError(reason)

    return result


def fetch_as_markdown(url, timeout=_DEFAULT_TIMEOUT):
    """Fetch a URL and return structured content."""
    response = fetch_url(url, timeout=timeout)
    title = _extract_title(response.text) or url
    content = html_to_markdown(response.text)
    return {"title": title, "url": url, "content": content}


async def _fetch_single_url_async(url, timeout, headers):
    """Fetch a single URL asynchronously."""
    try:
        logger.debug(f"Requesting URL: {url}")
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, http2=True
        ) as client:
            response = await client.get(
                url, headers=headers
            )
            logger.debug(f"Response received for {url}: {response.status_code}")
            response.raise_for_status()
            title = _extract_title(response.text) or url
            content_text = html_to_markdown(response.text)
            return {
                "title": title,
                "url": url,
                "content": content_text,
                "_html_length": len(response.text),
                "_final_url": str(response.url),
            }
    except Exception as exc:
        logger.debug(f"Error fetching {url}: {exc}")
        return {"title": url, "url": url, "error": str(exc)}


def _is_retriable_error(exc):
    """Check if an exception is eligible for retry.

    Retries network errors and 5xx HTTP errors.
    Does not retry 4xx client errors or content quality issues.
    """
    if isinstance(exc, NetworkError):
        return True
    if isinstance(exc, HTTPError):
        msg = str(exc)
        code = int(msg.split()[0]) if msg.split() else 0
        return code in _RETRIABLE_HTTP_CODES
    return False


async def _fetch_single_url_with_retry(
    url, timeout, headers, max_retries=_MAX_RETRIES
):
    """Fetch a single URL with retry and content validation.

    Retries transient errors (timeouts, 5xx) with exponential backoff.
    On success, validates content quality and strips internal metadata.

    Returns:
        Result dict. On success: includes title, url, content.
        On failure: includes title, url, error.
    """
    for attempt in range(max_retries + 1):
        result = await _fetch_single_url_async(url, timeout, headers)

        if "error" in result:
            err_msg = result["error"]
            is_retriable = (
                "Timeout" in err_msg
                or "refused" in err_msg
                or "TLS" in err_msg
                or any(
                    f"{code} " in err_msg
                    for code in _RETRIABLE_HTTP_CODES
                )
            )
            if is_retriable and attempt < max_retries:
                delay = _RETRY_DELAYS[attempt]
                logger.info(f"Retry {attempt + 1}/{max_retries} for {url} after {delay}s (Reason: {err_msg})")
                await asyncio.sleep(delay)
                continue
            return result

        # Success - validate content quality
        try:
            validate_content(result, url, result.get("_final_url"))
            result.pop("_html_length", None)
            result.pop("_final_url", None)
            return result
        except ContentQualityError:
            return {
                "title": url,
                "url": url,
                "error": "Content quality check failed",
            }

    return {"title": url, "url": url, "error": "Max retries exceeded"}


def fetch_urls_concurrent(urls, timeout=_DEFAULT_TIMEOUT):
    """Fetch multiple URLs concurrently."""
    async def _run():
        tasks = [
            _fetch_single_url_async(url, timeout, _DEFAULT_HEADERS)
            for url in urls
        ]
        return await asyncio.gather(*tasks)

    return list(asyncio.run(_run()))


def fetch_with_fallback(
    search_results, num_target=_DEFAULT_NUM, timeout=_DEFAULT_TIMEOUT
):
    """Fetch URLs from search results with feed-forward fallback.

    Fetches URLs in batches and keeps fetching from the buffer
    until we have enough good results.

    Args:
        search_results: List of search result dicts with url key.
        num_target: Desired number of good (non-error) results.
        timeout: HTTP timeout per URL in seconds.

    Returns:
        Tuple of (results_list, all_failed_bool).
    """
    good_results = []
    error_results = []
    url_index = 0

    async def _run():
        nonlocal url_index

        while (
            len(good_results) < num_target
            and url_index < len(search_results)
        ):
            still_needed = num_target - len(good_results)
            batch_size = min(
                still_needed + 2,
                len(search_results) - url_index,
            )
            batch_urls = [
                search_results[url_index + i]["url"]
                for i in range(batch_size)
            ]
            url_index += batch_size

            logger.info(f"Fetching batch of {len(batch_urls)} URLs (Progress: {len(good_results)}/{num_target})")

            tasks = [
                _fetch_single_url_with_retry(
                    url, timeout, _DEFAULT_HEADERS
                )
                for url in batch_urls
            ]
            batch_results = await asyncio.gather(*tasks)

            for result in batch_results:
                if "error" in result:
                    error_results.append(result)
                else:
                    good_results.append(result)

        all_results = good_results
        all_failed = (
            len(good_results) == 0 and len(error_results) > 0
        )
        return all_results, all_failed

    return asyncio.run(_run())
