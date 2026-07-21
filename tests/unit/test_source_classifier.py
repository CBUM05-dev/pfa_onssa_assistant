from onssa_ai.ingestion.source_classifier import SourceClassifier
from onssa_ai.ingestion.taxonomy import SiteTaxonomy, TaxonomyConfig, TaxonomyRule
from onssa_ai.sources.models import SourceManifestEntry


def test_classifier_includes_target_institutional_page() -> None:
    taxonomy = SiteTaxonomy(
        TaxonomyConfig(
            rules=[
                TaxonomyRule(
                    url_contains="/missions/",
                    vertical="institutionnel",
                    domain="onssa",
                    subdomain="presentation",
                    sub_subdomain="missions",
                    sub_subdomain_display="Missions",
                    display_path=["ONSSA", "Presentation", "Missions"],
                    include_in_first_slice=True,
                )
            ]
        )
    )
    classifier = SourceClassifier(
        target_vertical="institutionnel",
        target_domain="onssa",
        target_subdomain="presentation",
        taxonomy=taxonomy,
    )

    classification = classifier.classify(
        SourceManifestEntry(
            url="https://www.onssa.gov.ma/missions/",
            kind="page",
            status="new",
        )
    )

    assert classification.include is True
    assert classification.vertical == "institutionnel"
    assert classification.site_sub_subdomain == "missions"


def test_classifier_does_not_mix_institutional_page_into_regulatory_slice() -> None:
    taxonomy = SiteTaxonomy(
        TaxonomyConfig(
            rules=[
                TaxonomyRule(
                    url_contains="/missions/",
                    vertical="institutionnel",
                    domain="onssa",
                    subdomain="presentation",
                    include_in_first_slice=True,
                )
            ]
        )
    )
    classifier = SourceClassifier(taxonomy=taxonomy)

    classification = classifier.classify(
        SourceManifestEntry(
            url="https://www.onssa.gov.ma/missions/",
            kind="page",
            status="new",
        )
    )

    assert classification.include is False
