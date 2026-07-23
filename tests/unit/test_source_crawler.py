from bs4 import BeautifulSoup

from onssa_ai.sources.config import SourceConfig
from onssa_ai.sources.crawler import SourceCrawler


def _crawler() -> SourceCrawler:
    return SourceCrawler(
        SourceConfig(
            name="onssa",
            base_url="https://www.onssa.gov.ma/",
            seed_urls=["https://www.onssa.gov.ma/"],
            allowed_domains=["www.onssa.gov.ma"],
            pages_dir="data/raw/pages/onssa",
            pdfs_dir="data/raw/pdfs/onssa",
        )
    )


def test_crawler_classifies_pdf_and_image_urls() -> None:
    crawler = _crawler()

    assert crawler._kind_for_url("https://www.onssa.gov.ma/file.pdf") == "pdf"
    assert crawler._kind_for_url("https://www.onssa.gov.ma/image.png") == "image"
    assert crawler._kind_for_url("https://www.onssa.gov.ma/missions/") == "page"


def test_crawler_extracts_image_src_and_srcset_urls() -> None:
    crawler = _crawler()
    soup = BeautifulSoup(
        '<img src="/image.png" srcset="/image-small.png 320w, /image-large.png 1024w">',
        "html.parser",
    )

    urls = crawler._image_urls("https://www.onssa.gov.ma/missions/", soup.img)

    assert "https://www.onssa.gov.ma/image.png" in urls
    assert "https://www.onssa.gov.ma/image-small.png" in urls
    assert "https://www.onssa.gov.ma/image-large.png" in urls
