"""HTTP download helpers for source synchronization."""

from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from bs4 import BeautifulSoup


class DownloadedContent:
    def __init__(
        self,
        url: str,
        content: bytes,
        content_type: str | None,
        title: str | None,
    ) -> None:
        self.url = url
        self.content = content
        self.content_type = content_type
        self.title = title
        self.content_sha256 = sha256(content).hexdigest()


class BlockedSourceError(RuntimeError):
    """Raised when a downloaded response is an access-control challenge."""


class SourceDownloader:
    """Download HTML pages and PDF files."""

    def __init__(self, timeout_seconds: int, user_agent: str) -> None:
        self.timeout_seconds = timeout_seconds
        self.headers = {"User-Agent": user_agent}

    def download(self, url: str) -> DownloadedContent:
        with httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers=self.headers,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
        content_type = response.headers.get("content-type")
        self._raise_for_blocked_source(str(response.url), response.content, content_type)
        title = self._extract_title(response.content, content_type)
        return DownloadedContent(
            url=str(response.url),
            content=response.content,
            content_type=content_type,
            title=title,
        )

    def write(self, content: DownloadedContent, target_dir: Path, suffix: str) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = self._filename_for_url(content.url, suffix)
        target_path = target_dir / filename
        target_path.write_bytes(content.content)
        return target_path

    def _extract_title(self, content: bytes, content_type: str | None) -> str | None:
        if not content_type or "html" not in content_type.lower():
            return None
        soup = BeautifulSoup(content, "html.parser")
        if soup.title and soup.title.string:
            return " ".join(soup.title.string.split())
        heading = soup.find(["h1", "h2"])
        if heading:
            return " ".join(heading.get_text(" ", strip=True).split())
        return None

    def _raise_for_blocked_source(
        self,
        url: str,
        content: bytes,
        content_type: str | None,
    ) -> None:
        if not content_type or "html" not in content_type.lower():
            return
        text = content.decode("utf-8", errors="ignore").lower()
        blocked_markers = [
            "validation request",
            "user validation required",
            "captcha.gif",
            "captcha_resp",
            "validation needed due to the detection of invalid input",
        ]
        if any(marker in text for marker in blocked_markers):
            raise BlockedSourceError(
                f"Blocked by source access-control challenge while downloading {url}"
            )

    def _filename_for_url(self, url: str, suffix: str) -> str:
        parsed = urlparse(url)
        raw_name = Path(unquote(parsed.path)).name
        if raw_name and "." in raw_name:
            stem = Path(raw_name).stem
        else:
            stem = parsed.netloc + parsed.path.replace("/", "_")
        clean = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in stem)
        digest = sha256(url.encode("utf-8")).hexdigest()[:12]
        return f"{clean[:80]}_{digest}.{suffix}"
