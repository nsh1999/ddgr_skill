"""HTTP fetching and HTML-to-markdown conversion."""

import asyncio
import re
from typing import Optional

from bs4 import BeautifulSoup
import httpx
import markdownify

from ddgr_skill.exceptions import HTTPError, NetworkError

_DEFAULT_TIMEOUT = 10.0
_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_STRIP_TAGS = ["nav", "header", "footer", "aside"]


def fetch_url(
    url,
    timeout=_DEFAULT_TIMEOUT,
    user_agent=_DEFAULT_USER_AGENT,
):
    """Fetch a URL and return the response."""
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        )
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


def fetch_as_markdown(url, timeout=_DEFAULT_TIMEOUT):
    """Fetch a URL and return structured content."""
    response = fetch_url(url, timeout=timeout)
    title = _extract_title(response.text) or url
    content = html_to_markdown(response.text)
    return {"title": title, "url": url, "content": content}


async def _fetch_single_url_async(url, timeout, user_agent):
    """Fetch a single URL asynchronously."""
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                url,
                headers={"User-Agent": user_agent},
            )
            response.raise_for_status()
            title = _extract_title(response.text) or url
            content = html_to_markdown(response.text)
            return {"title": title, "url": url, "content": content}
    except Exception as exc:
        return {"title": url, "url": url, "error": str(exc)}


def fetch_urls_concurrent(urls, timeout=_DEFAULT_TIMEOUT):
    """Fetch multiple URLs concurrently."""
    async def _run():
        tasks = [
            _fetch_single_url_async(url, timeout, _DEFAULT_USER_AGENT)
            for url in urls
        ]
        return await asyncio.gather(*tasks)

    return list(asyncio.run(_run()))
