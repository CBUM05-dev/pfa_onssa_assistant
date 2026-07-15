"""Polite bounded crawler for ONSSA source discovery."""

from collections import deque
from collections.abc import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from onssa_ai.sources.config import SourceConfig
from onssa_ai.sources.models import DiscoveredSource


class SourceCrawler:
    """Discover pages and PDF links from configured seed URLs."""

    def __init__(self, config: SourceConfig) -> None:
        self.config = config
        self.headers = {"User-Agent": config.user_agent}

    def discover(self) -> list[DiscoveredSource]:
        seen: set[str] = set()
        discovered: dict[str, DiscoveredSource] = {}
        queue: deque[DiscoveredSource] = deque(
            DiscoveredSource(url=str(url), kind="page", depth=0) for url in self.config.seed_urls
        )

        while queue:
            current = queue.popleft()
            normalized_url = self._normalize_url(current.url)
            if normalized_url in seen:
                continue
            seen.add(normalized_url)
            if not self._is_allowed(normalized_url):
                continue

            discovered[normalized_url] = current.model_copy(update={"url": normalized_url})
            if current.kind == "pdf" or current.depth >= self.config.max_depth:
                continue

            for child in self._extract_links(normalized_url):
                if child.url not in seen and self._is_relevant(child.url):
                    queue.append(
                        child.model_copy(
                            update={
                                "depth": current.depth + 1,
                                "parent_url": normalized_url,
                            }
                        )
                    )

        return list(discovered.values())

    def _extract_links(self, page_url: str) -> Iterable[DiscoveredSource]:
        try:
            with httpx.Client(
                timeout=self.config.request_timeout_seconds,
                follow_redirects=True,
                headers=self.headers,
            ) as client:
                response = client.get(page_url)
                response.raise_for_status()
        except httpx.HTTPError:
            return []

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        links: list[DiscoveredSource] = []
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            absolute_url = self._normalize_url(urljoin(page_url, href))
            if not self._is_allowed(absolute_url):
                continue
            kind = "pdf" if self._looks_like_pdf(absolute_url) else "page"
            links.append(DiscoveredSource(url=absolute_url, kind=kind, depth=0))
        return links

    def _normalize_url(self, url: str) -> str:
        without_fragment, _fragment = urldefrag(url)
        return without_fragment.strip()

    def _is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        return parsed.netloc.lower() in {domain.lower() for domain in self.config.allowed_domains}

    def _is_relevant(self, url: str) -> bool:
        lowered = url.lower()
        if any(pattern.lower() in lowered for pattern in self.config.exclude_url_patterns):
            return False
        if self._looks_like_pdf(lowered):
            return True
        if not self.config.include_url_patterns:
            return True
        return any(pattern.lower() in lowered for pattern in self.config.include_url_patterns)

    def _looks_like_pdf(self, url: str) -> bool:
        return urlparse(url).path.lower().endswith(".pdf")
