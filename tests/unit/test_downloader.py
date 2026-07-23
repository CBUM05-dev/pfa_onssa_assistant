import pytest

from onssa_ai.sources.downloader import BlockedSourceError, SourceDownloader


def test_downloader_rejects_captcha_validation_page() -> None:
    downloader = SourceDownloader(timeout_seconds=30, user_agent="test")
    content = b"""
    <html>
      <title>Validation request</title>
      <body>
        User validation required to continue.
        <img src="/captcha.gif">
        <form action="/captcha_resp"></form>
      </body>
    </html>
    """

    with pytest.raises(BlockedSourceError):
        downloader._raise_for_blocked_source(
            "https://www.onssa.gov.ma/missions/",
            content,
            "text/html",
        )
