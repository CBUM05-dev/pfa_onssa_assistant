from onssa_ai.ingestion.html_extractor import HtmlExtractor


def test_html_extractor_preserves_sections_tables_and_images(tmp_path) -> None:
    html_path = tmp_path / "missions.html"
    html_path.write_text(
        """
        <html>
          <body>
            <nav>Menu a ignorer</nav>
            <main>
              <h1>Missions</h1>
              <p>Controle sanitaire des produits alimentaires.</p>
              <h2>Services</h2>
              <table>
                <tr><th>Service</th><th>Contact</th></tr>
                <tr><td>Direction centrale</td><td>contact@example.ma</td></tr>
              </table>
              <img src="/organigramme.png" alt="Organigramme ONSSA">
            </main>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    extracted = HtmlExtractor().extract(html_path)
    blocks = extracted.metadata["html_blocks"]

    assert extracted.title == "Missions"
    assert "Menu a ignorer" not in extracted.text
    assert any(block["block_type"] == "html_section" for block in blocks)
    assert any(block["block_type"] == "html_table" for block in blocks)
    assert any(block["block_type"] == "html_image" for block in blocks)
    assert "| Service | Contact |" in extracted.text
    assert "Direction centrale: Contact contact@example.ma." in extracted.text
    assert "Image: Organigramme ONSSA" in extracted.text
