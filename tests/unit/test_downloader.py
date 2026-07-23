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


def test_downloader_can_preserve_url_path(tmp_path) -> None:
    downloader = SourceDownloader(timeout_seconds=30, user_agent="test")

    path = downloader._path_for_url(
        tmp_path,
        "https://www.onssa.gov.ma/wp-content/uploads/2025/organigramme.png",
        "png",
    )

    assert path.parent.as_posix().endswith(
        "www.onssa.gov.ma/wp-content/uploads/2025"
    )
    assert path.name.startswith("organigramme_")
